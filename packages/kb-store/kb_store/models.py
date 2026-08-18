"""Shared Pydantic records for vectors, graph, and the Q&A cache."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChunkVectorRecord(BaseModel):
    """Metadata for one embedded chunk in the FAISS RAG index."""

    chunk_id: str
    page_id: str
    section_id: str
    text: str
    order: int


class ScoredChunk(BaseModel):
    """Vector search hit returned to the RAG query workflow."""

    chunk_id: str
    page_id: str
    section_id: str
    text: str
    score: float


class GraphNode(BaseModel):
    """Serializable graph node (NetworkX locally; Neptune in AWS)."""

    node_id: str
    label: str  # Page | Section | Chunk | Entity
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Directed edge between two nodes."""

    source_id: str
    target_id: str
    rel_type: str  # HAS_SECTION | HAS_CHUNK | NEXT | MENTIONS | RELATED_TO


class TextChunk(BaseModel):
    """Retrieval unit linked to a parent section (ingest + index)."""

    chunk_id: str
    section_id: str
    text: str
    order: int
    token_estimate: int = 0


class CacheRecord(BaseModel):
    """One cached question → answer pair."""

    question: str
    answer: str
    source: str = "seed"  # seed | auto


class CacheHit(BaseModel):
    """Lookup result from the Q&A cache index."""

    question: str
    answer: str
    score: float
    source: str = "seed"
