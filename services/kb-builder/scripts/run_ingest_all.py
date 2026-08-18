#!/usr/bin/env python3
"""
Ingest all Ziggo product pages from ziggo-product-label-urls.json.

Deduplicates by URL (several nav labels share the same page). Each unique URL
is ingested once through the full LangGraph pipeline (scrape → LLM → FAISS + graph).

Usage (from services/kb-builder):
    DATA_DIR=../../data .venv/bin/python scripts/run_ingest_all.py

    # Preview without ingesting
    DATA_DIR=../../data .venv/bin/python scripts/run_ingest_all.py --dry-run

    # Only www.ziggo.nl pages (skip directsales / hollandsnieuwe)
    DATA_DIR=../../data .venv/bin/python scripts/run_ingest_all.py --ziggo-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.schemas import IngestRequest
from app.pipeline.graph import run_ingest
from app.storage.kb import get_knowledge_base


def load_label_urls(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Label→URL map not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unique_pages(
    label_urls: dict[str, str],
    *,
    ziggo_only: bool = False,
) -> list[tuple[str, str]]:
    """
    Return (label, url) pairs deduplicated by URL.

    When multiple labels point to the same URL, the first label in file order wins.
    """
    seen_urls: set[str] = set()
    pages: list[tuple[str, str]] = []

    for label, url in label_urls.items():
        normalized = url.rstrip("/")
        if ziggo_only and not _is_ziggo_site(normalized):
            continue
        if normalized in seen_urls:
            continue
        seen_urls.add(normalized)
        pages.append((label, url))

    return pages


def _is_ziggo_site(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith("ziggo.nl")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest all unique pages from ziggo-product-label-urls.json",
    )
    parser.add_argument(
        "--labels-file",
        type=Path,
        default=None,
        help="Path to label→URL JSON (default: DATA_DIR/ziggo-product-label-urls.json)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.environ.get("DATA_DIR", "../../data")),
        help="Shared data directory (FAISS + graph output)",
    )
    parser.add_argument(
        "--ziggo-only",
        action="store_true",
        help="Skip external partner URLs (directsales.ziggo.nl, hollandsnieuwe.nl, …)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pages that would be ingested without running the pipeline",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first ingest failure",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write JSON summary report to this path",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    os.environ["DATA_DIR"] = str(data_dir)

    labels_path = args.labels_file or (data_dir / "ziggo-product-label-urls.json")
    label_urls = load_label_urls(labels_path)
    pages = unique_pages(label_urls, ziggo_only=args.ziggo_only)

    print(f"Label map: {len(label_urls)} entries → {len(pages)} unique URLs")
    if args.ziggo_only:
        print("(ziggo-only mode: external partner URLs skipped)")

    if args.dry_run:
        for i, (label, url) in enumerate(pages, start=1):
            print(f"  {i:2}. [{label}] {url}")
        return

    started = time.time()
    results: list[dict] = []
    failures = 0

    for i, (label, url) in enumerate(pages, start=1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(pages)}] {label}")
        print(f"  {url}")
        print("=" * 60)

        try:
            result = run_ingest(IngestRequest(label=label))
            row = result.model_dump()
            results.append(row)

            if result.status == "failed" or result.warnings:
                failures += 1
                print(json.dumps(row, indent=2, ensure_ascii=False))
                if args.fail_fast and result.status == "failed":
                    print("Stopping (--fail-fast).")
                    break
            else:
                print(
                    f"  ✓ chunks={result.chunks_count} entities={result.entities_extracted} "
                    f"vectors={result.vectors_indexed} quality={result.content_quality}"
                )
                if result.warnings:
                    for w in result.warnings:
                        print(f"  ⚠ {w}")
        except Exception as exc:
            failures += 1
            err = {"label": label, "url": url, "status": "error", "error": str(exc)}
            results.append(err)
            print(f"  ✗ ERROR: {exc}")
            if args.fail_fast:
                print("Stopping (--fail-fast).")
                break

    elapsed = time.time() - started

    # Final KB stats
    try:
        kb = get_knowledge_base()
        store = {
            "vector_chunks": len(kb.vectors.records),
            "graph_nodes": kb.graph.node_count,
            "graph_edges": kb.graph.edge_count,
        }
    except Exception as exc:
        store = {"error": str(exc)}

    summary = {
        "pages_attempted": len(results),
        "pages_total_unique": len(pages),
        "failures": failures,
        "elapsed_seconds": round(elapsed, 1),
        "store": store,
        "results": results,
    }

    print(f"\n{'=' * 60}")
    print("BATCH INGEST COMPLETE")
    print(f"  Pages: {len(results)}/{len(pages)}  Failures: {failures}  Time: {elapsed:.0f}s")
    print(f"  KB: {store}")
    print("=" * 60)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
