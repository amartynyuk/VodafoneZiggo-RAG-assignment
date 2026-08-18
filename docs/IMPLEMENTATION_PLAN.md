# Implementation Plan — VodafoneZiggo RAG Assistant

Phased build order for the project. Each phase produces something runnable or testable.

**Current state:** Phases 0–7 and 10 are complete. Phase 8 (Docker polish) and Phase 9 (CDK resources) are partial stubs.

## Principles

1. **RAG + LangGraph first** — assignment-critical path must work early.
2. **Storage abstractions early** — swap local ↔ AWS without rewriting services.
3. **Incremental demo** — every phase ends with a verifiable command or curl.
4. **You implement, I guide** — core Python/LangGraph logic is pair-programmed; infra, frontend, and scaffolding can be generated.

---

## Phase 0 — Repository scaffold ✅

**Goal:** Empty monorepo structure, tooling, and docs in place.

### Tasks

- [x] Create folder structure per [ARCHITECTURE.md](./ARCHITECTURE.md)
- [x] Root `package.json` + `turbo.json` (tasks: `infra#synth`, `web#build`, `web#dev`)
- [x] `infra/` — CDK app skeleton (stacks stubbed)
- [x] `apps/web/` — Vite + React shell (chat UI)
- [x] `services/ai-assistant/` — FastAPI skeleton + Dockerfile
- [x] `services/kb-builder/` — FastAPI skeleton + Dockerfile
- [x] `docker-compose.yml` — both services + web, shared `./data` volume
- [x] `.gitignore` — Python, Node, `.env`
- [x] `.env.example` — OpenAI, LangSmith, thresholds, security flags
- [x] Root `README.md` — quick start + doc links

### Verify

```bash
docker compose up --build
curl http://localhost:8000/health   # ai-assistant
curl http://localhost:8001/health   # kb-builder
```

---

## Phase 1 — Storage layer & shared models ✅

**Goal:** Local FAISS + NetworkX implementations both services share.

### Tasks

- [x] Define Pydantic models: `ChunkRecord`, `ScoredChunk`, `CacheHit`, ingest schemas
- [x] `FaissVectorStore` (RAG index — `rag.faiss`, `rag_meta.json`, `rag_vectors.npy`)
- [x] `FaissCacheStore` (separate index — `cache.faiss`, `cache_meta.json`, `cache_vectors.npy`)
- [x] `NetworkXGraphStore` (`graph.json`, node-link JSON)
- [x] `KnowledgeBase` facade in `storage/kb.py`
- [x] Smoke test: `scripts/smoke_storage.py`
- [ ] Formal `Protocol` classes *(deferred — convention-based interface works for now)*

### Verify

```bash
cd services/kb-builder
DATA_DIR=../../data python scripts/smoke_storage.py
```

---

## Phase 2 — KB Builder ingest pipeline ✅

**Goal:** Scrape Ziggo pages, build graph, chunk, embed, persist via LangGraph.

### Tasks

- [x] `scrape/` — `requests` + BeautifulSoup fetch + clean
- [x] `structure/` — parse h1–h4 hierarchy → Page / Section nodes
- [x] `chunk/` — section-aware chunking
- [x] `llm/` — entity extraction + section summarization (OpenAI)
- [x] `pipeline/graph.py` — LangGraph: resolve → fetch → clean → parse → chunk → build_graph → llm_extract → llm_summarize → index_kb → persist
- [x] `POST /ingest` — single page by URL or nav `label`
- [x] `GET /status` — page list + store stats
- [x] Sparse-page fallback for JS-heavy pages
- [x] Doc: `INGEST_PIPELINE.md`
- [ ] `config/pages.yaml` with seed URLs *(superseded by `ziggo-product-label-urls.json`)*

### Verify

```bash
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{"label": "Ziggo GO"}'

curl http://localhost:8001/status
ls -la data/rag.faiss data/graph.json data/pages/
```

### Stretch

- [x] Batch script: `scripts/run_ingest_all.py --ziggo-only`
- [x] Nav extraction: `scripts/extract_product_nav.py`

---

## Phase 3 — LangGraph query workflow (core RAG) ✅

**Goal:** Assignment-critical path — question in, graph-augmented answer out.

### Tasks

- [x] Define `AgentState` TypedDict
- [x] Node: `embed_question`
- [x] Node: `vector_retrieve` (with empty/low-score handling)
- [x] Node: `graph_expand_context`
- [x] Node: `generate_answer` (LLM + system prompt)
- [x] Node: `cannot_answer` + conditional edge from retrieve
- [x] Node: `return_answer`
- [x] `POST /ask` endpoint calling compiled graph
- [x] LangSmith env configuration + trace naming (`ziggo-ask`)
- [x] Doc: `QUERY_WORKFLOW.md`
- [x] Default `RAG_SIMILARITY_THRESHOLD=0.65` (was 0.75 — too strict)

### Verify

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What internet speeds does Ziggo offer?"}'
```

---

## Phase 4 — Q&A cache layer ✅

**Goal:** Separate cache index; short-circuit LLM on cache hit.

### Tasks

- [x] Seed file: `data/qa_cache_seed.json` (10 Q&As, NL + EN)
- [x] Load seed into cache index on startup (if index empty)
- [x] LangGraph node: `cache_lookup` (before security/RAG)
- [x] Conditional edge: hit → `return_cached_answer`, miss → continue
- [x] Node: `maybe_cache_answer` (write on high-confidence RAG responses)
- [x] Response field: `"source": "cache" | "rag" | "none"`

### Verify

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Ziggo GO?"}'
# Expect source=cache
```

---

## Phase 5 — Security gate (BERT) ✅

**Goal:** Block/reroute bad or off-topic questions before RAG.

### Tasks

- [x] `security/classifier.py` — `unitary/toxic-bert` + zero-shot DistilBERT
- [x] LangGraph node: `security_classify` (after cache miss)
- [x] Labels: `allow`, `off_topic`, `toxic`
- [x] Node: `reject_response` with safe customer message
- [x] Response field: `"blocked": true/false`
- [x] `SECURITY_ENABLED` env toggle
- [x] Script: `scripts/smoke_cache_security.py`

### Verify

```bash
DATA_DIR=../../data python scripts/smoke_cache_security.py
```

---

## Phase 6 — Multi-page KB & re-ingest ✅ (partial stretch)

**Goal:** Full knowledge engineering showcase — multiple pages, per-page upsert.

### Tasks

- [x] URL list: `data/ziggo-product-label-urls.json` (31 unique URLs)
- [x] Batch ingest: `scripts/run_ingest_all.py --ziggo-only`
- [x] Ingest report: `data/ingest_report.json` (30 pages, 353 chunks, 1004 nodes)
- [x] Re-ingest semantics: delete-then-insert per `page_id`
- [ ] Cross-page entity linking (`RELATED_TO` edges)
- [ ] Finalize `config/pages.yaml` *(optional — JSON URL list is canonical)*

### Verify

```bash
curl http://localhost:8001/status
# Ask cross-page question referencing multiple products
```

---

## Phase 7 — React web app ✅ (partial stretch)

**Goal:** Simple local chat UI for demo.

### Tasks

- [x] Chat interface (message list + input)
- [x] Call `POST /ask` on ai-assistant
- [x] Display answer + source badge (cache / rag / blocked)
- [x] CORS config on FastAPI services
- [ ] Admin panel button to trigger `POST /ingest` on kb-builder

### Verify

Open `http://localhost:3000`, ask a product question.

---

## Phase 8 — Docker Compose polish ⏳

**Goal:** One-command end-to-end run for reviewers.

### Tasks

- [x] Compose: healthchecks, `depends_on` with condition (web → ai-assistant)
- [x] Shared `DATA_DIR` volume mount
- [ ] Multi-stage Dockerfiles (slim Python images)
- [ ] Optional `profiles: ["ingest"]` for first-time seed
- [ ] Document committed sample data strategy

### Verify

```bash
docker compose up --build
# Fresh clone with committed data/ → ask question → get answer
```

---

## Phase 9 — AWS CDK (`infra/`) ⏳

**Goal:** Illustrative deployment — synth succeeds, diagram matches code.

### Tasks

- [x] CDK app with 4 stub stacks (Network, Data, Api, Ingest)
- [x] `cdk synth` in turbo pipeline
- [ ] `NetworkStack` — VPC, subnets, SGs (real resources)
- [ ] `DataStack` — Aurora Serverless v2 (pgvector), Neptune cluster
- [ ] `ApiStack` — API Gateway, container Lambda for ai-assistant + kb-builder
- [ ] `IngestStack` — Step Functions definition for long-running ingest
- [ ] Wire IAM least-privilege between Lambdas and data stores

### Not in scope

- Actual `cdk deploy` (cost / assignment scope)
- CI/CD pipeline (mention as future work in README)

### Verify

```bash
cd infra && npm install && npx cdk synth
```

---

## Phase 10 — Documentation & diagrams ✅

**Goal:** Reviewer-ready README and architecture artifacts.

### Tasks

- [x] README: quick start, model choices, env vars, assignment map
- [x] Architecture diagram (local) — Mermaid in README + ARCHITECTURE.md
- [x] AWS diagram — Mermaid in ARCHITECTURE §10
- [x] Service docs: `INGEST_PIPELINE.md`, `QUERY_WORKFLOW.md`
- [x] IMPLEMENTATION_PLAN completion status (this file)
- [x] Inline code comments on LangGraph edges and storage layout

### Assignment deliverable map

| Deliverable | Location |
|-------------|----------|
| Python source + comments | `services/ai-assistant/`, `services/kb-builder/` |
| LangGraph workflows | `app/graph/workflow.py` (query), `app/pipeline/graph.py` (ingest) |
| Dockerfile + compose | `services/*/Dockerfile`, `docker-compose.yml` |
| README | `README.md` |
| Architecture diagrams | `ARCHITECTURE.md`, `README.md` |
| AWS representation | `infra/`, ARCHITECTURE §10 |

---

## Suggested build order (summary)

```
Phase 0  Scaffold                    ✅
   ↓
Phase 1  Storage abstractions         ✅
   ↓
Phase 2  KB Builder (LangGraph)       ✅
   ↓
Phase 3  LangGraph RAG                ✅  ← assignment MVP
   ↓
Phase 4  Cache index                  ✅
   ↓
Phase 5  BERT gate                    ✅
   ↓
Phase 6  Multi-page KB                ✅ (RELATED_TO pending)
   ↓
Phase 7  React UI                     ✅ (admin panel pending)
   ↓
Phase 8  Docker polish                ⏳
   ↓
Phase 9  CDK                          ⏳ (stubs only)
   ↓
Phase 10 Docs                         ✅
```

---

## Environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | both | Embeddings + LLM |
| `LANGSMITH_TRACING` | both | Enable LangSmith |
| `LANGSMITH_API_KEY` | both | LangSmith auth |
| `LANGSMITH_PROJECT` | both | LangSmith project name |
| `EMBEDDING_MODEL` | both | Model identifier (default `text-embedding-3-small`) |
| `LLM_MODEL` | ai-assistant | Generation model |
| `CACHE_SIMILARITY_THRESHOLD` | ai-assistant | Cache hit threshold (default `0.92`) |
| `RAG_SIMILARITY_THRESHOLD` | ai-assistant | Min score for chunk relevance (default `0.65`) |
| `CACHE_AUTO_WRITE` | ai-assistant | Write high-confidence RAG answers to cache |
| `CACHE_MIN_WRITE_CONFIDENCE` | ai-assistant | Min confidence for cache write-back |
| `SECURITY_ENABLED` | ai-assistant | BERT gate on/off |
| `SECURITY_TOXIC_THRESHOLD` | ai-assistant | toxic-bert block threshold |
| `SECURITY_OFFTOPIC_THRESHOLD` | ai-assistant | zero-shot off-topic threshold |
| `DATA_DIR` | both | Path to `data/` volume (default `/app/data`) |
| `VITE_API_URL` | web | Browser → ai-assistant URL |

---

## Resolved decisions

| Decision | Choice |
|----------|--------|
| Embedding provider | OpenAI `text-embedding-3-small` |
| LLM | Configurable via `LLM_MODEL` |
| Entity extraction | LLM per chunk (`llm/extract.py`) |
| Cache auto-write | High-confidence only (`CACHE_MIN_WRITE_CONFIDENCE=0.70`) |
| Graph expansion depth | 1-hop (section + entities + NEXT) |
| Ingest orchestration | LangGraph (same as query) |
| Page URL source | `ziggo-product-label-urls.json` from nav extraction |
| RAG threshold | `0.65` (scores ~0.70–0.73 were filtered at `0.75`) |

---

## Next steps (optional enhancements)

1. **Phase 6 stretch** — cross-page `RELATED_TO` entity edges
2. **Phase 7 stretch** — admin ingest panel in web UI
3. **Phase 8** — multi-stage Dockerfiles, ingest compose profile
4. **Phase 9** — flesh out CDK stacks with real resource definitions
5. **Playwright** — full extraction for JS-heavy pricing pages (`/tv-internet`, etc.)
