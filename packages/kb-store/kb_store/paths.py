"""Resolve the shared data/ directory and embedding model from the environment."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_data_dir() -> Path:
    """
    DATA_DIR env, or repo data/ when this package lives in packages/kb-store.

    Docker Compose sets DATA_DIR=/app/data on the mounted volume.
    """
    if env := os.environ.get("DATA_DIR"):
        return Path(env)
    here = Path(__file__).resolve()
    # packages/kb-store/kb_store/paths.py → repo root at parents[3]
    if len(here.parents) > 3:
        return here.parents[3] / "data"
    return Path("/app/data")


def embedding_model() -> str:
    """OpenAI embedding model id (default text-embedding-3-small, 1536-d)."""
    return os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
