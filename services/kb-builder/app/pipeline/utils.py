"""Shared utilities for ingest pipeline nodes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings


def page_id_from_url(url: str) -> str:
    """
    Derive a stable page_id from a ziggo.nl URL path.

    Examples:
        https://www.ziggo.nl/televisie/ziggo-go → televisie_ziggo-go
        https://www.ziggo.nl/tv-internet → tv-internet
    """
    path = urlparse(url).path.strip("/")
    return path.replace("/", "_") if path else "home"


def resolve_url(page_url: str | None, label: str | None) -> tuple[str, str | None]:
    """
    Resolve ingest target from URL and/or nav label.

    Returns:
        (url, label) — label may be None if only URL was given.
    """
    label_map = load_label_urls()

    if page_url:
        url = str(page_url)
        # Reverse lookup label when possible.
        for nav_label, nav_url in label_map.items():
            if nav_url.rstrip("/") == url.rstrip("/"):
                return url, nav_label
        return url, label

    if label:
        if label not in label_map:
            raise ValueError(f"Unknown label {label!r}. Check ziggo-product-label-urls.json.")
        return label_map[label], label

    raise ValueError("Provide page_url or label.")


def load_label_urls() -> dict[str, str]:
    path = settings.label_urls_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
