"""OpenAI chat model for answer generation."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    """
    Chat model for RAG answer generation.

    LangSmith traces this automatically when LANGSMITH_TRACING=true.
    """
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
