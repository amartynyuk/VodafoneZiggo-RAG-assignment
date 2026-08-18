"""Schema-guided entity extraction from page chunks."""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.llm.client import get_chat_model
from app.llm.schemas import PageEntityExtraction
from app.models.schemas import ExtractedEntity, TextChunk

_ENTITY_SYSTEM = """You extract structured entities from Ziggo (VodafoneZiggo) customer-facing web content in Dutch or English.

Rules:
- Only extract entities explicitly stated in each chunk. Do not infer or hallucinate.
- Use canonical product names (e.g. "Ziggo GO", not "the app").
- entity_type must be one of:
  - Product: named Ziggo services/packages (Ziggo GO, TV Start, Internet & TV)
  - ServiceFeature: capabilities (Replay TV, offline kijken, Wifi Garantie)
  - Hardware: physical equipment (CI+ module, mediabox, modem)
  - Specification: measurable facts (70+ zenders, 3 apparaten, Mbit/s)
  - PricePoint: prices (€ 58,40)
- Return an entry per chunk_id provided, even if entities is empty.
"""


def _entity_id(name: str, entity_type: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]
    return f"{entity_type.lower()}:{slug}"


def extract_entities_from_chunks(chunks: list[TextChunk]) -> list[ExtractedEntity]:
    """
    Run batched structured LLM extraction over all page chunks.

    Chunks are grouped into batches to limit prompt size while keeping
    chunk_id attribution accurate.
    """
    if not chunks:
        return []

    llm = get_chat_model().with_structured_output(PageEntityExtraction)
    batch_size = settings.llm_chunk_batch_size
    all_entities: list[ExtractedEntity] = []

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        chunk_block = "\n\n".join(
            f"### chunk_id: {c.chunk_id}\n{c.text}" for c in batch
        )
        messages = [
            SystemMessage(content=_ENTITY_SYSTEM),
            HumanMessage(
                content=f"Extract entities from these chunks:\n\n{chunk_block}"
            ),
        ]
        result: PageEntityExtraction = llm.invoke(messages)

        result_by_id = {item.chunk_id: item for item in result.chunks}
        for chunk in batch:
            extraction = result_by_id.get(chunk.chunk_id)
            if extraction is None:
                continue
            for record in extraction.entities:
                all_entities.append(
                    ExtractedEntity(
                        entity_id=_entity_id(record.name, record.entity_type),
                        name=record.name.strip(),
                        entity_type=record.entity_type,
                        source_chunk_id=chunk.chunk_id,
                    )
                )

    return all_entities
