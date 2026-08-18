"""LangGraph nodes: Q&A cache lookup and write-back."""

from __future__ import annotations

from app.cache.store import get_cache_store
from app.config import settings
from app.graph.state import AgentState
from app.storage.embeddings import embed_texts


def cache_lookup(state: AgentState) -> dict:
    """
    Node — similarity search in the separate Q&A cache index.

    Runs after embed_question; reuses question_vector.
    """
    cache = get_cache_store()
    hit = cache.lookup(state["question_vector"], settings.cache_similarity_threshold)
    if hit is None:
        return {"cache_hit": False, "status": "cache_miss"}
    return {
        "cache_hit": True,
        "answer": hit.answer,
        "confidence": hit.score,
        "source": "cache",
        "blocked": False,
        "status": "cache_hit",
    }


def route_after_cache(state: AgentState) -> str:
    return "hit" if state.get("cache_hit") else "miss"


def return_cached_answer(state: AgentState) -> dict:
    """Terminal path for cache hits — answer already in state."""
    return {"status": "completed"}


def maybe_cache_answer(state: AgentState) -> dict:
    """
    After successful RAG, optionally store Q&A for future cache hits.

    Only writes when confidence ≥ cache_min_write_confidence and auto-write is on.
    """
    if not settings.cache_auto_write:
        return {"status": "cache_skip"}
    if state.get("source") != "rag":
        return {"status": "cache_skip"}

    confidence = float(state.get("confidence", 0.0))
    if confidence < settings.cache_min_write_confidence:
        return {"status": "cache_skip"}

    question = state["question"].strip()
    answer = state.get("answer", "").strip()
    if not question or not answer:
        return {"status": "cache_skip"}

    try:
        vector = state.get("question_vector") or embed_texts([question])[0]
        cache = get_cache_store()
        cache.put(
            question=question,
            answer=answer,
            vector=vector,
            embedding_model=settings.embedding_model,
            source="auto",
        )
        return {"status": "cache_written"}
    except Exception:
        return {"status": "cache_write_failed"}
