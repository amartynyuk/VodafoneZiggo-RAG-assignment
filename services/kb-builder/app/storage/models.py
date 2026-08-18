"""Storage record types for vectors and graph persistence."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChunkVectorRecord(BaseModel):
    """Metadata for one embedded chunk in the FAISS index."""

    chunk_id: str
    page_id: str
    section_id: str
    text: str
    order: int


class ScoredChunk(BaseModel):
    """Vector search hit returned to the RAG pipeline."""

    chunk_id: str
    page_id: str
    section_id: str
    text: str
    score: float
