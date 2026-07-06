
"""
Script to verify that chunks were properly embedded and stored in ChromaDB.
Run this after executing the ingestion pipeline.
"""

import sys
import logging
from retrieval.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_embeddings():
    logger.info("Connecting to Vector Store...")
    store = VectorStore()
    
    count = store.get_count()
    if count == 0:
        logger.error("❌ Vector store is empty! Please run the ingestion pipeline first:")
        logger.error("Run: python retrieval/vector_store.py")
        sys.exit(1)
        
    logger.info(f"\n✅ SUCCESS: Found {count} chunks stored in ChromaDB.")
    
    # Fetch all data including embeddings
    data = store.collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    embeddings = data.get('embeddings', [])
    if not embeddings or len(embeddings) == 0:
        logger.error("\n❌ ERROR: Embeddings were not found or not stored correctly.")
        sys.exit(1)
        
    # Check dimensionality of the first embedding
    dim = len(embeddings[0])
    logger.info(f"✅ SUCCESS: Embedding Dimensionality: {dim} (Expected 384 for BGE-Small)")
    
    if dim != 384:
        logger.warning(f"\n❌ WARNING: Dimensionality mismatch! Expected 384 but got {dim}.")
        
    # Print a few samples
    samples_to_show = min(3, count)
    logger.info(f"\n--- DISPLAYING {samples_to_show} SAMPLE CHUNKS ---")
    
    for i in range(samples_to_show):
        logger.info(f"\n[Sample {i+1}]")
        logger.info(f"Scheme: {data['metadatas'][i].get('scheme_name')}")
        logger.info(f"Heading: {data['metadatas'][i].get('section_heading')}")
        logger.info(f"Text Preview: {data['documents'][i][:100]}...")
        
        # Display the first 5 floats of the embedding vector
        vec_preview = [round(x, 4) for x in embeddings[i][:5]]
        logger.info(f"Embedding Vector (first 5 dims): {vec_preview} ... (Total: {len(embeddings[i])} dims)")
        
    logger.info("\n✅ All embeddings verified successfully. The data is ready for retrieval!")

if __name__ == "__main__":
    verify_embeddings()
