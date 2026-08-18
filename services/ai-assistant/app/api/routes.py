"""API route definitions."""

from fastapi import APIRouter, HTTPException

from app.graph.workflow import run_query
from app.models.schemas import AskRequest, AskResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and load balancers."""
    return {"status": "ok", "service": "ai-assistant"}


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """
    Accept a customer question and return a graph-augmented RAG answer.

    Workflow: embed → retrieve → graph expand → generate (LangGraph).
    LangSmith traces each step when LANGSMITH_TRACING=true.
    """
    try:
        return run_query(request)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not indexed yet. Run kb-builder ingest first.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
