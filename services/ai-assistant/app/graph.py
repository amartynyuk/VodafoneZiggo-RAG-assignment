"""
LangGraph query workflow.

Wires nodes from nodes.py into a StateGraph. HTTP and smoke scripts call run_query().
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.nodes import (
    AgentState,
    cache_lookup,
    cannot_answer,
    embed_question,
    generate_answer,
    graph_expand_context,
    maybe_cache_answer,
    reject_response,
    return_answer,
    return_cached_answer,
    route_after_cache,
    route_after_retrieve,
    route_after_security,
    security_classify,
    vector_retrieve,
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Customer question about Ziggo products/services")


class AskResponse(BaseModel):
    answer: str
    source: Literal["cache", "rag", "none"] = "rag"
    confidence: float = Field(ge=0.0, le=1.0)
    blocked: bool = False


def build_query_graph():
    """
    Compile the customer query StateGraph.

    Flow:
        embed → cache_lookup → [hit | security → retrieve → expand → generate → maybe_cache]
    """
    graph = StateGraph(AgentState)

    graph.add_node("embed_question", embed_question)
    graph.add_node("cache_lookup", cache_lookup)
    graph.add_node("return_cached_answer", return_cached_answer)
    graph.add_node("security_classify", security_classify)
    graph.add_node("reject_response", reject_response)
    graph.add_node("vector_retrieve", vector_retrieve)
    graph.add_node("graph_expand_context", graph_expand_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("maybe_cache_answer", maybe_cache_answer)
    graph.add_node("cannot_answer", cannot_answer)
    graph.add_node("return_answer", return_answer)

    graph.add_edge(START, "embed_question")
    graph.add_edge("embed_question", "cache_lookup")
    graph.add_conditional_edges(
        "cache_lookup",
        route_after_cache,
        {"hit": "return_cached_answer", "miss": "security_classify"},
    )
    graph.add_conditional_edges(
        "security_classify",
        route_after_security,
        {"allow": "vector_retrieve", "block": "reject_response"},
    )
    graph.add_conditional_edges(
        "vector_retrieve",
        route_after_retrieve,
        {"expand": "graph_expand_context", "no_context": "cannot_answer"},
    )
    graph.add_edge("graph_expand_context", "generate_answer")
    graph.add_edge("generate_answer", "maybe_cache_answer")
    graph.add_edge("maybe_cache_answer", "return_answer")
    graph.add_edge("cannot_answer", "return_answer")
    graph.add_edge("reject_response", "return_answer")
    graph.add_edge("return_cached_answer", END)
    graph.add_edge("return_answer", END)

    return graph.compile()


QUERY_GRAPH = build_query_graph()


def run_query(question: str) -> AskResponse:
    """
    Execute the full query workflow for one customer question.

    LangSmith traces the run as 'ziggo-ask' when LANGSMITH_TRACING=true.
    """
    initial: AgentState = {"question": question.strip()}
    final = QUERY_GRAPH.invoke(
        initial,
        config={"run_name": "ziggo-ask"},
    )
    return AskResponse(
        answer=final.get("answer", ""),
        source=final.get("source", "none"),  # type: ignore[arg-type]
        confidence=float(final.get("confidence", 0.0)),
        blocked=final.get("blocked", False),
    )
