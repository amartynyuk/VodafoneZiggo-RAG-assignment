"""
NetworkX graph store for knowledge-graph structure.

Persists as node-link JSON (data/graph.json). Supports per-page upsert
for re-ingest: removes Page/Section/Chunk nodes for a page_id, keeps
shared Entity nodes that may link across pages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from app.models.schemas import GraphEdge, GraphNode


class NetworkXGraphStore:
    def __init__(self, data_dir: Path) -> None:
        self.graph_path = data_dir / "graph.json"
        self.g: nx.DiGraph = nx.DiGraph()

    def load(self) -> None:
        if not self.graph_path.exists():
            self.g = nx.DiGraph()
            return
        payload = json.loads(self.graph_path.read_text(encoding="utf-8"))
        self.g = nx.node_link_graph(payload, edges="links")

    def save(self) -> None:
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        payload = nx.node_link_data(self.g, edges="links")
        self.graph_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def delete_page(self, page_id: str) -> int:
        """Remove page subgraph (Page, Section, Chunk nodes). Entity nodes are kept."""
        to_remove: list[str] = []
        for node_id in self.g.nodes:
            if node_id == f"page:{page_id}":
                to_remove.append(node_id)
            elif node_id.startswith(f"section:{page_id}::"):
                to_remove.append(node_id)
            elif node_id.startswith(f"chunk:{page_id}::"):
                to_remove.append(node_id)
        self.g.remove_nodes_from(to_remove)
        return len(to_remove)

    def upsert_page_subgraph(
        self,
        page_id: str,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> None:
        """Replace the page subgraph with freshly built nodes and edges."""
        self.delete_page(page_id)
        for node in nodes:
            attrs: dict[str, Any] = {"label": node.label, **node.properties}
            self.g.add_node(node.node_id, **attrs)
        for edge in edges:
            if edge.source_id in self.g and edge.target_id in self.g:
                self.g.add_edge(
                    edge.source_id,
                    edge.target_id,
                    rel_type=edge.rel_type,
                )

    def expand_from_chunks(self, chunk_ids: list[str], hops: int = 1) -> dict[str, Any]:
        """
        Graph-augmented context: parent sections, NEXT chunks, MENTIONS entities.

        Returns serializable nodes/edges for the RAG context builder (Phase 3).
        """
        collected_nodes: dict[str, dict] = {}
        collected_edges: list[dict] = []

        for chunk_id in chunk_ids:
            node_id = f"chunk:{chunk_id}"
            if node_id not in self.g:
                continue
            frontier = {node_id}
            visited = set()
            for _ in range(hops + 1):
                next_frontier = set()
                for nid in frontier:
                    if nid in visited:
                        continue
                    visited.add(nid)
                    attrs = dict(self.g.nodes[nid])
                    attrs["node_id"] = nid
                    collected_nodes[nid] = attrs
                    for _, target, data in self.g.out_edges(nid, data=True):
                        collected_edges.append(
                            {"source": nid, "target": target, **data}
                        )
                        next_frontier.add(target)
                    for source, _, data in self.g.in_edges(nid, data=True):
                        collected_edges.append(
                            {"source": source, "target": nid, **data}
                        )
                        next_frontier.add(source)
                frontier = next_frontier

        return {"nodes": list(collected_nodes.values()), "edges": collected_edges}

    @property
    def node_count(self) -> int:
        return self.g.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.g.number_of_edges()
