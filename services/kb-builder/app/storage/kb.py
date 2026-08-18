"""Facade over FAISS + NetworkX stores in the shared data/ directory."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.models.schemas import GraphEdge, GraphNode, TextChunk
from app.storage.graph_store import NetworkXGraphStore
from app.storage.vector_store import FaissVectorStore


class KnowledgeBase:
    """
    Read/write the on-disk knowledge base (vectors + graph).

    Both kb-builder (write) and ai-assistant (read) use the same files under DATA_DIR.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or settings.data_dir
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


def get_knowledge_base() -> KnowledgeBase:
    """Return a loaded knowledge base from configured DATA_DIR."""
    kb = KnowledgeBase()
    kb.load()
    return kb
