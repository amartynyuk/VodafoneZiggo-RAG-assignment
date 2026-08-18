# Implementation Plan — VodafoneZiggo RAG Assistant

Phased build order for the project. Each phase produces something runnable or testable. Estimated total effort: **assignment core ~4h**, **full showcase ~12–16h** depending on depth.

## Principles

1. **RAG + LangGraph first** — assignment-critical path must work early.
2. **Storage abstractions early** — swap local ↔ AWS without rewriting services.
3. **Incremental demo** — every phase ends with a verifiable command or curl.
4. **You implement, I guide** — core Python/LangGraph logic is pair-programmed; infra, frontend, and scaffolding can be generated.

---

## Phase 0 — Repository scaffold

**Goal:** Empty monorepo structure, tooling, and docs in place.

### Tasks

- [ ] Create folder structure per [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ ] Root `package.json` + `turbo.json` (tasks: `infra#synth`, `web#build`, `web#dev`)
- [ ] `infra/` — CDK app skeleton (stacks stubbed, no resources yet)
- [ ] `apps/web/` — Vite + React shell (chat UI placeholder)
- [ ] `services/ai-assistant/` — FastAPI skeleton + Dockerfile
- [ ] `services/kb-builder/` — FastAPI skeleton + Dockerfile
- [ ] `docker-compose.yml` — both services + web, shared `./data` volume
- [ ] `.gitignore` — Python, Node, `.env`, optional `data/*.index`
- [ ] `.env.example` — `OPENAI_API_KEY`, `LANGCHAIN_API_KEY`, etc.
- [ ] Update root `README.md` — pointer to architecture + plan docs

### Verify

```bash
docker compose up --build
curl http://localhost:8000/health   # ai-assistant
curl http://localhost:8001/health   # kb-builder
```

---

## Phase 1 — Storage layer & shared models

**Goal:** Abstract interfaces and local implementations both services share.

### Tasks

- [ ] Define Pydantic models: `ChunkRecord`, `ScoredChunk`, `CacheHit`, `GraphContext`, `PageIngestResult`
- [ ] `VectorStore` protocol + `FaissVectorStore` (RAG index)
- [ ] `CacheStore` protocol + `FaissCacheStore` (separate index file)
- [ ] `GraphStore` protocol + `NetworkXGraphStore`
- [ ] Serialize/load: `data/rag.index`, `data/cache.index`, `data/graph.json`
- [ ] Unit smoke test: upsert → search → expand (can be a simple script)

### Design notes

- Use **same embedding dimension** across RAG and cache stores.
- `page_id` on every chunk for delete-by-page during re-ingest.
- Graph save format: node-link JSON (NetworkX `node_link_data`) for git-friendly diffs.

### Verify

```bash
cd services/kb-builder && python -m scripts.smoke_storage
```

---

## Phase 2 — KB Builder ingest pipeline

**Goal:** Scrape one Ziggo page, build graph, chunk, embed, persist.

### Tasks

- [ ] `scrape.py` — `requests` + BeautifulSoup, extract main content
- [ ] `structure.py` — parse h1–h4 hierarchy → Page / Section nodes
- [ ] `chunk.py` — section-aware chunking (respect heading boundaries, max token size)
- [ ] `entities.py` — extract entities (start simple: known product names + LLM/regex)
- [ ] `embed.py` — batch embed chunks via chosen embedding model
- [ ] `pipeline.py` — orchestrate scrape → graph → chunk → embed → persist
- [ ] `POST /ingest` — single page re-ingest endpoint
- [ ] `GET /status` — per-page last ingest timestamp
- [ ] Configure **5–10 seed URLs** in `config/pages.yaml`

### Verify

```bash
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{"page_url": "https://www.ziggo.nl/internet"}'

# Check data/ artifacts created
ls -la data/
```

### Stretch

- [ ] `POST /ingest/batch` — ingest all configured pages
- [ ] CLI: `python -m app.cli ingest --url ...`

---

## Phase 3 — LangGraph query workflow (core RAG)

**Goal:** Assignment-critical path — question in, graph-augmented answer out.

### Tasks

- [ ] Define `AgentState` TypedDict (question, vectors, chunks, context, answer, metadata)
- [ ] Node: `embed_question`
- [ ] Node: `vector_retrieve` (with empty/low-score handling)
- [ ] Node: `graph_expand_context`
- [ ] Node: `generate_answer` (LLM + system prompt)
- [ ] Node: `return_answer` / `cannot_answer`
- [ ] Wire graph with conditional edges for retrieval failure
- [ ] `POST /ask` endpoint calling compiled graph
- [ ] LangSmith env configuration + trace naming

### System prompt guidelines

- Customer-facing tone (Ziggo brand-friendly, Dutch or English per config)
- Answer only from provided context
- Say clearly when information is not in the knowledge base

### Verify

```bash
# After ingest (Phase 2)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What internet speeds does Ziggo offer?"}'
```

---

## Phase 4 — Q&A cache layer

**Goal:** Separate cache index; short-circuit LLM on cache hit.

### Tasks

- [ ] Seed file: `data/qa_cache_seed.json` (5–10 canonical Q&As)
- [ ] Load seed into cache index on startup (if index empty)
- [ ] LangGraph node: `cache_lookup` (before security/RAG)
- [ ] Conditional edge: hit → `return_cached_answer`, miss → continue
- [ ] Node: `maybe_cache_answer` (write on high-confidence RAG responses)
- [ ] Response field: `"source": "cache" | "rag"`

### Verify

```bash
# Should hit cache without LLM (check LangSmith trace — no generate node)
curl -X POST http://localhost:8000/ask \
  -d '{"question": "What is Ziggo GO?"}'
```

---

## Phase 5 — Security gate (BERT)

**Goal:** Block/reroute bad or off-topic questions before RAG.

### Tasks

- [ ] `security/classifier.py` — load pretrained BERT (toxicity) or zero-shot pipeline
- [ ] LangGraph node: `security_classify` (after cache miss)
- [ ] Labels: `allow`, `off_topic`, `block`
- [ ] Node: `reject_response` with safe customer message
- [ ] Response field: `"blocked": true/false`

### Verify

```bash
curl -X POST http://localhost:8000/ask \
  -d '{"question": "<off-topic or toxic example>"}'
# Expect blocked response, no RAG in LangSmith trace
```

---

## Phase 6 — Multi-page KB & re-ingest

**Goal:** Full knowledge engineering showcase — 5–10 pages, per-page upsert.

### Tasks

- [ ] Finalize `config/pages.yaml` with 5–10 Ziggo URLs
- [ ] Batch ingest script or endpoint
- [ ] Cross-page entity linking (`RELATED_TO` edges)
- [ ] Re-ingest test: ingest page A twice, confirm no duplicate chunks
- [ ] Document page list and graph stats in README

### Suggested pages

| page_id | URL (example) |
|---------|---------------|
| internet | https://www.ziggo.nl/internet |
| tv | https://www.ziggo.nl/tv |
| ziggo-go | https://www.ziggo.nl/ziggo-go |
| ... | (add 2–7 more product/service pages) |

### Verify

```bash
curl http://localhost:8001/status
# Ask cross-page question referencing multiple products
```

---

## Phase 7 — React web app

**Goal:** Simple local chat UI for demo.

### Tasks

- [ ] Chat interface (message list + input)
- [ ] Call `POST /ask` on ai-assistant
- [ ] Display answer + source badge (cache / rag / blocked)
- [ ] Optional: admin panel button to trigger `POST /ingest` on kb-builder
- [ ] CORS config on FastAPI services

*Agent implements frontend per project rules.*

### Verify

Open `http://localhost:3000`, ask a product question, see streamed or full response.

---

## Phase 8 — Docker Compose polish

**Goal:** One-command end-to-end run for reviewers.

### Tasks

- [ ] Multi-stage Dockerfiles (slim Python images)
- [ ] Compose: healthchecks, `depends_on` with condition
- [ ] Startup: ai-assistant loads pre-built `data/` if present
- [ ] Optional init container or kb-builder `profiles: ["ingest"]` for first-time seed
- [ ] Document in README:

```bash
docker compose up --build
# or with fresh ingest:
docker compose --profile ingest up --build
```

### Verify

Fresh clone → `docker compose up` → ask question → get answer (using committed `data/` sample).

---

## Phase 9 — AWS CDK (`infra/`)

**Goal:** Illustrative deployment — synth succeeds, diagram matches code.

### Tasks

- [ ] `NetworkStack` — VPC, subnets, SGs
- [ ] `DataStack` — Aurora Serverless v2 (pgvector), Neptune cluster
- [ ] `ApiStack` — API Gateway, container Lambda for ai-assistant + kb-builder
- [ ] `IngestStack` — Step Functions definition for long-running ingest
- [ ] Wire IAM least-privilege between Lambdas and data stores
- [ ] `cdk synth` in turbo pipeline
- [ ] Output values: API URL, cluster endpoints (for documentation)

### Not in scope

- Actual `cdk deploy` (cost / assignment scope)
- CI/CD pipeline (mention as future work in README)

### Verify

```bash
cd infra && npm install && npx cdk synth
```

---

## Phase 10 — Documentation & diagrams

**Goal:** Reviewer-ready README and architecture artifacts.

### Tasks

- [ ] README: quick start, model choices, LangGraph node table, env vars
- [ ] Architecture diagram (local) — Mermaid in README or linked PNG
- [ ] AWS diagram — Mermaid in README or `docs/aws-architecture.md`
- [ ] Inline code comments on: LangGraph edges, storage swap, error paths
- [ ] Assignment checklist mapping (which deliverable → which file)

### Assignment deliverable map

| Deliverable | Location |
|-------------|----------|
| Python source + comments | `services/*/` |
| LangGraph workflow | `services/ai-assistant/app/graph/` |
| Dockerfile + compose | `services/*/Dockerfile`, `docker-compose.yml` |
| README | `README.md` |
| Architecture diagrams | `ARCHITECTURE.md`, README |
| AWS representation | `infra/`, ARCHITECTURE §10 |

---

## Suggested build order (summary)

```
Phase 0  Scaffold
   ↓
Phase 1  Storage abstractions
   ↓
Phase 2  KB Builder (one page)
   ↓
Phase 3  LangGraph RAG          ← assignment MVP
   ↓
Phase 4  Cache index
   ↓
Phase 5  BERT gate
   ↓
Phase 6  Multi-page KB
   ↓
Phase 7  React UI
   ↓
Phase 8  Docker polish
   ↓
Phase 9  CDK
   ↓
Phase 10 Docs final pass
```

---

## Environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | both | Embeddings + LLM |
| `LANGCHAIN_API_KEY` | ai-assistant | LangSmith |
| `LANGCHAIN_PROJECT` | ai-assistant | LangSmith project name |
| `EMBEDDING_MODEL` | both | Model identifier |
| `LLM_MODEL` | ai-assistant | Generation model |
| `CACHE_SIMILARITY_THRESHOLD` | ai-assistant | Cache hit threshold (e.g. 0.92) |
| `RAG_SIMILARITY_THRESHOLD` | ai-assistant | Min score for chunk relevance |
| `DATA_DIR` | both | Path to `data/` volume (default `/app/data`) |

---

## Open decisions (resolve during build)

| Decision | Options | Default |
|----------|---------|---------|
| Embedding provider | OpenAI vs HuggingFace local | OpenAI `text-embedding-3-small` |
| LLM | `gpt-4o-mini` vs `gpt-4o` | `gpt-4o-mini` (cost) |
| Entity extraction | Regex/known list vs LLM NER | Known list + LLM for stretch |
| Cache auto-write | On every answer vs high-confidence only | High-confidence only |
| Graph expansion depth | 1-hop vs 2-hop | 1-hop (section + entities) |
| Language | Dutch vs English responses | Dutch (Ziggo customers) |

---

## Next step

**Phase 0 — scaffold the repo.** Say when you want to start and we'll do it together: I'll generate the folder skeleton, `docker-compose.yml`, and turbo config; you run the commands and we verify health endpoints.
