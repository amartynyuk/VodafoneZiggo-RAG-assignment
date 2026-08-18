"""LangGraph node: embed chunks and persist FAISS + NetworkX."""

from __future__ import annotations

from app.config import settings
from app.pipeline.state import IngestState
from app.storage.embeddings import embed_texts
from app.storage.kb import KnowledgeBase


def index_knowledge_base(state: IngestState) -> dict:
    """
    Node 9 — Embed chunks and save to shared vector + graph stores.

    Writes:
        data/rag.faiss, data/rag_meta.json, data/rag_vectors.npy
        data/graph.json

    Re-ingest replaces vectors and graph nodes for the same page_id only.
    """
    metadata = state["metadata"]
    chunks = state.get("chunks", [])
    if not chunks:
        return {"warnings": ["No chunks to index."], "status": "index_skipped"}

    try:
        vectors = embed_texts([c.text for c in chunks])
        kb = KnowledgeBase()
        stats = kb.upsert_page(
            page_id=metadata.page_id,
            chunks=chunks,
            vectors=vectors,
            graph_nodes=state.get("graph_nodes", []),
            graph_edges=state.get("graph_edges", []),
            embedding_model=settings.embedding_model,
        )
        return {
            "status": "indexed",
            "vectors_indexed": stats["vectors_indexed"],
            "graph_nodes_total": stats["graph_nodes"],
            "graph_edges_total": stats["graph_edges"],
        }
    except Exception as exc:
        return {
            "warnings": [f"KB indexing failed: {exc}"],
            "status": "index_failed",
        }
