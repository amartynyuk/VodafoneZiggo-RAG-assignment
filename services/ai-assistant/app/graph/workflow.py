"""LangGraph query workflow definition."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    cannot_answer,
    embed_question,
    generate_answer,
    graph_expand_context,
    return_answer,
    route_after_retrieve,
    vector_retrieve,
)
from app.graph.nodes_cache import (
    cache_lookup,
    maybe_cache_answer,
    return_cached_answer,
    route_after_cache,
)
from app.graph.nodes_security import (
    reject_response,
    route_after_security,
    security_classify,
)
from app.graph.state import AgentState
from app.models.schemas import AskRequest, AskResponse


def build_query_graph():
    """
    Compile the customer query StateGraph.

    Flow:
        embed → cache_lookup → [hit | security → retrieve → expand → generate → maybe_cache]
    """
    graph = StateGraph(AgentState)

    # Core path
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


def run_query(request: AskRequest) -> AskResponse:
    """
    Execute the full query workflow for one customer question.

    LangSmith traces the run as 'ziggo-ask' when LANGSMITH_TRACING=true.
    """
    initial: AgentState = {"question": request.question.strip()}
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
