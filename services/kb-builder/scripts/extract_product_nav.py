#!/usr/bin/env python3
"""
Extract Ziggo product navigation from a saved HTML source file.

Reads the "Producten" main-menu droplet and writes two JSON files:

- structure: hierarchical labels only (no URLs); category items are label lists
- label→URL map: one dict; duplicate labels keep the first URL seen in nav order

Usage:
    python scripts/extract_product_nav.py \\
        --input ../../data/ziggo.nl.txt \\
        --structure-out ../../data/ziggo-product-structure.json \\
        --labels-out ../../data/ziggo-product-label-urls.json
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.ziggo.nl"
MENU_TOP = "producten"


def normalize_url(href: str | None) -> str | None:
    """Turn relative paths into absolute ziggo.nl URLs; leave external URLs unchanged."""
    if not href:
        return None
    href = href.strip()
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(BASE_URL, href)


def link_label(anchor: Tag) -> str:
    """Prefer visible menu text; fall back to analytics slug."""
    text_span = anchor.select_one(".vfz-navigation__droplet-menuitem--text")
    if text_span and text_span.get_text(strip=True):
        return html.unescape(text_span.get_text(strip=True))
    slug = anchor.get("data-ddm-menu-sub-sub") or anchor.get("data-ddm-menu-sub")
    if slug:
        return html.unescape(slug)
    return html.unescape(anchor.get_text(strip=True))


def parse_link(anchor: Tag) -> dict[str, str]:
    return {
        "label": link_label(anchor),
        "url": normalize_url(anchor.get("href")) or "",
    }


def find_producten_droplet(soup: BeautifulSoup) -> Tag | None:
    """Locate the grouped menu list inside the Producten navigation droplet."""
    producten_button = soup.find(
        "button",
        attrs={"data-ddm-menu-top": MENU_TOP, "data-test": "vfz-navigation__main-menuitem-0"},
    )
    if producten_button is None:
        producten_button = soup.find("button", attrs={"data-ddm-menu-top": MENU_TOP})

    if producten_button is None:
        return None

    droplet = producten_button.find_parent("li")
    if droplet is None:
        return None

    return droplet.select_one("ul.vfz-navigation__droplet-grouped-menuitems")


def extract_categories(menu_list: Tag) -> list[dict[str, Any]]:
    """
    Walk top-level <li> sections under Producten.

    Each section is either:
    - a quick link (single <a>, no category toggle), or
    - a category toggle with nested sub-links.
    """
    categories: list[dict[str, Any]] = []

    for section in menu_list.select(":scope > li.vfz-generic-navigation__subitem"):
        quick_link = section.select_one(
            ".vfz-generic-navigation-droplet-item--quick-link a[data-ddm-menu-top='producten']"
        )
        if quick_link:
            link = parse_link(quick_link)
            categories.append(
                {
                    "label": link["label"],
                    "type": "quick_link",
                    "url": link["url"],
                }
            )
            continue

        toggle = section.select_one(
            "button.vfz-navigation__droplet-toggleitem[data-ddm-menu-top='producten']"
        )
        if toggle is None:
            continue

        category_label = html.unescape(
            toggle.select_one(".vfz-navigation__droplet-toggleitem-text").get_text(strip=True)
        )
        sub_anchors = section.select(
            "ul[data-test='droplet-grouped-menuitems'] a[data-ddm-menu-top='producten'][data-ddm-menu-sub-sub]"
        )

        categories.append(
            {
                "label": category_label,
                "type": "category",
                "items": [parse_link(anchor) for anchor in sub_anchors],
            }
        )

    return categories


def build_label_url_dict(categories: list[dict[str, Any]]) -> dict[str, str]:
    """
    Label→URL dict in document order.

    When the same label appears more than once, the first occurrence wins.
    """
    label_urls: dict[str, str] = {}

    for category in categories:
        if category["type"] == "quick_link":
            label = category["label"]
            if label not in label_urls:
                label_urls[label] = category["url"]
            continue

        for item in category.get("items", []):
            label = item["label"]
            if label not in label_urls:
                label_urls[label] = item["url"]

    return label_urls


def to_structure_output(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip URLs; category items become plain label lists."""
    output: list[dict[str, Any]] = []

    for category in categories:
        if category["type"] == "quick_link":
            output.append({"label": category["label"], "type": "quick_link"})
            continue

        output.append(
            {
                "label": category["label"],
                "type": "category",
                "items": [item["label"] for item in category.get("items", [])],
            }
        )

    return output


def extract_product_navigation(html_source: str) -> tuple[dict[str, Any], dict[str, str]]:
    soup = BeautifulSoup(html_source, "html.parser")
    menu_list = find_producten_droplet(soup)

    if menu_list is None:
        raise ValueError(
            f'Could not find Producten menu (data-ddm-menu-top="{MENU_TOP}") in HTML source.'
        )

    categories = extract_categories(menu_list)
    structure = {
        "menu": "Producten",
        "source": BASE_URL,
        "categories": to_structure_output(categories),
    }
    label_urls = build_label_url_dict(categories)
    return structure, label_urls


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    default_input = repo_root / "data" / "ziggo.nl.txt"
    default_structure = repo_root / "data" / "ziggo-product-structure.json"
    default_labels = repo_root / "data" / "ziggo-product-label-urls.json"

    parser = argparse.ArgumentParser(description="Extract Ziggo product nav from saved HTML.")
    parser.add_argument("--input", type=Path, default=default_input, help="HTML source file")
    parser.add_argument(
        "--structure-out",
        type=Path,
        default=default_structure,
        help="Output path for hierarchical structure JSON",
    )
    parser.add_argument(
        "--labels-out",
        type=Path,
        default=default_labels,
        help="Output path for flat label→URL mapping JSON",
    )
    args = parser.parse_args()

    html_source = args.input.read_text(encoding="utf-8")
    structure, label_urls = extract_product_navigation(html_source)

    write_json(args.structure_out, structure)
    write_json(args.labels_out, label_urls)

    category_count = len(structure["categories"])
    link_count = len(label_urls)
    print(f"Wrote {category_count} top-level categories and {link_count} unique label→URL mappings")
    print(f"  structure: {args.structure_out}")
    print(f"  labels:    {args.labels_out}")


if __name__ == "__main__":
    main()
