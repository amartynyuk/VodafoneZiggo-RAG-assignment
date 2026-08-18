"""API route definitions."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import IngestRequest, IngestResult
from app.pipeline.graph import run_ingest

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and load balancers."""
    return {"status": "ok", "service": "kb-builder"}


@router.post("/ingest", response_model=IngestResult)
async def ingest(request: IngestRequest) -> IngestResult:
    """
    Re-ingest a single Ziggo page by URL or nav label.

    Runs the LangGraph ingest pipeline (deterministic nodes + LLM stubs).
    """
    if not request.page_url and not request.label:
        raise HTTPException(status_code=400, detail="Provide page_url or label.")

    try:
        return run_ingest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
async def status() -> dict:
    """List ingested page bundles from data/pages/."""
    from app.config import settings

    pages_dir = settings.data_dir / "pages"
    if not pages_dir.exists():
        return {"pages": []}

    pages = []
    for path in sorted(pages_dir.glob("*.json")):
        pages.append({"page_id": path.stem, "artifact": str(path.name)})
    return {"pages": pages}
