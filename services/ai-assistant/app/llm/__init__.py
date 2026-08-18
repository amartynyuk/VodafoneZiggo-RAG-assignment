"""Chat model and prompts for grounded RAG answers."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.config import settings

_LANGUAGE_NAMES = {"nl": "Dutch", "en": "English"}


@lru_cache
def get_chat_model() -> ChatOpenAI:
    """Chat model for RAG answer generation (LangSmith traces when enabled)."""
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )


def system_prompt() -> str:
    lang = _LANGUAGE_NAMES.get(settings.response_language, "Dutch")
    return f"""You are a helpful customer assistant for Ziggo (VodafoneZiggo), a Dutch telecommunications provider.

Rules:
- Answer in {lang}.
- Use ONLY the provided context to answer. Do not use outside knowledge.
- If the context does not contain enough information, say clearly that you cannot answer based on the available information.
- Be friendly, concise, and professional — suitable for a customer-facing chat.
- Do not invent product names, prices, speeds, or features.
- When relevant, mention specific Ziggo product names exactly as they appear in the context."""


def user_prompt(question: str, context_text: str) -> str:
    return f"""Use the following context to answer the customer question.

--- CONTEXT ---
{context_text}
--- END CONTEXT ---

Customer question: {question}"""
