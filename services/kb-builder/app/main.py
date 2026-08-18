"""
FastAPI application entrypoint for the KB Builder service.

On startup we load the shared FAISS + NetworkX stores and warm the embedder
so POST /ingest does not pay that cost on the first request.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from kb_store.embeddings import get_embedder
from kb_store.kb import get_knowledge_base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load vector + graph stores once for the process lifetime."""
    get_embedder()
    get_knowledge_base()
    yield


app = FastAPI(
    title="Ziggo KB Builder",
    description="Knowledge base ingestion pipeline for Ziggo RAG assistant",
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

app.include_router(router)
