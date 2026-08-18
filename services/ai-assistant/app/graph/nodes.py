"""LangGraph nodes for the RAG query workflow."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.graph.context import build_context_text
from app.graph.state import AgentState
from app.llm.client import get_chat_model
from app.llm.prompts import system_prompt, user_prompt
from app.storage.embeddings import embed_texts
from app.storage.kb import get_knowledge_base


def embed_question(state: AgentState) -> dict:
    """Node 1 — Embed the customer question for vector search."""
    question = state["question"].strip()
    vector = embed_texts([question])[0]
    return {"question_vector": vector, "status": "embedded"}


def vector_retrieve(state: AgentState) -> dict:
    """
    Node 2 — Top-k similarity search in FAISS.

    Filters results below rag_similarity_threshold.
    """
    kb = get_knowledge_base()
    hits = kb.vectors.search(state["question_vector"], top_k=settings.rag_top_k)
    threshold = settings.rag_similarity_threshold
    filtered = [h for h in hits if h.score >= threshold]
    return {"retrieved_chunks": filtered, "status": "retrieved"}


def route_after_retrieve(state: AgentState) -> str:
    """Route to graph expansion or cannot_answer when retrieval is empty."""
    if state.get("retrieved_chunks"):
        return "expand"
    return "no_context"


def graph_expand_context(state: AgentState) -> dict:
    """
    Node 3 — Expand graph around retrieved chunks.

    Pulls parent sections, entities, and adjacent chunks into context_text.
    """
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
    """Node 4 — LLM generation grounded in retrieved + graph context."""
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
    """Terminal node — marks workflow complete (answer already in state)."""
    return {"status": "completed"}
