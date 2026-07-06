"""
Response Generator (Phase 3.3 / 3.4)

Orchestrates the entire query pipeline: 
1. Guardrail checks (PII, Intent)
2. Retrieval and Threshold filtering
3. Formatting Prompt
4. LLM Generation via Groq
"""

import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import (
    GROQ_API_KEY, 
    GROQ_MODEL, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS,
    SYSTEM_PROMPT,
    FALLBACK_MESSAGE
)

from retrieval.guardrails import detect_pii, classify_intent
from retrieval.retriever import retrieve_context, format_context_block
from retrieval.vector_store import VectorStore
from generation.prompt_templates import build_context_prompt

logger = logging.getLogger(__name__)

# Global singleton
_llm_instance = None

def get_llm():
    """Initialize Groq client."""
    global _llm_instance
    if _llm_instance is None:
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY is missing from environment/settings.")
            raise ValueError("GROQ_API_KEY is not set.")
            
        logger.info(f"Initializing Groq client with model: {GROQ_MODEL}")
        _llm_instance = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS
        )
    return _llm_instance

def generate_response(query: str, vector_store: VectorStore) -> str:
    """
    End-to-End Orchestrator for processing a user query.
    
    Args:
        query (str): The user's input question.
        vector_store (VectorStore): The initialized vector store.
        
    Returns:
        str: The final LLM response or a hardcoded fallback/guardrail message.
    """
    logger.info(f"Processing query: '{query}'")
    
    # 1. PII Check
    pii_result = detect_pii(query)
    if pii_result["has_pii"]:
        return pii_result["message"]
        
    # 2. Advisory Intent Check
    intent_result = classify_intent(query)
    if intent_result["should_refuse"]:
        return intent_result["refusal_message"]
        
    # 3. Retrieve Context
    valid_chunks = retrieve_context(query, vector_store)
    
    if not valid_chunks:
        logger.info("No relevant context found. Returning fallback message.")
        return FALLBACK_MESSAGE
        
    # 4. Generate Prompt
    context_block = format_context_block(valid_chunks)
    user_prompt = build_context_prompt(context_block, query)
    
    # 5. Call LLM
    logger.info("Sending prompt to Groq LLM...")
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        return response.content
        
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error generating response from LLM: {str(e)}")
        if "rate limit" in error_msg or "429" in error_msg or "too many requests" in error_msg:
            return "⏳ Rate limit exceeded. Groq's API is currently maxed out (30 requests/min or 12k tokens/min). Please wait 60 seconds and try again."
        return "I encountered an error connecting to my language model. Please try again later."
