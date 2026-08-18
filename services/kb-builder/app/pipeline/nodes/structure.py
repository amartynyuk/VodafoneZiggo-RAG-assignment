"""LangGraph nodes: parse sections and chunk text."""

from __future__ import annotations

from app.chunk.chunker import chunk_sections
from app.models.schemas import ContentQuality, SectionBlock
from app.pipeline.state import IngestState
from app.structure.sections import parse_sections


def _sparse_overview_section(state: IngestState) -> list[SectionBlock]:
    """
    Build a single overview section for JS-heavy pages.

    Uses og/meta descriptions plus any static text we captured — avoids
    parsing hidden pricing templates in the DOM shell.
    """
    metadata = state["metadata"]
    parts: list[str] = []
    for field in (metadata.og_description, metadata.meta_description, state.get("cleaned_text")):
        if field and field not in parts:
            parts.append(field)

    return [
        SectionBlock(
            section_id=f"{metadata.page_id}::overview",
            heading=metadata.title or metadata.page_id,
            level=1,
            text="\n\n".join(parts),
            order=1,
        )
    ]


def parse_page_sections(state: IngestState) -> dict:
    """
    Node 4 — Heading-aware section parse.

    Input:  content_html, metadata.page_id, content_quality
    Output: sections
    """
    metadata = state["metadata"]

    if state.get("content_quality") == ContentQuality.SPARSE:
        sections = _sparse_overview_section(state)
        return {"sections": sections, "status": "parsed_sparse"}

    sections = parse_sections(state["content_html"], metadata.page_id)

    # Drop heading-only shells; keep sections that carry body text.
    sections = [s for s in sections if s.text.strip()]

    if not sections and state.get("cleaned_text"):
        sections = _sparse_overview_section(state)

    return {"sections": sections, "status": "parsed"}


def chunk_page_sections(state: IngestState) -> dict:
    """
    Node 5 — Split sections into retrieval chunks.

    Input:  sections, metadata.page_id
    Output: chunks
    """
    metadata = state["metadata"]
    chunks = chunk_sections(state.get("sections", []), metadata.page_id)
    return {"chunks": chunks, "status": "chunked"}
