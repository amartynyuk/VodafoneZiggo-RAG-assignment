"""
FAISS-backed Q&A cache (separate from the RAG chunk index).

Stores question embeddings → cached answers for cost/latency savings.
Files: cache.faiss, cache_meta.json, cache_vectors.npy
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from kb_store.models import CacheHit, CacheRecord


class FaissCacheStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.index_path = data_dir / "cache.faiss"
        self.meta_path = data_dir / "cache_meta.json"
        self.vectors_path = data_dir / "cache_vectors.npy"
        self.records: list[CacheRecord] = []
        self.vectors: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self.embedding_model: str = ""
        self.dimension: int = 0
        self._index: faiss.Index | None = None

    def load(self) -> None:
        if self.meta_path.exists():
            payload = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self.embedding_model = payload.get("embedding_model", "")
            self.dimension = int(payload.get("dimension", 0))
            self.records = [CacheRecord(**r) for r in payload.get("records", [])]
        if self.vectors_path.exists() and self.records:
            self.vectors = np.load(self.vectors_path)
        if self.index_path.exists() and self.dimension > 0:
            self._index = faiss.read_index(str(self.index_path))
        else:
            self._rebuild_index()

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "embedding_model": self.embedding_model,
            "dimension": self.dimension,
            "records": [r.model_dump() for r in self.records],
        }
        self.meta_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if self.vectors.size:
            np.save(self.vectors_path, self.vectors)
        if self._index is not None and self._index.ntotal > 0:
            faiss.write_index(self._index, str(self.index_path))

    def lookup(self, query_vector: list[float], threshold: float) -> CacheHit | None:
        """Return best cache hit if similarity ≥ threshold."""
        if self._index is None or self._index.ntotal == 0:
            return None
        if self.dimension and len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector dim {len(query_vector)} != cache dim {self.dimension}."
            )
        q = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q)
        scores, indices = self._index.search(q, 1)
        score = float(scores[0][0])
        idx = int(indices[0][0])
        if idx < 0 or score < threshold:
            return None
        rec = self.records[idx]
        return CacheHit(
            question=rec.question,
            answer=rec.answer,
            score=score,
            source=rec.source,
        )

    def put(
        self,
        question: str,
        answer: str,
        vector: list[float],
        embedding_model: str,
        source: str = "auto",
    ) -> None:
        """Append a new Q&A pair to the cache."""
        matrix = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(matrix)

        if self.vectors.size == 0:
            self.vectors = matrix
            self.dimension = matrix.shape[1]
        else:
            self.vectors = np.vstack([self.vectors, matrix])

        self.embedding_model = embedding_model
        self.records.append(
            CacheRecord(question=question, answer=answer, source=source)
        )
        self._rebuild_index()
        self.save()

    def _rebuild_index(self) -> None:
        if self.vectors.size == 0 or self.dimension == 0:
            self._index = faiss.IndexFlatIP(self.dimension or 1)
            return
        self._index = faiss.IndexFlatIP(self.dimension)
        self._index.add(self.vectors)

    @property
    def size(self) -> int:
        return len(self.records)
