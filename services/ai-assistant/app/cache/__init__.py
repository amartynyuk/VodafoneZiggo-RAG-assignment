"""Q&A cache: load the FAISS index once, seed from JSON if empty."""

from __future__ import annotations

import json
from functools import lru_cache

import faiss
import numpy as np

from app.config import settings
from kb_store.cache_store import FaissCacheStore
from kb_store.embeddings import embed_texts
from kb_store.models import CacheRecord


def seed_cache_if_empty(cache: FaissCacheStore) -> int:
    """Populate cache from data/qa_cache_seed.json when no entries exist."""
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
        CacheRecord(question=e["question"], answer=e["answer"], source="seed")
        for e in entries
    ]
    cache._rebuild_index()
    cache.save()
    return len(entries)


@lru_cache
def get_cache_store() -> FaissCacheStore:
    """Process-wide cache store; seeded on first load if the index is empty."""
    store = FaissCacheStore(settings.data_dir)
    store.load()
    seed_cache_if_empty(store)
    return store
