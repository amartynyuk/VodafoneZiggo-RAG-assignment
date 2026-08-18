"""OpenAI embedding client shared by ingest, RAG retrieval, and the Q&A cache."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from kb_store.paths import embedding_model


@lru_cache
def get_embedder() -> OpenAIEmbeddings:
    """
    Shared embedder — model from EMBEDDING_MODEL (default text-embedding-3-small).

    We keep the native 1536-d vectors so existing FAISS indexes stay valid.
    Call this at app startup so the client is ready before the first request.
    """
    return OpenAIEmbeddings(model=embedding_model())


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed document strings; returns one vector per input text."""
    if not texts:
        return []
    return get_embedder().embed_documents(texts)
