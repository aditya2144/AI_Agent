"""RAG package for retrieval-augmented generation."""

from app.rag.knowledge_base import KnowledgeBase
from app.rag.product_loader import initialize_knowledge_base, create_product_documents

__all__ = [
    "KnowledgeBase",
    "initialize_knowledge_base",
    "create_product_documents",
]
