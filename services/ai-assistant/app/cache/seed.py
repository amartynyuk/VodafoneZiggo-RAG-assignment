"""Load seed Q&A pairs into the cache index when empty."""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.storage.cache_store import FaissCacheStore
from app.storage.embeddings import embed_texts
from app.storage.models import CacheRecord


def seed_cache_if_empty(cache: FaissCacheStore) -> int:
    """
    Populate cache from data/qa_cache_seed.json when no entries exist.

    Returns number of seed entries added.
    """
    if cache.records:
        return 0

    seed_path = settings.data_dir / "qa_cache_seed.json"
    if not seed_path.exists():
        return 0

    entries = json.loads(seed_path.read_text(encoding="utf-8"))
    if not entries:
        return 0

    questions = [e["question"] for e in entries]
    vectors = embed_texts(questions)

    cache.embedding_model = settings.embedding_model
    matrix = np.array(vectors, dtype=np.float32)
    faiss.normalize_L2(matrix)
    cache.vectors = matrix
    cache.dimension = matrix.shape[1]
    cache.records = [
        CacheRecord(
            question=e["question"],
            answer=e["answer"],
            source="seed",
        )
        for e in entries
    ]
    cache._rebuild_index()
    cache.save()
    return len(entries)
