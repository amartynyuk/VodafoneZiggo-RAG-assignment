"""API route definitions."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and load balancers."""
    return {"status": "ok", "service": "kb-builder"}


@router.post("/ingest")
async def ingest(payload: dict) -> dict:
    """
    Re-ingest a single Ziggo page by URL.

    Phase 0 stub — full pipeline is added in Phase 2.
    """
    page_url = payload.get("page_url", "")
    return {
        "page_id": "stub",
        "page_url": page_url,
        "chunks_created": 0,
        "entities_extracted": 0,
        "status": "stub — ingest pipeline not wired yet",
    }


@router.get("/status")
async def status() -> dict:
    """Return ingest status per page (Phase 2+)."""
    return {"pages": []}
