"""LangGraph node: resolve URL and page_id."""

from __future__ import annotations

from app.pipeline.state import IngestState
from app.pipeline.utils import page_id_from_url, resolve_url


def resolve_input(state: IngestState) -> dict:
    """
    Node 1 — Resolve ingest target.

    Input:  page_url and/or label from API request.
    Output: canonical page_url, page_id, optional nav label.
    """
    url, label = resolve_url(state.get("page_url"), state.get("label"))
    return {
        "page_url": url,
        "label": label or state.get("label"),
        "status": "resolved",
    }


def attach_page_id(state: IngestState) -> dict:
    """Helper used by fetch node to set metadata.page_id early."""
    page_id = page_id_from_url(state["page_url"])
    return {"status": "page_id_set", "page_id": page_id}
