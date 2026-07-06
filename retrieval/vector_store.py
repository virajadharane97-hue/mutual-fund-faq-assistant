"""
Vector Store Wrapper (Phase 2.5)

Manages the ChromaDB instance, persists embeddings, and provides 
methods for semantic querying.
"""

import logging
import uuid
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import os
import sys

# Ensure config imports work whether run standalone or as a module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import CHROMA_PERSIST_DIR, COLLECTION_NAME

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR, collection_name: str = COLLECTION_NAME):
        """Initialize ChromaDB client and collection."""
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize PersistentClient
        self.client = chromadb.PersistentClient(
            path=self.persist_dir, 
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection with Cosine Similarity
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaDB at {self.persist_dir} with collection '{self.collection_name}'")

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add text chunks, metadata, and their embeddings to the vector store."""
        if not texts:
            logger.warning("No documents provided to add_documents.")
            return
            
        # Generate unique IDs
        ids = [str(uuid.uuid4()) for _ in texts]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} documents to vector store.")

    def query(self, query_embedding: List[float], top_k: int = 3, filters: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for the most similar chunks.
        
        Returns:
            List[Dict]: A list of results formatted as:
            [{"text": str, "metadata": dict, "distance": float, "id": str}, ...]
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters
        )
        
        formatted_results = []
        if results and 'documents' in results and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "id": results['ids'][0][i]
                })
                
        return formatted_results

    def reset_collection(self):
        """Delete and recreate the collection. Useful for full re-ingestion."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{self.collection_name}' reset successfully.")
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")

    def get_count(self) -> int:
        """Get total number of documents in the collection."""
        return self.collection.count()


def run_ingestion_pipeline():
    """
    End-to-End ingestion: Scrape -> Parse -> Chunk -> Embed -> Store.
    Executes all Phase 2 steps sequentially.
    """
    from ingestion.scraper import scrape_all_urls
    from ingestion.parser import parse_scheme_page
    from ingestion.chunker import chunk_scheme_data
    from ingestion.embedder import embed_chunks
    
    logger.info("=== Starting E2E Data Ingestion Pipeline ===")
    
    # 1. Fetch
    raw_results = scrape_all_urls()
    
    # 2. Parse & 3. Chunk
    all_chunks = []
    for raw in raw_results:
        if raw["status"] == 200 and raw["html"]:
            parsed = parse_scheme_page(raw["html"], raw["url"])
            chunks = chunk_scheme_data(parsed)
            all_chunks.extend(chunks)
            
    if not all_chunks:
        logger.error("No chunks generated. Aborting ingestion.")
        return
        
    logger.info(f"Generated {len(all_chunks)} chunks total.")
    
    # 4. Embed
    embedded_chunks = embed_chunks(all_chunks)
    
    texts = [c["text"] for c in embedded_chunks]
    metadatas = [c["metadata"] for c in embedded_chunks]
    embeddings = [c["embedding"] for c in embedded_chunks]
    
    # 5. Store
    store = VectorStore()
    store.reset_collection() # Start fresh on every run for stateless consistency
    store.add_documents(texts, metadatas, embeddings)
    
    logger.info(f"=== Ingestion complete. Vector store now has {store.get_count()} chunks. ===")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion_pipeline()
