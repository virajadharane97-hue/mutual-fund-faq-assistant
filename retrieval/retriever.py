"""
Retrieval Pipeline (Phase 3.2)

Handles the embedding of user queries and fetching of top-K 
relevant chunks from the Vector Store using Cosine Similarity.
"""

import logging
from typing import List, Dict, Any
from retrieval.vector_store import VectorStore
from ingestion.embedder import get_embedder
from config.settings import TOP_K, SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

def retrieve_context(query: str, vector_store: VectorStore) -> List[Dict[str, Any]]:
    """
    Embed the query, search ChromaDB, and apply threshold filtering.
    
    Args:
        query (str): The sanitized user query.
        vector_store (VectorStore): Initialized vector store instance.
        
    Returns:
        List[Dict]: List of valid chunks that pass the similarity threshold.
    """
    embedder = get_embedder()
    
    logger.info(f"Embedding query: '{query}'")
    query_embedding = embedder.embed_query(query)
    
    # Query ChromaDB
    # Chroma returns cosine distance (1 - cosine_similarity).
    # Since normalized embeddings are used, cosine_similarity = 1 - distance.
    raw_results = vector_store.query(query_embedding, top_k=TOP_K)
    
    if not raw_results:
        logger.info("No results returned from vector store.")
        return []
        
    valid_chunks = []
    
    for res in raw_results:
        # Calculate similarity score
        # Note: Depending on Chroma version and space setting, distance might already
        # be cosine distance. For 'cosine' space, similarity = 1 - distance
        distance = res.get("distance", 1.0)
        similarity = 1.0 - distance
        
        logger.debug(f"Chunk ID: {res.get('id')}, Distance: {distance:.4f}, Similarity: {similarity:.4f}")
        
        if similarity >= SIMILARITY_THRESHOLD:
            # We append the similarity score for downstream use if needed
            res["similarity_score"] = similarity
            valid_chunks.append(res)
            
    logger.info(f"Retrieved {len(valid_chunks)} chunks above threshold {SIMILARITY_THRESHOLD}")
    return valid_chunks

def format_context_block(chunks: List[Dict[str, Any]]) -> str:
    """
    Compile retrieved text into a single context string block.
    """
    if not chunks:
        return ""
        
    context_parts = []
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        source_url = chunk["metadata"].get("source_url", "Unknown Source")
        scraped_at = chunk["metadata"].get("scraped_at", "Unknown Date")
        
        # Inject metadata into the context block for LLM citation parsing
        context_parts.append(f"[Document {i+1}]\nSource: {source_url}\nDate: {scraped_at}\nContent:\n{text}")
        
    return "\n\n".join(context_parts)
