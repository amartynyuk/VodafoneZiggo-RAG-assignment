"""Facade over FAISS + NetworkX stores in the shared data/ directory."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from kb_store.graph_store import NetworkXGraphStore
from kb_store.models import GraphEdge, GraphNode, TextChunk
from kb_store.paths import resolve_data_dir
from kb_store.vector_store import FaissVectorStore


class KnowledgeBase:
    """
    Read/write the on-disk knowledge base (vectors + graph).

    Both kb-builder (write) and ai-assistant (read) use the same files under DATA_DIR.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or resolve_data_dir()
        self.vectors = FaissVectorStore(self.data_dir)
        self.graph = NetworkXGraphStore(self.data_dir)

    def load(self) -> None:
        self.vectors.load()
        self.graph.load()

    def save(self) -> None:
        self.vectors.save()
        self.graph.save()

    def upsert_page(
        self,
        page_id: str,
        chunks: list[TextChunk],
        vectors: list[list[float]],
        graph_nodes: list[GraphNode],
        graph_edges: list[GraphEdge],
        embedding_model: str,
    ) -> dict[str, int]:
        """Embed and persist one page; replaces any prior data for that page_id."""
        self.load()
        chunk_ids = [c.chunk_id for c in chunks]
        section_ids = [c.section_id for c in chunks]
        texts = [c.text for c in chunks]
        orders = [c.order for c in chunks]

        indexed = self.vectors.upsert_chunks(
            page_id=page_id,
            chunk_ids=chunk_ids,
            section_ids=section_ids,
            texts=texts,
            orders=orders,
            vectors=vectors,
            embedding_model=embedding_model,
        )
        self.graph.upsert_page_subgraph(page_id, graph_nodes, graph_edges)
        self.save()
        return {
            "vectors_indexed": indexed,
            "graph_nodes": self.graph.node_count,
            "graph_edges": self.graph.edge_count,
        }


@lru_cache
def get_knowledge_base() -> KnowledgeBase:
    """
    Process-wide knowledge base, loaded once (call from FastAPI lifespan).

    After ingest in the same process the in-memory stores are already updated.
    After ingest from the *other* Compose service, restart ai-assistant so it
    re-reads the volume.
    """
    kb = KnowledgeBase()
    kb.load()
    return kb
