"""LangGraph node: persist ingest artifacts to data/."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.config import settings
from app.pipeline.state import IngestState


def persist_artifacts(state: IngestState) -> dict:
    """
    Node 9 — Write page bundle to DATA_DIR.

    Output layout:
        data/pages/{page_id}.json  — full ingest snapshot (graph + chunks)
    """
    metadata = state["metadata"]
    page_id = metadata.page_id
    out_dir = settings.data_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "ingested_at": datetime.now(UTC).isoformat(),
        "metadata": metadata.model_dump(),
        "content_quality": state.get("content_quality"),
        "main_char_count": state.get("main_char_count"),
        "warnings": state.get("warnings", []),
        "sections": [s.model_dump() for s in state.get("sections", [])],
        "chunks": [c.model_dump() for c in state.get("chunks", [])],
        "graph_nodes": [n.model_dump() for n in state.get("graph_nodes", [])],
        "graph_edges": [e.model_dump() for e in state.get("graph_edges", [])],
        "entities": [e.model_dump() for e in state.get("entities", [])],
        "section_summaries": state.get("section_summaries", {}),
    }

    out_path = out_dir / f"{page_id}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"status": "completed", "output_path": str(out_path)}
