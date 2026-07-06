"""
Input Guardrails (Phase 3.1)

Validates user queries before they hit the LLM or retrieval pipeline.
Detects PII and classifies advisory/out-of-scope intents.
"""

import re
import logging
from typing import Dict, Any
from config.settings import ADVISORY_KEYWORDS, PII_WARNING_MESSAGE, REFUSAL_MESSAGE

logger = logging.getLogger(__name__)

# PII Regex Patterns
PII_PATTERNS = {
    "PAN": r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
    "Aadhaar": r'\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b',
    "Phone": r'\b(\+91[\s-]?)?[6-9][0-9]{9}\b',
    "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
}

def detect_pii(query: str) -> Dict[str, Any]:
    """
    Scan query for PII (PAN, Aadhaar, Phone, Email).
    
    Returns:
        Dict with "has_pii" (bool), "pii_types" (list), and "message" (str).
    """
    found_types = []
    
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, query, re.IGNORECASE):
            found_types.append(pii_type)
            
    if found_types:
        logger.warning(f"PII Detected in query: {found_types}")
        return {
            "has_pii": True,
            "pii_types": found_types,
            "message": PII_WARNING_MESSAGE
        }
        
    return {"has_pii": False, "pii_types": [], "message": ""}

def classify_intent(query: str) -> Dict[str, Any]:
    """
    Classify query intent using keyword scanning.
    Blocks advisory/investment recommendation queries.
    
    Returns:
        Dict with "intent", "should_refuse", and "refusal_message".
    """
    lower_query = query.lower()
    
    # 1. Keyword check for Advisory queries
    for keyword in ADVISORY_KEYWORDS:
        if keyword in lower_query:
            logger.warning(f"Advisory intent detected via keyword: '{keyword}'")
            return {
                "intent": "ADVISORY",
                "should_refuse": True,
                "refusal_message": REFUSAL_MESSAGE
            }
            
    return {
        "intent": "FACTUAL",
        "should_refuse": False,
        "refusal_message": ""
    }
