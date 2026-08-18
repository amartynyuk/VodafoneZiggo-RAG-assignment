"""OpenAI embedding client for chunk vectorization."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from app.config import settings


@lru_cache
def get_embedder() -> OpenAIEmbeddings:
    """Shared embedder — model from EMBEDDING_MODEL env (default text-embedding-3-small)."""
    return OpenAIEmbeddings(model=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed document strings; returns one vector per input text."""
    if not texts:
        return []
    return get_embedder().embed_documents(texts)
