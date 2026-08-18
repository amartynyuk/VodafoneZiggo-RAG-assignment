"""
Pydantic models for the KB ingest pipeline.

These types are shared across LangGraph nodes and the FastAPI layer.
They mirror the graph schema in ARCHITECTURE.md (Page → Section → Chunk).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ContentQuality(str, Enum):
    """How much usable text we extracted without JavaScript rendering."""

    RICH = "rich"  # main content has enough structure for section parsing
    SPARSE = "sparse"  # mostly shell HTML; pricing/tables likely JS-rendered


class PageMetadata(BaseModel):
    """Deterministic metadata from <head> and Open Graph tags."""

    url: str
    page_id: str
    label: str | None = None
    title: str | None = None
    meta_description: str | None = None
    og_title: str | None = None
    og_description: str | None = None


class SectionBlock(BaseModel):
    """A heading-delimited block of content (deterministic parse)."""

    section_id: str
    heading: str
    level: int = Field(ge=1, le=6, description="Heading level 1–6")
    text: str
    order: int


class TextChunk(BaseModel):
    """Retrieval unit linked to a parent section."""

    chunk_id: str
    section_id: str
    text: str
    order: int
    token_estimate: int


class GraphNode(BaseModel):
    """Serializable graph node (NetworkX / Neptune)."""

    node_id: str
    label: str  # Page | Section | Chunk | Entity
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Directed edge between two nodes."""

    source_id: str
    target_id: str
    rel_type: str  # HAS_SECTION | HAS_CHUNK | NEXT | MENTIONS | RELATED_TO


class ExtractedEntity(BaseModel):
    """Entity produced by the LLM extraction node (Phase 2b)."""

    entity_id: str
    name: str
    entity_type: str
    source_chunk_id: str | None = None


class IngestResult(BaseModel):
    """API response after a full ingest run."""

    page_id: str
    page_url: str
    label: str | None = None
    content_quality: ContentQuality
    sections_count: int
    chunks_count: int
    graph_nodes: int
    graph_edges: int
    entities_extracted: int = 0
    vectors_indexed: int = 0
    graph_nodes_total: int = 0
    graph_edges_total: int = 0
    status: str
    warnings: list[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    """POST /ingest body — provide URL or nav label."""

    page_url: HttpUrl | None = None
    label: str | None = None
