"""Storage record types for vectors, graph, and Q&A cache."""

from __future__ import annotations

from pydantic import BaseModel


class ChunkVectorRecord(BaseModel):
    chunk_id: str
    page_id: str
    section_id: str
    text: str
    order: int


class ScoredChunk(BaseModel):
    chunk_id: str
    page_id: str
    section_id: str
    text: str
    score: float


class CacheRecord(BaseModel):
    """One cached question→answer pair."""

    question: str
    answer: str
    source: str = "seed"  # seed | auto


class CacheHit(BaseModel):
    question: str
    answer: str
    score: float
    source: str = "seed"
