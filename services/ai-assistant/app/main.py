"""
FastAPI application entrypoint for the AI Assistant service.

This service handles customer questions via POST /ask. The LangGraph workflow
(cache → security → graph-augmented RAG) will be wired in Phase 3+.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="Ziggo AI Assistant",
    description="Customer-facing RAG assistant with LangGraph orchestration",
    version="0.1.0",
)

# Allow the React dev server and Docker web container to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
