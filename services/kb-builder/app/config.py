"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


def _default_data_dir() -> Path:
    """DATA_DIR env, or repo data/ when running locally outside Docker."""
    if env := os.environ.get("DATA_DIR"):
        return Path(env)
    here = Path(__file__).resolve()
    # .../services/kb-builder/app/config.py → repo root at parents[3]
    if len(here.parents) > 3:
        return here.parents[3] / "data"
    return Path("/app/data")


def _env_files() -> tuple[str, ...]:
    """Load root .env when running locally from services/kb-builder."""
    candidates = [Path(".env")]
    here = Path(__file__).resolve()
    if len(here.parents) > 3:
        candidates.append(here.parents[3] / ".env")
    return tuple(str(p) for p in candidates if p.exists())


# LangChain reads OPENAI_API_KEY / LANGSMITH_* from os.environ — load root .env first.
for _env_path in _env_files():
    load_dotenv(_env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files() or (".env",),
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=_default_data_dir)
    user_agent: str = "Mozilla/5.0 (compatible; ZiggoRAGBot/0.1)"
    min_main_text_chars: int = 1500
    max_chunk_chars: int = 1200

    # OpenAI / LangSmith (keys via env; LangSmith auto-traces when LANGSMITH_TRACING=true)
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_chunk_batch_size: int = 5
    embedding_model: str = "text-embedding-3-small"  # 1536-d; do not change without re-ingest

    @property
    def label_urls_path(self) -> Path:
        """Label→URL map lives in the shared data/ volume."""
        return self.data_dir / "ziggo-product-label-urls.json"


settings = Settings()
