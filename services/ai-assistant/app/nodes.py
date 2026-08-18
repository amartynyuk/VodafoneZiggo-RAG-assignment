"""
LangGraph nodes for the query workflow.

Each function is one graph node: it reads AgentState, returns a partial update.
Routing functions return the name of the next edge.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage

from app.cache import get_cache_store
from app.config import settings
from app.llm import get_chat_model, system_prompt, user_prompt
from app.security import SecurityLabel, classify_question
from kb_store.embeddings import embed_texts
from kb_store.kb import get_knowledge_base
from kb_store.models import ScoredChunk


class AgentState(TypedDict, total=False):
    question: str
    question_vector: list[float]
    cache_hit: bool
    security_label: str
    security_score: float
    retrieved_chunks: list[ScoredChunk]
    graph_context: dict
    context_text: str
    answer: str
    confidence: float
    source: str  # cache | rag | none
    blocked: bool
    status: str


# --- Context helper (used by graph_expand_context) ---


def build_context_text(chunks: list[ScoredChunk], graph_expansion: dict) -> str:
    """Merge vector hits with section headings, entities, and neighbouring chunks."""
    parts: list[str] = ["## Retrieved content"]
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"### Passage {i} (relevance: {chunk.score:.2f})\n{chunk.text}")

    nodes = graph_expansion.get("nodes", [])
    sections = [n for n in nodes if n.get("label") == "Section"]
    if sections:
        parts.append("\n## Related sections")
        for section in sections:
            heading = section.get("heading", "")
            summary = section.get("summary", "")
            if heading:
                line = f"- **{heading}**"
                if summary:
                    line += f": {summary}"
                parts.append(line)

    entities = [n for n in nodes if n.get("label") == "Entity"]
    if entities:
        names = sorted({n.get("name", "") for n in entities if n.get("name")})
        if names:
            parts.append("\n## Related products and features")
            parts.append(", ".join(names))

    hit_ids = {c.chunk_id for c in chunks}
    extra_chunks: list[str] = []
    for node in nodes:
        if node.get("label") != "Chunk":
            continue
        chunk_id = node.get("chunk_id") or node.get("node_id", "").removeprefix("chunk:")
        text = node.get("text", "")
        if chunk_id and chunk_id not in hit_ids and text:
            extra_chunks.append(text)
    if extra_chunks:
        parts.append("\n## Additional context from linked passages")
        for text in extra_chunks[:3]:
            parts.append(text)

    return "\n\n".join(parts)


# --- Embed / retrieve / expand / generate ---


def embed_question(state: AgentState) -> dict:
    """Embed the customer question (reused by cache lookup and RAG)."""
    question = state["question"].strip()
    vector = embed_texts([question])[0]
    return {"question_vector": vector, "status": "embedded"}


def vector_retrieve(state: AgentState) -> dict:
    """Top-k FAISS search; drop hits below rag_similarity_threshold."""
    kb = get_knowledge_base()
    hits = kb.vectors.search(state["question_vector"], top_k=settings.rag_top_k)
    threshold = settings.rag_similarity_threshold
    filtered = [h for h in hits if h.score >= threshold]
    return {"retrieved_chunks": filtered, "status": "retrieved"}


def route_after_retrieve(state: AgentState) -> str:
    return "expand" if state.get("retrieved_chunks") else "no_context"


def graph_expand_context(state: AgentState) -> dict:
    """Walk the knowledge graph around retrieved chunks to build LLM context."""
    kb = get_knowledge_base()
    chunk_ids = [c.chunk_id for c in state["retrieved_chunks"]]
    expansion = kb.graph.expand_from_chunks(chunk_ids, hops=settings.graph_expand_hops)
    context_text = build_context_text(state["retrieved_chunks"], expansion)
    confidence = max(c.score for c in state["retrieved_chunks"])
    return {
        "graph_context": expansion,
        "context_text": context_text,
        "confidence": confidence,
        "status": "context_built",
    }


def generate_answer(state: AgentState) -> dict:
    """LLM generation grounded in retrieved + graph context."""
    llm = get_chat_model()
    messages = [
        SystemMessage(content=system_prompt()),
        HumanMessage(content=user_prompt(state["question"], state["context_text"])),
    ]
    response = llm.invoke(messages)
    answer = response.content if isinstance(response.content, str) else str(response.content)
    return {
        "answer": answer,
        "source": "rag",
        "blocked": False,
        "status": "generated",
    }


def cannot_answer(state: AgentState) -> dict:
    """Fallback when no chunks pass the similarity threshold."""
    if settings.response_language == "en":
        answer = (
            "I couldn't find relevant information about that in our knowledge base. "
            "Please try rephrasing your question or ask about Ziggo internet, TV, or Ziggo GO."
        )
    else:
        answer = (
            "Ik kan daar geen passend antwoord op geven op basis van de beschikbare informatie. "
            "Probeer je vraag anders te formuleren, of vraag naar Ziggo internet, TV of Ziggo GO."
        )
    return {
        "answer": answer,
        "source": "none",
        "confidence": 0.0,
        "blocked": False,
        "status": "no_context",
    }


def return_answer(state: AgentState) -> dict:
    """Terminal node — answer is already in state."""
    return {"status": "completed"}


# --- Cache ---


def cache_lookup(state: AgentState) -> dict:
    """Similarity search in the separate Q&A cache index."""
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
    return {"status": "completed"}


def maybe_cache_answer(state: AgentState) -> dict:
    """Write high-confidence RAG answers back to the cache."""
    if not settings.cache_auto_write or state.get("source") != "rag":
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
        get_cache_store().put(
            question=question,
            answer=answer,
            vector=vector,
            embedding_model=settings.embedding_model,
            source="auto",
        )
        return {"status": "cache_written"}
    except Exception:
        return {"status": "cache_write_failed"}


# --- Security ---


def security_classify(state: AgentState) -> dict:
    """BERT toxicity + zero-shot topic check before RAG."""
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
