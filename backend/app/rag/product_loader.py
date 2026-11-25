"""Load product data into the knowledge base."""

import logging
from typing import List
from langchain_core.documents import Document
from app.rag.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "TechStore Pro 15",
        "model": "TS-PRO-15",
        "price": 1299.99,
        "processor": "Intel Core i7-13700H",
        "ram": "16GB DDR5",
        "storage": "512GB NVMe SSD",
        "display": "15.6\" FHD (1920x1080), 165Hz",
        "gpu": "NVIDIA RTX 4060",
        "battery_life": "8 hours",
        "weight": "2.1 kg",
        "description": "High-performance laptop perfect for gaming and professional work. Features latest Intel processor and RTX graphics for smooth gaming and video editing.",
    },
    {
        "id": 2,
        "name": "TechStore Business 14",
        "model": "TS-BIZ-14",
        "price": 899.99,
        "processor": "Intel Core i5-13420H",
        "ram": "8GB DDR5",
        "storage": "256GB NVMe SSD",
        "display": "14\" FHD (1920x1080), 60Hz",
        "gpu": "Intel Iris Xe Graphics",
        "battery_life": "12 hours",
        "weight": "1.5 kg",
        "description": "Lightweight business laptop ideal for professionals who travel. Excellent battery life and productivity-focused features.",
    },
    {
        "id": 3,
        "name": "TechStore Ultra 17",
        "model": "TS-ULTRA-17",
        "price": 1799.99,
        "processor": "Intel Core i9-13900H",
        "ram": "32GB DDR5",
        "storage": "1TB NVMe SSD",
        "display": "17.3\" 4K (3840x2160), 120Hz",
        "gpu": "NVIDIA RTX 4080",
        "battery_life": "7 hours",
        "weight": "2.8 kg",
        "description": "Ultimate performance machine for content creators. 4K display, latest i9 processor, and RTX 4080 for professional video editing and 3D rendering.",
    },
    {
        "id": 4,
        "name": "TechStore Student 13",
        "model": "TS-STU-13",
        "price": 599.99,
        "processor": "AMD Ryzen 5 5600H",
        "ram": "8GB DDR4",
        "storage": "256GB NVMe SSD",
        "display": "13.3\" FHD (1920x1080), 60Hz",
        "gpu": "AMD Radeon Graphics",
        "battery_life": "10 hours",
        "weight": "1.3 kg",
        "description": "Budget-friendly laptop for students. Portable, reliable, and handles everyday computing tasks with ease.",
    },
    {
        "id": 5,
        "name": "TechStore Creator 16",
        "model": "TS-CRE-16",
        "price": 1599.99,
        "processor": "Intel Core i7-13700H",
        "ram": "32GB DDR5",
        "storage": "1TB NVMe SSD",
        "display": "16\" OLED (3072x1920), 120Hz",
        "gpu": "NVIDIA RTX 4070",
        "battery_life": "9 hours",
        "weight": "2.5 kg",
        "description": "Perfect for creative professionals. OLED display with stunning colors for photo and video editing.",
    },
    {
        "id": 6,
        "name": "TechStore Gaming Beast 15",
        "model": "TS-GAME-15",
        "price": 1499.99,
        "processor": "Intel Core i7-13700K",
        "ram": "16GB DDR5",
        "storage": "512GB NVMe SSD",
        "display": "15.6\" FHD (1920x1080), 240Hz",
        "gpu": "NVIDIA RTX 4070 Ti",
        "battery_life": "5 hours",
        "weight": "2.3 kg",
        "description": "High-end gaming laptop with 240Hz display for competitive gaming. Extreme performance for the latest AAA titles.",
    },
]


def create_product_documents() -> List[Document]:
    """Create Document objects from sample products.
    
    Returns:
        List of Document objects.
    """
    documents = []
    
    for product in SAMPLE_PRODUCTS:
        content = f"""
Product: {product['name']} ({product['model']})
Price: ${product['price']:.2f}
Processor: {product['processor']}
RAM: {product['ram']}
Storage: {product['storage']}
Display: {product['display']}
GPU: {product['gpu']}
Battery Life: {product['battery_life']}
Weight: {product['weight']}
Description: {product['description']}
        """.strip()
        
        doc = Document(
            page_content=content,
            metadata={
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "model": product["model"],
            }
        )
        documents.append(doc)
    
    return documents


def initialize_knowledge_base(persist_directory: str = "./data/chromadb") -> KnowledgeBase:
    """Initialize and populate the knowledge base.
    
    Args:
        persist_directory: Path to persist ChromaDB data.
        
    Returns:
        Initialized KnowledgeBase instance.
    """
    try:
        kb = KnowledgeBase(persist_directory=persist_directory)
        
        # Create and add product documents
        documents = create_product_documents()
        kb.add_documents(documents)
        
        logger.info(f"Knowledge base initialized with {len(documents)} products")
        return kb
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}")
        raise
