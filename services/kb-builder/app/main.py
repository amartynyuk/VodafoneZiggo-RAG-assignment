"""
FastAPI application entrypoint for the KB Builder service.

This service scrapes Ziggo pages, builds the knowledge graph, chunks content,
and persists vectors + graph to the shared data/ volume.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Ziggo KB Builder",
    description="Knowledge base ingestion pipeline for Ziggo RAG assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
