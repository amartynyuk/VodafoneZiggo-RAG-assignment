"""
LangGraph state for the query (RAG) workflow.

Flow: embed → cache → security → retrieve → expand → generate → maybe_cache
"""

from __future__ import annotations

from typing import TypedDict

from app.storage.models import ScoredChunk


class AgentState(TypedDict, total=False):
    # Input
    question: str

    # embed_question
    question_vector: list[float]

    # cache_lookup
    cache_hit: bool

    # security_classify
    security_label: str
    security_score: float

    # vector_retrieve
    retrieved_chunks: list[ScoredChunk]

    # graph_expand_context
    graph_context: dict
    context_text: str

    # generate_answer / responses
    answer: str
    confidence: float
    source: str  # cache | rag | none
    blocked: bool
    status: str
