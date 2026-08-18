"""
BERT-based security gate for incoming questions.

Two-stage classification (both lazy-loaded on first request):
1. unitary/toxic-bert — block toxic / harmful input
2. Zero-shot DistilBERT — detect off-topic questions before expensive RAG

In production you would fine-tune on Ziggo-specific labeled data; pretrained
models are sufficient for the assignment demo.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from app.config import settings


class SecurityLabel(str, Enum):
    ALLOW = "allow"
    OFF_TOPIC = "off_topic"
    TOXIC = "toxic"


@lru_cache
def _get_toxic_classifier():
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model="unitary/toxic-bert",
        top_k=None,
    )


@lru_cache
def _get_topic_classifier():
    from transformers import pipeline

    return pipeline(
        "zero-shot-classification",
        model="typeform/distilbert-base-uncased-mnli",
    )


_ZIGGO_TOPIC = "question about Ziggo internet television wifi mobile or telecom products and services"
_OFF_TOPIC = "unrelated chit chat jokes or general knowledge not about telecommunications"


def classify_question(question: str) -> tuple[SecurityLabel, float]:
    """
    Classify a customer question for routing.

    Returns:
        (label, confidence) — TOXIC and OFF_TOPIC should block RAG.
    """
    if not settings.security_enabled:
        return SecurityLabel.ALLOW, 1.0

    text = question.strip()
    if not text:
        return SecurityLabel.OFF_TOPIC, 1.0

    # Stage 1: toxicity
    toxic_results = _get_toxic_classifier()(text[:512])
    if isinstance(toxic_results, list) and toxic_results and isinstance(toxic_results[0], list):
        toxic_results = toxic_results[0]
    for item in toxic_results:
        label = str(item.get("label", "")).upper()
        score = float(item.get("score", 0.0))
        if "TOXIC" in label and score >= settings.security_toxic_threshold:
            return SecurityLabel.TOXIC, score

    # Stage 2: topic relevance (zero-shot)
    topic_result = _get_topic_classifier()(
        text[:512],
        candidate_labels=[_ZIGGO_TOPIC, _OFF_TOPIC],
        hypothesis_template="This is {}.",
    )
    top_label = topic_result["labels"][0]
    top_score = float(topic_result["scores"][0])
    if top_label == _OFF_TOPIC and top_score >= settings.security_offtopic_threshold:
        return SecurityLabel.OFF_TOPIC, top_score

    return SecurityLabel.ALLOW, top_score
