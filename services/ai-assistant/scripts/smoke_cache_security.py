#!/usr/bin/env python3
"""Test cache hits and BERT security gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph import run_query


def main() -> None:
    os.environ.setdefault("DATA_DIR", str(Path(__file__).resolve().parents[3] / "data"))

    cases = [
        ("cache hit", "What is Ziggo GO?"),
        ("cache hit NL", "Hoeveel apparaten kan ik tegelijk gebruiken met Ziggo GO?"),
        ("rag path", "Welke mediaboxen biedt Ziggo aan?"),
        ("off-topic", "What is the capital of France?"),
        ("toxic", "I hate you, you stupid bot"),
    ]

    for label, question in cases:
        print(f"\n--- {label}: {question!r} ---")
        result = run_query(question)
        print(f"source={result.source} blocked={result.blocked} confidence={result.confidence:.3f}")
        print(result.answer[:200])


if __name__ == "__main__":
    main()
