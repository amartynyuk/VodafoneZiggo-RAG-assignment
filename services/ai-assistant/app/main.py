"""
FastAPI application for the AI Assistant.

On startup we load FAISS + the knowledge graph, warm the OpenAI embedder,
seed the Q&A cache if empty, and load BERT security models from HF_HOME.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.cache import get_cache_store
from app.config import settings
from app.graph import AskRequest, AskResponse, run_query
from app.security import warmup_security_models
from kb_store.embeddings import get_embedder
from kb_store.kb import get_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load stores and models once so the first /ask is not a cold start."""
    get_embedder()
    get_knowledge_base()
    get_cache_store()
    if settings.security_enabled:
        warmup_security_models()
    yield


app = FastAPI(
    title="Ziggo AI Assistant",
    description="Customer-facing RAG assistant with LangGraph orchestration",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and load balancers."""
    return {"status": "ok", "service": "ai-assistant"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    """
    Accept a customer question and return a graph-augmented RAG answer.

    Workflow: embed → cache → security → retrieve → expand → generate (LangGraph).
    """
    try:
        return run_query(request.question)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not indexed yet. Run kb-builder ingest first.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
