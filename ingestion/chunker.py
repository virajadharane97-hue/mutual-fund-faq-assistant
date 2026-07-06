"""
Text Chunker (Phase 2.3)

Splits parsed sections into smaller, semantically meaningful chunks 
with context injection for embedding.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

def chunk_scheme_data(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunk parsed scheme data into embeddable pieces with metadata.
    
    Args:
        parsed_data (Dict): The parsed output from `parser.py` containing 'sections'.
        
    Returns:
        List[Dict]: List of chunks, where each chunk has 'text' and 'metadata'.
    """
    if not parsed_data or "sections" not in parsed_data:
        logger.warning("Empty or invalid parsed_data provided to chunker.")
        return []
        
    scheme_name = parsed_data.get("scheme_name", "Unknown Scheme")
    source_url = parsed_data.get("source_url", "")
    scraped_at = parsed_data.get("scraped_at", datetime.now(timezone.utc).isoformat())
    sections = parsed_data.get("sections", [])
    
    # Langchain's text splitter uses character length. 
    # Since CHUNK_SIZE in settings is meant for tokens, we approximate 1 token ≈ 4 characters.
    char_chunk_size = CHUNK_SIZE * 4
    char_overlap = CHUNK_OVERLAP * 4
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_chunk_size,
        chunk_overlap=char_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = []
    
    for section in sections:
        heading = section.get("heading", "General")
        content = section.get("content", "").strip()
        
        if not content:
            continue
            
        # Context Injection: prepend the scheme and section to every single chunk
        context_prefix = f"{scheme_name} - {heading}: "
        
        # Key Metrics Strategy: Keep intact (do not split)
        if heading == "Key Metrics":
            chunk_text = context_prefix + content
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source_url": source_url,
                    "scheme_name": scheme_name,
                    "section_heading": heading,
                    "scraped_at": scraped_at
                }
            })
        else:
            # General Text Strategy: Split using LangChain
            raw_chunks = text_splitter.split_text(content)
            
            for raw_chunk in raw_chunks:
                chunk_text = context_prefix + raw_chunk.strip()
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source_url": source_url,
                        "scheme_name": scheme_name,
                        "section_heading": heading,
                        "scraped_at": scraped_at
                    }
                })
                
    return chunks

if __name__ == "__main__":
    import json
    import os
    
    logging.basicConfig(level=logging.INFO)
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    input_file = os.path.join(data_dir, "parsed_outputs.json")
    output_file = os.path.join(data_dir, "chunked_outputs.json")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}. Run parser.py first.")
    else:
        with open(input_file, "r", encoding="utf-8") as f:
            all_parsed_data = json.load(f)
            
        all_chunks = []
        for parsed_item in all_parsed_data:
            chunks = chunk_scheme_data(parsed_item)
            all_chunks.extend(chunks)
            logger.info(f"Generated {len(chunks)} chunks for {parsed_item.get('scheme_name')}")
            
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Total chunks created: {len(all_chunks)}")
        logger.info(f"Saved chunked data to {output_file}")
