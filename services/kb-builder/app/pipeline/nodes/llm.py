"""
LangGraph nodes: LLM extraction, labeling, and graph enrichment.

Uses langchain_openai with structured outputs. Traces appear in LangSmith
when LANGSMITH_TRACING=true (see root .env).
"""

from __future__ import annotations

from app.llm.extract import extract_entities_from_chunks
from app.llm.graph_enrich import apply_section_enrichments, merge_entities_into_graph
from app.llm.summarize import enrich_sections
from app.pipeline.state import IngestState


def llm_extract_entities(state: IngestState) -> dict:
    """
    Node 7 — Schema-guided entity extraction per chunk.

    Input:  chunks, graph_nodes, graph_edges
    Output: entities, enriched graph_nodes/graph_edges (Entity + MENTIONS)
    """
    chunks = state.get("chunks", [])
    if not chunks:
        return {"entities": [], "status": "entities_skipped"}

    try:
        entities = extract_entities_from_chunks(chunks)
        nodes, edges = merge_entities_into_graph(
            state.get("graph_nodes", []),
            state.get("graph_edges", []),
            entities,
        )
        return {
            "entities": entities,
            "graph_nodes": nodes,
            "graph_edges": edges,
            "status": "entities_extracted",
        }
    except Exception as exc:
        return {
            "entities": [],
            "warnings": [f"LLM entity extraction failed: {exc}"],
            "status": "entities_failed",
        }


def llm_label_and_summarize(state: IngestState) -> dict:
    """
    Node 8 — Section topic labels and summaries.

    Input:  sections, graph_nodes
    Output: section_summaries, section_topics on graph Section nodes
    """
    sections = state.get("sections", [])
    if not sections:
        return {"section_summaries": {}, "status": "summaries_skipped"}

    try:
        summaries, topics = enrich_sections(sections)
        nodes = apply_section_enrichments(
            state.get("graph_nodes", []),
            summaries,
            topics,
        )
        return {
            "section_summaries": summaries,
            "graph_nodes": nodes,
            "status": "summaries_done",
        }
    except Exception as exc:
        return {
            "section_summaries": {},
            "warnings": [f"LLM section summarization failed: {exc}"],
            "status": "summaries_failed",
        }
