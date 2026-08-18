"""
FAISS vector store for RAG chunk retrieval.

Uses IndexFlatIP on L2-normalized vectors (cosine similarity).
Persists:
  - rag.faiss       — FAISS index
  - rag_meta.json   — chunk metadata (no raw vectors)
  - rag_vectors.npy — float32 matrix aligned with meta records (for re-ingest rebuild)
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from kb_store.models import ChunkVectorRecord, ScoredChunk


class FaissVectorStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.index_path = data_dir / "rag.faiss"
        self.meta_path = data_dir / "rag_meta.json"
        self.vectors_path = data_dir / "rag_vectors.npy"
        self.records: list[ChunkVectorRecord] = []
        self.vectors: np.ndarray = np.empty((0, 0), dtype=np.float32)
        self.embedding_model: str = ""
        self.dimension: int = 0
        self._index: faiss.Index | None = None

    def load(self) -> None:
        """Load index + metadata from disk (no-op if files missing)."""
        if self.meta_path.exists():
            payload = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self.embedding_model = payload.get("embedding_model", "")
            self.dimension = int(payload.get("dimension", 0))
            self.records = [ChunkVectorRecord(**r) for r in payload.get("records", [])]
        if self.vectors_path.exists() and self.records:
            self.vectors = np.load(self.vectors_path)
        if self.index_path.exists() and self.dimension > 0:
            self._index = faiss.read_index(str(self.index_path))
        else:
            self._rebuild_index()

    def save(self) -> None:
        """Persist index, metadata, and vector matrix."""
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
        if self._index is not None:
            faiss.write_index(self._index, str(self.index_path))

    def delete_by_page(self, page_id: str) -> int:
        """Remove all vectors for a page; returns count removed."""
        if not self.records:
            return 0
        keep_idx = [i for i, r in enumerate(self.records) if r.page_id != page_id]
        removed = len(self.records) - len(keep_idx)
        if removed == 0:
            return 0
        self.records = [self.records[i] for i in keep_idx]
        self.vectors = self.vectors[keep_idx] if self.vectors.size else self.vectors
        self._rebuild_index()
        return removed

    def upsert_chunks(
        self,
        page_id: str,
        chunk_ids: list[str],
        section_ids: list[str],
        texts: list[str],
        orders: list[int],
        vectors: list[list[float]],
        embedding_model: str,
    ) -> int:
        """
        Replace all chunks for page_id, then append new embedded records.

        Returns number of chunks indexed.
        """
        self.delete_by_page(page_id)
        if not vectors:
            return 0

        self.embedding_model = embedding_model
        matrix = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(matrix)
        self.dimension = matrix.shape[1]

        new_records = [
            ChunkVectorRecord(
                chunk_id=cid,
                page_id=page_id,
                section_id=sid,
                text=text,
                order=order,
            )
            for cid, sid, text, order in zip(chunk_ids, section_ids, texts, orders, strict=True)
        ]

        if self.vectors.size == 0:
            self.vectors = matrix
        else:
            self.vectors = np.vstack([self.vectors, matrix])
        self.records.extend(new_records)
        self._rebuild_index()
        return len(new_records)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[ScoredChunk]:
        """Cosine similarity search; returns chunks ranked by score."""
        if self._index is None or self._index.ntotal == 0:
            return []
        if self.dimension and len(query_vector) != self.dimension:
            raise ValueError(
                f"Query vector dim {len(query_vector)} != index dim {self.dimension}. "
                "Re-ingest after changing EMBEDDING_MODEL."
            )
        q = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q)
        scores, indices = self._index.search(q, min(top_k, self._index.ntotal))
        hits: list[ScoredChunk] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0:
                continue
            rec = self.records[idx]
            hits.append(
                ScoredChunk(
                    chunk_id=rec.chunk_id,
                    page_id=rec.page_id,
                    section_id=rec.section_id,
                    text=rec.text,
                    score=float(score),
                )
            )
        return hits

    def _rebuild_index(self) -> None:
        if self.vectors.size == 0 or self.dimension == 0:
            self._index = faiss.IndexFlatIP(self.dimension or 1)
            return
        self._index = faiss.IndexFlatIP(self.dimension)
        self._index.add(self.vectors)
