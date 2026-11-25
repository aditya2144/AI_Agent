"""RAG knowledge base for product information."""

import os
import logging
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Knowledge base using ChromaDB for RAG."""
    
    def __init__(self, persist_directory: str = "./data/chromadb"):
        """Initialize knowledge base.
        
        Args:
            persist_directory: Path to persist ChromaDB data.
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize or load vector store
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="techstore_products"
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the knowledge base.
        
        Args:
            documents: List of Document objects to add.
        """
        try:
            self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to knowledge base")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(self, query: str, k: int = 3) -> List[tuple]:
        """Search for relevant documents.
        
        Args:
            query: Search query.
            k: Number of results to return.
            
        Returns:
            List of (Document, score) tuples.
        """
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def get_context(self, query: str, k: int = 3) -> str:
        """Get context for a query.
        
        Args:
            query: Search query.
            k: Number of results to return.
            
        Returns:
            Formatted context string.
        """
        results = self.search(query, k=k)
        
        if not results:
            return "No relevant products found."
        
        context = "Product Information:\n\n"
        for i, (doc, score) in enumerate(results, 1):
            context += f"{i}. {doc.page_content}\n"
            context += f"   (Relevance: {score:.2f})\n\n"
        
        return context
    
    def clear(self) -> None:
        """Clear the knowledge base."""
        try:
            # Delete all collections and reinitialize
            self.vector_store.delete_collection()
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="techstore_products"
            )
            logger.info("Knowledge base cleared")
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {e}")
