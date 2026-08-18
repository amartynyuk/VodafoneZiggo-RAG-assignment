#!/usr/bin/env python3
"""Smoke-test FAISS + NetworkX stores (load, search, graph expand)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kb_store.embeddings import embed_texts
from kb_store.kb import get_knowledge_base


def main() -> None:
    data_dir = Path(os.environ.get("DATA_DIR", "../../data"))
    os.environ["DATA_DIR"] = str(data_dir.resolve())

    kb = get_knowledge_base()
    print(f"Vector chunks: {len(kb.vectors.records)}")
    print(f"Graph: {kb.graph.node_count} nodes, {kb.graph.edge_count} edges")
    print(f"Embedding model: {kb.vectors.embedding_model or '(none)'}")

    if not kb.vectors.records:
        print("No vectors indexed yet — run ingest first.")
        return

    query = "How many devices can I use with Ziggo GO?"
    hits = kb.vectors.search(embed_texts([query])[0], top_k=3)
    print(f"\nQuery: {query!r}")
    for hit in hits:
        print(f"  score={hit.score:.3f} chunk={hit.chunk_id}")
        print(f"    {hit.text[:100]}...")

    if hits:
        ctx = kb.graph.expand_from_chunks([hits[0].chunk_id])
        print(f"\nGraph expand: {len(ctx['nodes'])} nodes, {len(ctx['edges'])} edges")


if __name__ == "__main__":
    main()
