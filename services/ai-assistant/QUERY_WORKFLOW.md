# AI Assistant — Query Workflow

LangGraph RAG pipeline with Q&A cache and BERT security gate.

## Flow

```
embed_question
    → cache_lookup ──hit──→ return_cached_answer → END
    │ miss
    → security_classify ──block──→ reject_response → return_answer → END
    │ allow
    → vector_retrieve → [graph_expand | cannot_answer]
    → generate_answer → maybe_cache_answer → return_answer → END
```

| Node | Type | What it does |
|------|------|--------------|
| `embed_question` | deterministic | Embed question (shared by cache + RAG) |
| `cache_lookup` | deterministic | Search separate FAISS Q&A index |
| `security_classify` | **BERT** | toxic-bert + zero-shot topic check |
| `vector_retrieve` | deterministic | RAG chunk search |
| `graph_expand_context` | deterministic | NetworkX context expansion |
| `generate_answer` | **LLM** | Grounded answer generation |
| `maybe_cache_answer` | deterministic | Write high-confidence RAG answers to cache |
| `reject_response` | deterministic | Safe refusal (blocked=true) |

## Run locally

```bash
cd services/ai-assistant
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

DATA_DIR=../../data .venv/bin/python scripts/smoke_cache_security.py
```

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `CACHE_SIMILARITY_THRESHOLD` | 0.92 | Min score for cache hit |
| `CACHE_AUTO_WRITE` | true | Store successful RAG answers |
| `CACHE_MIN_WRITE_CONFIDENCE` | 0.70 | Min RAG score to auto-cache |
| `SECURITY_ENABLED` | true | Enable BERT gate |
| `SECURITY_TOXIC_THRESHOLD` | 0.5 | toxic-bert block threshold |
| `SECURITY_OFFTOPIC_THRESHOLD` | 0.75 | Zero-shot off-topic threshold |
| `RAG_SIMILARITY_THRESHOLD` | 0.65 | Min chunk relevance score |

## Cache seed data

`data/qa_cache_seed.json` — loaded at startup (lifespan) when the cache index is empty.

## Models (loaded at app startup)

- OpenAI `text-embedding-3-small` (1536-d) — question + chunk embeddings
- `unitary/toxic-bert` — toxicity detection
- `typeform/distilbert-base-uncased-mnli` — zero-shot topic classification

FAISS indexes, the knowledge graph, and BERT pipelines are initialized in the FastAPI **lifespan** so the first `/ask` is not a cold start. Docker bakes the Hugging Face weights into the image (`scripts/download_hf_models.py`).
