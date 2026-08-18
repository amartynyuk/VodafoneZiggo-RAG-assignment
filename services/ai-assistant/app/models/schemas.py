"""Minimal shared models for storage (mirrors kb-builder)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    node_id: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    rel_type: str


class TextChunk(BaseModel):
    """Chunk record (used by KnowledgeBase.upsert on kb-builder only)."""

    chunk_id: str
    section_id: str
    text: str
    order: int
    token_estimate: int = 0
