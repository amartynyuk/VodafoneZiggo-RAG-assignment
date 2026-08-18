"""
Deterministic section parsing from cleaned content HTML.

Pattern observed on ziggo.nl (e.g. /televisie/ziggo-go):
- <main> contains <section> blocks with vfz-spacing-* classes
- Product copy follows h1 → h2 → h3 hierarchy with sibling <p> tags
- Feature grids use h3 + p pairs under a shared h2
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from app.models.schemas import SectionBlock


def parse_sections(content_html: str, page_id: str) -> list[SectionBlock]:
    """
    Walk the content DOM and emit heading-delimited sections.

    Each time we hit h1–h4 we start a new section. Inline text and paragraphs
    until the next heading are appended to that section's body.
    """
    soup = BeautifulSoup(content_html, "html.parser")
    sections: list[SectionBlock] = []
    current_heading = ""
    current_level = 1
    current_lines: list[str] = []
    order = 0

    def flush() -> None:
        nonlocal order
        text = _normalize_section_text("\n".join(current_lines))
        heading = current_heading.strip()
        if not heading and not text:
            return
        if not heading:
            heading = "Introduction"
        order += 1
        slug = _slugify(heading) or f"section-{order}"
        sections.append(
            SectionBlock(
                section_id=f"{page_id}::{slug}",
                heading=heading,
                level=current_level,
                text=text,
                order=order,
            )
        )

    # Depth-first walk keeps document order stable for NEXT edges later.
    for element in soup.descendants:
        if isinstance(element, NavigableString):
            if element.parent and element.parent.name in ("script", "style"):
                continue
            line = str(element).strip()
            if line and element.parent and element.parent.name in ("p", "li", "span", "div"):
                # Avoid duplicating text already captured via heading tags.
                if element.parent.name in ("p", "li"):
                    current_lines.append(line)
            continue

        if not isinstance(element, Tag):
            continue

        if element.name in ("h1", "h2", "h3", "h4"):
            flush()
            current_heading = element.get_text(strip=True)
            current_level = int(element.name[1])
            current_lines = []

    flush()
    return sections


def _normalize_section_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:60]
