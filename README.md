# VodafoneZiggo RAG Assistant

Customer-facing AI assistant for Ziggo product questions, built with RAG, LangGraph, and a graph-structured knowledge base.

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, data flows, AWS target
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) — phased build checklist
- [Technical_Assignment_Assist_Teams.md](./Technical_Assignment_Assist_Teams.md) — original assignment brief

## Quick start

```bash
# 1. Copy env template and add your API keys
cp .env.example .env

# 2. Start all services
docker compose up --build

# 3. Verify health endpoints
curl http://localhost:8000/health   # ai-assistant
curl http://localhost:8001/health   # kb-builder

# 4. Open the chat UI
open http://localhost:3000
```

## Repository structure

```
apps/web/              React chat UI
infra/                 AWS CDK (synth only)
services/ai-assistant/ Query path — FastAPI + LangGraph
services/kb-builder/   Ingest path — scrape → graph → embed
data/                  Shared FAISS + NetworkX artifacts + Ziggo source exports
```

### Ziggo product navigation (JSON)

The kb-builder includes a script that parses a saved Ziggo homepage HTML export and extracts the **Producten** menu: top-level categories (Pakketten, Internet, Televisie, …) and their sub-page labels.

**How it works:** BeautifulSoup loads `data/ziggo.nl.txt`, finds the main-nav droplet with `data-ddm-menu-top="producten"`, walks each category section, and reads link labels from the menu markup. Relative paths are normalized to `https://www.ziggo.nl/...`. It writes two files:

| Output | Contents |
|--------|----------|
| `data/ziggo-product-structure.json` | Hierarchy only — categories and label lists (no URLs) |
| `data/ziggo-product-label-urls.json` | Flat `label → url` dict; duplicate labels keep the first URL seen in nav order |

**Re-create the JSON files** (from repo root):

```bash
cd services/kb-builder
python3 -m venv .venv          # first time only
source .venv/bin/activate
pip install -r requirements.txt

python scripts/extract_product_nav.py
```

Optional flags: `--input`, `--structure-out`, `--labels-out` (defaults point at `data/ziggo.nl.txt` and the two JSON files above).

To refresh the source HTML, save the Ziggo homepage markup to `data/ziggo.nl.txt`, then re-run the script.

## Development (without Docker)

### Node and pnpm

Inssrtuctions from https://nodejs.org/en/download official web page.

```
# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash
# in lieu of restarting the shell
\. "$HOME/.nvm/nvm.sh"
# Download and install Node.js:
nvm install 24
# Verify the Node.js version:
node -v # Should print "v24.19.0".
# Download and install pnpm:
corepack enable pnpm
# Verify pnpm version:
pnpm -v
```


```bash
# Python services
cd services/ai-assistant && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd services/kb-builder && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Web UI
cd apps/web && npm install && npm run dev

# CDK synth
cd infra && npm install && npm run synth
```

## Current status

**Phase 0 complete** — monorepo scaffold with stub endpoints. Next: Phase 1 (storage abstractions).
