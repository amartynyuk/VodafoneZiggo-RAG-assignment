# AI Assistant — Query Workflow (Phase 3)

LangGraph RAG pipeline for customer questions.

## Flow

```
embed_question → vector_retrieve → [graph_expand_context | cannot_answer]
    → generate_answer → return_answer
```

| Node | Input | Output |
|------|-------|--------|
| `embed_question` | question | question_vector |
| `vector_retrieve` | question_vector | retrieved_chunks (score ≥ threshold) |
| `graph_expand_context` | chunks | context_text (+ sections, entities from graph) |
| `generate_answer` | question + context | answer (Dutch by default) |
| `cannot_answer` | — | polite fallback when no chunks match |

## Run locally

```bash
cd services/ai-assistant
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Requires indexed KB (kb-builder ingest first)
DATA_DIR=../../data .venv/bin/python scripts/smoke_ask.py

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hoeveel apparaten kan ik gebruiken met Ziggo GO?"}'
```

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `RAG_SIMILARITY_THRESHOLD` | 0.65 | Min cosine score for chunk retrieval |
| `RAG_TOP_K` | 5 | Max chunks retrieved |
| `LLM_MODEL` | gpt-4o-mini | Answer generation |
| `RESPONSE_LANGUAGE` | nl | `nl` or `en` |
| `LANGSMITH_TRACING` | — | Set `true` for LangSmith traces |

## LangSmith

Each `/ask` run is named `ziggo-ask` in LangSmith when tracing is enabled.
