"""
HTTP fetch layer for Ziggo pages.

Uses requests (assignment baseline). Ziggo product pages are a mix of:
- **Rich static HTML** (e.g. /televisie/ziggo-go) — full h2/h3 copy in the initial response.
- **Sparse shells** (e.g. /tv-internet) — pricing tables rendered client-side; we still
  capture metadata and flag content_quality=sparse for later Playwright if needed.
"""

from __future__ import annotations

import requests

from app.config import settings


class FetchError(Exception):
    """Raised when the HTTP request fails or returns a non-2xx status."""


def fetch_page_html(url: str, timeout: int = 30) -> str:
    """
    Download raw HTML for a Ziggo page.

    Args:
        url: Absolute page URL (https://www.ziggo.nl/...).
        timeout: Request timeout in seconds.

    Returns:
        Raw HTML string.

    Raises:
        FetchError: On network errors or HTTP status >= 400.
    """
    headers = {
        "User-Agent": settings.user_agent,
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc

    if response.status_code >= 400:
        raise FetchError(f"HTTP {response.status_code} for {url}")

    return response.text
