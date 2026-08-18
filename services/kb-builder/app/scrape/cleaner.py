"""
HTML cleaning and main-content extraction.

Strips navigation, footer, scripts, and cookie UI so downstream nodes
work on product copy only.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

# Tags removed entirely before text extraction.
_STRIP_TAGS = ("script", "style", "noscript", "svg", "iframe")
# Containers treated as boilerplate (Ziggo vfz-* nav patterns).
_BOILERPLATE_SELECTORS = (
    "nav",
    "footer",
    "header.vfz-navigation",
    "[data-test*='cookie']",
    "[class*='cookie']",
    "[class*='consent']",
)


def _strip_boilerplate(soup: BeautifulSoup) -> None:
    """Remove known noise regions in-place."""
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for selector in _BOILERPLATE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()


def _pick_content_root(soup: BeautifulSoup) -> Tag:
    """
    Prefer semantic main content; fall back to body.

    Ziggo pages consistently expose <main>; article is secondary.
    """
    for selector in ("main", "article", "[role='main']"):
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 50:
            return el
    body = soup.body
    if body is None:
        raise ValueError("No <body> in HTML document")
    return body


def clean_html(raw_html: str) -> tuple[str, str, int]:
    """
    Parse HTML and return cleaned plain text plus the content subtree HTML.

    Returns:
        Tuple of (plain_text, content_html, main_char_count_before_clean).
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    root = _pick_content_root(soup)
    main_char_count = len(root.get_text(strip=True))

    # Work on a copy of the content subtree only.
    content_soup = BeautifulSoup(str(root), "html.parser")
    _strip_boilerplate(content_soup)

    plain = _normalize_whitespace(content_soup.get_text(separator="\n", strip=True))
    return plain, str(content_soup), main_char_count


def _normalize_whitespace(text: str) -> str:
    """Collapse excessive blank lines and spaces."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_head_metadata(soup: BeautifulSoup) -> dict[str, str | None]:
    """Read deterministic metadata from <head> without an LLM."""

    def meta_content(name: str | None = None, prop: str | None = None) -> str | None:
        attrs: dict[str, str] = {}
        if name:
            attrs["name"] = name
        if prop:
            attrs["property"] = prop
        tag = soup.find("meta", attrs=attrs)
        return tag.get("content") if tag else None

    title_tag = soup.find("title")
    return {
        "title": title_tag.get_text(strip=True) if title_tag else None,
        "meta_description": meta_content(name="description"),
        "og_title": meta_content(prop="og:title"),
        "og_description": meta_content(prop="og:description"),
    }
