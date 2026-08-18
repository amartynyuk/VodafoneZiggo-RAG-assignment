"""LangGraph node: build deterministic knowledge-graph skeleton."""

from __future__ import annotations

from app.models.schemas import GraphEdge, GraphNode
from app.pipeline.state import IngestState


def build_graph_skeleton(state: IngestState) -> dict:
    """
    Node 6 — Create Page → Section → Chunk graph (no LLM).

    Edges:
        Page -[HAS_SECTION]-> Section
        Section -[HAS_CHUNK]-> Chunk
        Chunk -[NEXT]-> Chunk (reading order within page)

  This matches ARCHITECTURE.md and sets up graph-augmented retrieval later.
    """
    metadata = state["metadata"]
    sections = state.get("sections", [])
    chunks = state.get("chunks", [])

    page_node_id = f"page:{metadata.page_id}"
    nodes: list[GraphNode] = [
        GraphNode(
            node_id=page_node_id,
            label="Page",
            properties={
                "page_id": metadata.page_id,
                "url": metadata.url,
                "title": metadata.title,
                "label": metadata.label,
                "content_quality": state.get("content_quality", "unknown"),
            },
        )
    ]
    edges: list[GraphEdge] = []

    section_ids: dict[str, str] = {}
    for section in sections:
        section_node_id = f"section:{section.section_id}"
        section_ids[section.section_id] = section_node_id
        nodes.append(
            GraphNode(
                node_id=section_node_id,
                label="Section",
                properties={
                    "section_id": section.section_id,
                    "heading": section.heading,
                    "level": section.level,
                    "order": section.order,
                },
            )
        )
        edges.append(
            GraphEdge(source_id=page_node_id, target_id=section_node_id, rel_type="HAS_SECTION")
        )

    prev_chunk_id: str | None = None
    for chunk in chunks:
        chunk_node_id = f"chunk:{chunk.chunk_id}"
        nodes.append(
            GraphNode(
                node_id=chunk_node_id,
                label="Chunk",
                properties={
                    "chunk_id": chunk.chunk_id,
                    "section_id": chunk.section_id,
                    "text": chunk.text,
                    "order": chunk.order,
                    "token_estimate": chunk.token_estimate,
                },
            )
        )
        section_node_id = section_ids.get(chunk.section_id)
        if section_node_id:
            edges.append(
                GraphEdge(
                    source_id=section_node_id,
                    target_id=chunk_node_id,
                    rel_type="HAS_CHUNK",
                )
            )
        if prev_chunk_id:
            edges.append(
                GraphEdge(source_id=prev_chunk_id, target_id=chunk_node_id, rel_type="NEXT")
            )
        prev_chunk_id = chunk_node_id

    return {"graph_nodes": nodes, "graph_edges": edges, "status": "graph_built"}
