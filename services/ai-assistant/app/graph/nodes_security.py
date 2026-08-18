"""LangGraph nodes: BERT security gate."""

from __future__ import annotations

from app.config import settings
from app.graph.state import AgentState
from app.security.classifier import SecurityLabel, classify_question


def security_classify(state: AgentState) -> dict:
    """
    Node — BERT toxicity + zero-shot topic check before RAG.

    Blocks toxic or clearly off-topic questions to save LLM cost.
    """
    label, score = classify_question(state["question"])
    return {
        "security_label": label.value,
        "security_score": score,
        "status": "security_checked",
    }


def route_after_security(state: AgentState) -> str:
    label = state.get("security_label", SecurityLabel.ALLOW.value)
    if label in (SecurityLabel.TOXIC.value, SecurityLabel.OFF_TOPIC.value):
        return "block"
    return "allow"


def reject_response(state: AgentState) -> dict:
    """Safe customer-facing refusal for blocked questions."""
    label = state.get("security_label", SecurityLabel.TOXIC.value)
    nl = settings.response_language == "nl"

    if label == SecurityLabel.TOXIC.value:
        answer = (
            "Ik kan je vraag niet beantwoorden. Houd het alstublieft respectvol."
            if nl
            else "I cannot answer that question. Please keep the conversation respectful."
        )
    else:
        answer = (
            "Ik ben de Ziggo-assistent en kan alleen helpen met vragen over Ziggo "
            "internet, tv, wifi en gerelateerde diensten. Waar kan ik je mee helpen?"
            if nl
            else "I'm the Ziggo assistant and can only help with questions about Ziggo "
            "internet, TV, wifi and related services. How can I help you?"
        )

    return {
        "answer": answer,
        "source": "none",
        "confidence": 0.0,
        "blocked": True,
        "status": "blocked",
    }
