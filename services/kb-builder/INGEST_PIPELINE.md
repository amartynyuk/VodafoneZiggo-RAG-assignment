# KB Builder — Ingest Pipeline

LangGraph workflow for scraping Ziggo pages and building the knowledge graph.

## Pipeline (deterministic → LLM)

```
resolve → fetch → clean → parse_sections → chunk → build_graph
    → llm_extract (stub) → llm_summarize (stub) → persist
```

| Node | Type | What it does |
|------|------|--------------|
| `resolve` | deterministic | Map nav label → URL via `data/ziggo-product-label-urls.json` |
| `fetch` | deterministic | `requests` GET |
| `clean` | deterministic | Strip nav/footer; extract `<head>` metadata; flag `rich` vs `sparse` |
| `parse_sections` | deterministic | h1–h4 sections, or overview fallback for sparse pages |
| `chunk` | deterministic | Section-aware chunking |
| `build_graph` | deterministic | Page → Section → Chunk + NEXT edges |
| `llm_extract` | **LLM** | Entity extraction per chunk → Entity + MENTIONS edges |
| `llm_summarize` | **LLM** | Section topic + summary on Section nodes |
| `persist` | deterministic | Write `data/pages/{page_id}.json` |

## Page patterns (from live fetch)

| Page | Static HTML | Strategy |
|------|-------------|----------|
| `/televisie/ziggo-go` | Rich (~13k chars in `<main>`) | Full heading parse |
| `/tv-internet` | Sparse (~588 chars) | Overview from og/meta only |

## Run locally

```bash
cd services/kb-builder
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

DATA_DIR=../../data .venv/bin/python scripts/run_ingest_sample.py
DATA_DIR=../../data .venv/bin/python scripts/run_ingest_sample.py --label "Ziggo GO"
```

## API

```bash
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{"label": "Ziggo GO"}'
```
