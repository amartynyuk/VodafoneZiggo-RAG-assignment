"""
Section-aware chunking for vector retrieval.

Keeps each section intact when short; splits long sections on paragraph
boundaries so chunks stay semantically coherent.
"""

from __future__ import annotations

import re

from app.config import settings
from app.models.schemas import SectionBlock, TextChunk


def chunk_sections(
    sections: list[SectionBlock],
    page_id: str,
    max_chars: int | None = None,
) -> list[TextChunk]:
    """
    Convert sections into retrieval-sized chunks.

    Args:
        sections: Parsed section blocks from structure/sections.py.
        page_id: Stable page identifier for chunk_id prefixing.
        max_chars: Override default max chunk size from settings.
    """
    limit = max_chars or settings.max_chunk_chars
    chunks: list[TextChunk] = []
    order = 0

    for section in sections:
        body = section.text.strip()
        prefix = f"{section.heading}\n\n" if section.heading else ""
        full_text = f"{prefix}{body}".strip() if body else section.heading

        if not full_text:
            continue

        if len(full_text) <= limit:
            order += 1
            chunks.append(_make_chunk(page_id, section.section_id, full_text, order))
            continue

        # Split long sections on blank lines (paragraph boundaries).
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        buffer = prefix
        for para in paragraphs:
            candidate = f"{buffer}{para}\n\n" if buffer else f"{para}\n\n"
            if len(candidate) > limit and buffer.strip():
                order += 1
                chunks.append(_make_chunk(page_id, section.section_id, buffer.strip(), order))
                buffer = f"{prefix}{para}\n\n"
            else:
                buffer = candidate
        if buffer.strip():
            order += 1
            chunks.append(_make_chunk(page_id, section.section_id, buffer.strip(), order))

    return chunks


def _make_chunk(page_id: str, section_id: str, text: str, order: int) -> TextChunk:
    return TextChunk(
        chunk_id=f"{page_id}::chunk-{order:04d}",
        section_id=section_id,
        text=text,
        order=order,
        token_estimate=max(1, len(text) // 4),
    )
