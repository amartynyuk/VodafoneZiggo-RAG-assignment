#!/usr/bin/env python3
"""
Run the ingest LangGraph on sample URLs from ziggo-product-label-urls.json.

For a full batch ingest of all unique pages, use run_ingest_all.py instead.

Usage (from services/kb-builder):
    DATA_DIR=../../data .venv/bin/python scripts/run_ingest_sample.py
    DATA_DIR=../../data .venv/bin/python scripts/run_ingest_sample.py --label "Ziggo GO"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow `python scripts/run_ingest_sample.py` without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.schemas import IngestRequest
from app.pipeline.graph import run_ingest

DEFAULT_LABELS = ("Ziggo GO", "Internet & TV")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run KB ingest on sample Ziggo pages.")
    parser.add_argument(
        "--label",
        action="append",
        help="Nav label from ziggo-product-label-urls.json (repeatable)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.environ.get("DATA_DIR", "../../data")),
        help="Output directory for page artifacts",
    )
    args = parser.parse_args()

    os.environ["DATA_DIR"] = str(args.data_dir.resolve())

    labels = args.label or list(DEFAULT_LABELS)
    results = []

    for label in labels:
        print(f"\n--- Ingesting: {label} ---")
        result = run_ingest(IngestRequest(label=label))
        results.append(result.model_dump())
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

    print(f"\nDone. {len(results)} page(s) written to {args.data_dir / 'pages'}")


if __name__ == "__main__":
    main()
