"""Q&A cache access for the query workflow."""

from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.storage.cache_store import FaissCacheStore
from app.cache.seed import seed_cache_if_empty


@lru_cache
def get_cache_store() -> FaissCacheStore:
    """
    Return the shared cache store, seeding from qa_cache_seed.json if empty.

    Cached in memory for the process lifetime; call get_cache_store.cache_clear()
    after manual cache updates in development.
    """
    store = FaissCacheStore(settings.data_dir)
    store.load()
    seed_cache_if_empty(store)
    return store
