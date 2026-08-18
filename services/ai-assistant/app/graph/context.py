"""Build LLM context string from vector hits + graph expansion."""

from __future__ import annotations

from app.storage.models import ScoredChunk


def build_context_text(
    chunks: list[ScoredChunk],
    graph_expansion: dict,
) -> str:
    """
    Merge retrieved chunks with graph-expanded section/entity context.

    Primary content comes from vector hits; graph adds section headings,
    summaries, and related entity names for graph-augmented RAG.
    """
    parts: list[str] = ["## Retrieved content"]

    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"### Passage {i} (relevance: {chunk.score:.2f})\n{chunk.text}"
        )

    nodes = graph_expansion.get("nodes", [])
    sections = [n for n in nodes if n.get("label") == "Section"]
    if sections:
        parts.append("\n## Related sections")
        for section in sections:
            heading = section.get("heading", "")
            summary = section.get("summary", "")
            if heading:
                line = f"- **{heading}**"
                if summary:
                    line += f": {summary}"
                parts.append(line)

    entities = [n for n in nodes if n.get("label") == "Entity"]
    if entities:
        names = sorted({n.get("name", "") for n in entities if n.get("name")})
        if names:
            parts.append("\n## Related products and features")
            parts.append(", ".join(names))

    # Include adjacent chunk text from graph (NEXT edges) not already in hits
    hit_ids = {c.chunk_id for c in chunks}
    extra_chunks: list[str] = []
    for node in nodes:
        if node.get("label") != "Chunk":
            continue
        chunk_id = node.get("chunk_id") or node.get("node_id", "").removeprefix("chunk:")
        text = node.get("text", "")
        if chunk_id and chunk_id not in hit_ids and text:
            extra_chunks.append(text)
    if extra_chunks:
        parts.append("\n## Additional context from linked passages")
        for text in extra_chunks[:3]:
            parts.append(text)

    return "\n\n".join(parts)
