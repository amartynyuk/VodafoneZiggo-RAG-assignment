"""API route definitions."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and load balancers."""
    return {"status": "ok", "service": "ai-assistant"}


@router.post("/ask")
async def ask(payload: dict) -> dict:
    """
    Accept a customer question and return an answer.

    Phase 0 stub — LangGraph workflow is added in Phase 3.
    """
    question = payload.get("question", "")
    return {
        "answer": f"[stub] Received your question: {question!r}. LangGraph not wired yet.",
        "source": "stub",
        "confidence": 0.0,
        "blocked": False,
    }
