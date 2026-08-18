"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    if env := os.environ.get("DATA_DIR"):
        return Path(env)
    here = Path(__file__).resolve()
    if len(here.parents) > 3:
        return here.parents[3] / "data"
    return Path("/app/data")


def _env_files() -> tuple[str, ...]:
    candidates = [Path(".env")]
    here = Path(__file__).resolve()
    if len(here.parents) > 3:
        candidates.append(here.parents[3] / ".env")
    return tuple(str(p) for p in candidates if p.exists())


for _env_path in _env_files():
    load_dotenv(_env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_files() or (".env",), extra="ignore")

    data_dir: Path = Field(default_factory=_default_data_dir)
    embedding_model: str = "text-embedding-3-small"  # 1536-d; do not change without re-ingest
    llm_model: str = "gpt-5.6-luna"
    llm_temperature: float = 0.2
    rag_similarity_threshold: float = 0.65
    rag_top_k: int = 5
    graph_expand_hops: int = 1
    response_language: str = "nl"

    # Q&A cache (separate FAISS index)
    cache_similarity_threshold: float = 0.92
    cache_auto_write: bool = True
    cache_min_write_confidence: float = 0.70

    # BERT security gate
    security_enabled: bool = True
    security_toxic_threshold: float = 0.5
    security_offtopic_threshold: float = 0.75


settings = Settings()
