"""Merge LLM extraction results into the knowledge graph."""

from __future__ import annotations

import re

from app.models.schemas import ExtractedEntity, GraphEdge, GraphNode


def _entity_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:80] or "unknown"


def merge_entities_into_graph(
    graph_nodes: list[GraphNode],
    graph_edges: list[GraphEdge],
    entities: list[ExtractedEntity],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Add Entity nodes and Chunk -[MENTIONS]-> Entity edges.

    Deduplicates entities by normalized name so the same product mentioned
    in multiple chunks maps to one graph node.
    """
    nodes = list(graph_nodes)
    edges = list(graph_edges)
    known_entity_ids: dict[str, str] = {}

    for entity in entities:
        slug = _entity_slug(entity.name)
        entity_node_id = f"entity:{slug}"

        if slug not in known_entity_ids:
            known_entity_ids[slug] = entity_node_id
            nodes.append(
                GraphNode(
                    node_id=entity_node_id,
                    label="Entity",
                    properties={
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "type": entity.entity_type,
                    },
                )
            )
        else:
            entity_node_id = known_entity_ids[slug]

        if entity.source_chunk_id:
            chunk_node_id = f"chunk:{entity.source_chunk_id}"
            key = (chunk_node_id, entity_node_id, "MENTIONS")
            if key not in {(e.source_id, e.target_id, e.rel_type) for e in edges}:
                edges.append(
                    GraphEdge(
                        source_id=chunk_node_id,
                        target_id=entity_node_id,
                        rel_type="MENTIONS",
                    )
                )

    return nodes, edges


def apply_section_enrichments(
    graph_nodes: list[GraphNode],
    section_summaries: dict[str, str],
    section_topics: dict[str, str],
) -> list[GraphNode]:
    """Attach topic + summary properties to Section nodes."""
    updated: list[GraphNode] = []
    for node in graph_nodes:
        if node.label != "Section":
            updated.append(node)
            continue
        section_id = node.properties.get("section_id")
        props = dict(node.properties)
        if section_id and section_id in section_summaries:
            props["summary"] = section_summaries[section_id]
        if section_id and section_id in section_topics:
            props["topic"] = section_topics[section_id]
        updated.append(GraphNode(node_id=node.node_id, label=node.label, properties=props))
    return updated
