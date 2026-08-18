"""API request/response models for the AI Assistant."""

from __future__ import annotations

from typing import Any, Literal

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
    chunk_id: str
    section_id: str
    text: str
    order: int
    token_estimate: int = 0


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Customer question about Ziggo products/services")


class AskResponse(BaseModel):
    answer: str
    source: Literal["rag", "none"] = "rag"
    confidence: float = Field(ge=0.0, le=1.0, description="Top retrieval score when source=rag")
    blocked: bool = False
