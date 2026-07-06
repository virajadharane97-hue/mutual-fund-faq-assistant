"""
Embedder Module (Phase 2.4)

Loads the BGE-Small model and generates normalized embeddings 
for text chunks.
"""

import logging
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from config.settings import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Global singleton to avoid reloading the model unnecessarily
_embedder_instance = None

def get_embedder() -> HuggingFaceBgeEmbeddings:
    """Initialize and return the BGE-Small embedding model singleton."""
    global _embedder_instance
    if _embedder_instance is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedder_instance = HuggingFaceBgeEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}  # Critical for Cosine Similarity
        )
    return _embedder_instance

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Embed text chunks using BGE-Small and return them with embeddings included.
    
    Args:
        chunks (List[Dict]): Chunks generated from `chunker.py` (containing 'text' and 'metadata').
        
    Returns:
        List[Dict]: The same chunks with an added 'embedding' key (list of floats).
    """
    if not chunks:
        logger.warning("No chunks provided to embed_chunks.")
        return []
        
    embedder = get_embedder()
    
    texts = [chunk["text"] for chunk in chunks]
    
    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = embedder.embed_documents(texts)
    
    embedded_chunks = []
    for i, chunk in enumerate(chunks):
        embedded_chunk = {
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "embedding": embeddings[i]
        }
        embedded_chunks.append(embedded_chunk)
        
    return embedded_chunks
