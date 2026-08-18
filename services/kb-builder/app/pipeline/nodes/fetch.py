"""LangGraph node: HTTP fetch."""

from __future__ import annotations

from app.pipeline.state import IngestState
from app.pipeline.utils import page_id_from_url
from app.scrape.fetcher import FetchError, fetch_page_html


def fetch_html(state: IngestState) -> dict:
    """
    Node 2 — Download raw HTML.

    Input:  page_url
    Output: raw_html
    """
    url = state["page_url"]
    try:
        html = fetch_page_html(url)
    except FetchError as exc:
        return {"status": "failed", "errors": [str(exc)]}
    return {"raw_html": html, "status": "fetched"}


def route_after_fetch(state: IngestState) -> str:
    """Conditional edge: stop pipeline on fetch failure."""
    if state.get("errors"):
        return "failed"
    return "clean"
