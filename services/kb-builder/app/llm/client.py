"""
OpenAI chat model factory (langchain_openai).

LangSmith tracing is enabled automatically when LANGSMITH_TRACING=true
and LANGSMITH_API_KEY are set in the environment (see root .env).
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    """
    Return a shared ChatOpenAI instance for ingest LLM nodes.

    Uses LLM_MODEL from settings (default gpt-4o-mini). Temperature 0
    keeps extraction deterministic and reproducible.
    """
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
