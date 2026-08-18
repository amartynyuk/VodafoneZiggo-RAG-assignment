"""FAISS vector store + NetworkX graph (read/write via shared data/)."""

from app.storage.kb import KnowledgeBase, get_knowledge_base

__all__ = ["KnowledgeBase", "get_knowledge_base"]
