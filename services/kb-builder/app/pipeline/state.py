"""
LangGraph state for the KB ingest pipeline.

TypedDict is required by LangGraph so each node declares what it reads/writes.
Deterministic nodes populate the left column; LLM nodes (stubs) fill the right.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from app.models.schemas import (
    ContentQuality,
    ExtractedEntity,
    GraphEdge,
    GraphNode,
    PageMetadata,
    SectionBlock,
    TextChunk,
)


def _append_warnings(existing: list[str], new: list[str]) -> list[str]:
    return existing + new


class IngestState(TypedDict, total=False):
    # --- Inputs ---
    page_url: str
    label: str | None

    # --- Deterministic: fetch & clean ---
    raw_html: str
    cleaned_text: str
    content_html: str
    main_char_count: int
    content_quality: ContentQuality
    metadata: PageMetadata
    warnings: Annotated[list[str], _append_warnings]

    # --- Deterministic: structure ---
    sections: list[SectionBlock]
    chunks: list[TextChunk]

    # --- Deterministic: graph skeleton ---
    graph_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]

    # --- LLM phases (populated later) ---
    entities: list[ExtractedEntity]
    section_summaries: dict[str, str]

    # --- Output ---
    status: str
    errors: list[str]
