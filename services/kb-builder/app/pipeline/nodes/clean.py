"""LangGraph nodes: clean HTML and extract head metadata."""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.config import settings
from app.models.schemas import ContentQuality, PageMetadata
from app.pipeline.state import IngestState
from app.pipeline.utils import page_id_from_url
from app.scrape.cleaner import clean_html, extract_head_metadata


def clean_and_extract(state: IngestState) -> dict:
    """
    Node 3 — Strip boilerplate and read <head> metadata.

    Input:  raw_html, page_url, label
    Output: cleaned_text, content_html, metadata, content_quality, warnings
    """
    raw_html = state["raw_html"]
    page_url = state["page_url"]
    page_id = page_id_from_url(page_url)

    soup = BeautifulSoup(raw_html, "html.parser")
    head_meta = extract_head_metadata(soup)
    cleaned_text, content_html, main_char_count = clean_html(raw_html)

    quality = (
        ContentQuality.RICH
        if main_char_count >= settings.min_main_text_chars
        else ContentQuality.SPARSE
    )

    warnings: list[str] = []
    if quality == ContentQuality.SPARSE:
        warnings.append(
            f"Sparse static content ({main_char_count} chars in <main>). "
            "Pricing/tables may need Playwright for full extraction."
        )

    metadata = PageMetadata(
        url=page_url,
        page_id=page_id,
        label=state.get("label"),
        title=head_meta["title"],
        meta_description=head_meta["meta_description"],
        og_title=head_meta["og_title"],
        og_description=head_meta["og_description"],
    )

    return {
        "cleaned_text": cleaned_text,
        "content_html": content_html,
        "main_char_count": main_char_count,
        "content_quality": quality,
        "metadata": metadata,
        "warnings": warnings,
        "status": "cleaned",
    }
