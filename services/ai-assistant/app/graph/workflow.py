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
from app.graph.state import AgentState
from app.models.schemas import AskRequest, AskResponse


def build_query_graph():
    """
    Compile the customer query StateGraph.

    Flow:
        embed_question → vector_retrieve → [expand | cannot_answer]
        expand → generate_answer → return_answer
        cannot_answer → return_answer
    """
    graph = StateGraph(AgentState)

    graph.add_node("embed_question", embed_question)
    graph.add_node("vector_retrieve", vector_retrieve)
    graph.add_node("graph_expand_context", graph_expand_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("cannot_answer", cannot_answer)
    graph.add_node("return_answer", return_answer)

    graph.add_edge(START, "embed_question")
    graph.add_edge("embed_question", "vector_retrieve")
    graph.add_conditional_edges(
        "vector_retrieve",
        route_after_retrieve,
        {"expand": "graph_expand_context", "no_context": "cannot_answer"},
    )
    graph.add_edge("graph_expand_context", "generate_answer")
    graph.add_edge("generate_answer", "return_answer")
    graph.add_edge("cannot_answer", "return_answer")
    graph.add_edge("return_answer", END)

    return graph.compile()


QUERY_GRAPH = build_query_graph()


def run_query(request: AskRequest) -> AskResponse:
    """
    Execute the RAG workflow for one customer question.

    LangSmith traces the run when LANGSMITH_TRACING=true (see root .env).
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
