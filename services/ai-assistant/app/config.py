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
    embedding_model: str = "text-embedding-3-small"
    rag_similarity_threshold: float = 0.75


settings = Settings()
