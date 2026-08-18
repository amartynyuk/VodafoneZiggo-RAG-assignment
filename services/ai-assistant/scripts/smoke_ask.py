#!/usr/bin/env python3
"""Smoke-test POST /ask workflow locally (no HTTP server required)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import run_query
from app.models.schemas import AskRequest


def main() -> None:
    os.environ.setdefault("DATA_DIR", str(Path(__file__).resolve().parents[3] / "data"))

    questions = [
        "Hoeveel apparaten kan ik tegelijk gebruiken met Ziggo GO?",
        "What is Ziggo GO?",
    ]
    for q in questions:
        print(f"\n--- Q: {q} ---")
        result = run_query(AskRequest(question=q))
        print(f"source={result.source} confidence={result.confidence:.3f}")
        print(result.answer[:500])


if __name__ == "__main__":
    main()
