"""Structured output schemas for LLM ingest steps."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Subset of the Ziggo ontology (ARCHITECTURE.md + extraction research).
EntityType = Literal[
    "Product",
    "ServiceFeature",
    "Hardware",
    "Specification",
    "PricePoint",
]

SectionTopic = Literal[
    "features",
    "faq",
    "how_to",
    "pricing",
    "overview",
    "other",
]


class ExtractedEntityRecord(BaseModel):
    """One entity mention inside a chunk."""

    name: str = Field(description="Canonical name as used on ziggo.nl (e.g. Ziggo GO)")
    entity_type: EntityType


class ChunkEntityExtraction(BaseModel):
    """Entities found in a single text chunk."""

    chunk_id: str
    entities: list[ExtractedEntityRecord] = Field(default_factory=list)


class PageEntityExtraction(BaseModel):
    """Batch entity extraction across multiple chunks."""

    chunks: list[ChunkEntityExtraction]


class SectionEnrichment(BaseModel):
    """Topic label and short summary for a page section."""

    section_id: str
    topic: SectionTopic
    summary: str = Field(description="1-2 sentence summary of the section")


class PageSectionEnrichment(BaseModel):
    """Batch section labeling for one page."""

    sections: list[SectionEnrichment]
