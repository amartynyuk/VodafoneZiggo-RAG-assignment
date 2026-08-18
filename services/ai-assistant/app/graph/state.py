"""
LangGraph state for the query (RAG) workflow.

Each node reads/writes specific keys. Phase 4+ will add cache and security fields.
"""

from __future__ import annotations

from typing import TypedDict

from app.storage.models import ScoredChunk


class AgentState(TypedDict, total=False):
    # Input
    question: str

    # embed_question
    question_vector: list[float]

    # vector_retrieve
    retrieved_chunks: list[ScoredChunk]

    # graph_expand_context
    graph_context: dict
    context_text: str

    # generate_answer
    answer: str
    confidence: float

    # Response metadata
    source: str  # "rag" | "none"
    blocked: bool
    status: str
