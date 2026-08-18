"""LangGraph ingest pipeline definition."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.models.schemas import ContentQuality, IngestRequest, IngestResult
from app.pipeline.nodes.clean import clean_and_extract
from app.pipeline.nodes.fetch import fetch_html, route_after_fetch
from app.pipeline.nodes.graph_build import build_graph_skeleton
from app.pipeline.nodes.index_kb import index_knowledge_base
from app.pipeline.nodes.llm import llm_extract_entities, llm_label_and_summarize
from app.pipeline.nodes.persist import persist_artifacts
from app.pipeline.nodes.resolve import resolve_input
from app.pipeline.nodes.structure import chunk_page_sections, parse_page_sections
from app.pipeline.state import IngestState


def _route_on_errors(state: IngestState) -> str:
    if state.get("errors"):
        return "failed"
    return "continue"


def build_ingest_graph():
    """
    Compile the KB ingest StateGraph.

    Deterministic chain:
        resolve → fetch → clean → parse → chunk → graph → persist

    LLM hooks (stubs, run before persist):
        llm_extract_entities → llm_label_and_summarize
    """
    graph = StateGraph(IngestState)

    graph.add_node("resolve", resolve_input)
    graph.add_node("fetch", fetch_html)
    graph.add_node("clean", clean_and_extract)
    graph.add_node("parse_sections", parse_page_sections)
    graph.add_node("chunk", chunk_page_sections)
    graph.add_node("build_graph", build_graph_skeleton)
    graph.add_node("llm_extract", llm_extract_entities)
    graph.add_node("llm_summarize", llm_label_and_summarize)
    graph.add_node("index_kb", index_knowledge_base)
    graph.add_node("persist", persist_artifacts)

    graph.add_edge(START, "resolve")
    graph.add_edge("resolve", "fetch")
    graph.add_conditional_edges("fetch", route_after_fetch, {"clean": "clean", "failed": END})
    graph.add_edge("clean", "parse_sections")
    graph.add_edge("parse_sections", "chunk")
    graph.add_edge("chunk", "build_graph")
    graph.add_edge("build_graph", "llm_extract")
    graph.add_edge("llm_extract", "llm_summarize")
    graph.add_edge("llm_summarize", "index_kb")
    graph.add_edge("index_kb", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


# Singleton compiled graph — reused across API requests.
INGEST_GRAPH = build_ingest_graph()


def run_ingest(request: IngestRequest) -> IngestResult:
    """
    Execute the ingest pipeline for one page.

    Args:
        request: URL and/or nav label from the API.

    Returns:
        IngestResult summary for POST /ingest response.
    """
    initial: IngestState = {
        "label": request.label,
        "warnings": [],
        "errors": [],
        "entities": [],
        "section_summaries": {},
    }
    if request.page_url:
        initial["page_url"] = str(request.page_url)

    final = INGEST_GRAPH.invoke(initial)

    if final.get("errors"):
        from app.pipeline.utils import page_id_from_url

        url = final.get("page_url", "")
        return IngestResult(
            page_id=page_id_from_url(url) if url else "unknown",
            page_url=final.get("page_url", ""),
            label=final.get("label"),
            content_quality=ContentQuality.SPARSE,
            sections_count=0,
            chunks_count=0,
            graph_nodes=0,
            graph_edges=0,
            status="failed",
            warnings=final.get("warnings", []) + final.get("errors", []),
        )

    metadata = final["metadata"]
    return IngestResult(
        page_id=metadata.page_id,
        page_url=metadata.url,
        label=metadata.label,
        content_quality=final["content_quality"],
        sections_count=len(final.get("sections", [])),
        chunks_count=len(final.get("chunks", [])),
        graph_nodes=len(final.get("graph_nodes", [])),
        graph_edges=len(final.get("graph_edges", [])),
        entities_extracted=len(final.get("entities", [])),
        vectors_indexed=final.get("vectors_indexed", 0),
        graph_nodes_total=final.get("graph_nodes_total", len(final.get("graph_nodes", []))),
        graph_edges_total=final.get("graph_edges_total", len(final.get("graph_edges", []))),
        status=final.get("status", "completed"),
        warnings=final.get("warnings", []),
    )
