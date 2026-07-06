"""
Mutual Fund FAQ Assistant — Configuration Settings

Centralized configuration for all system components:
- Data sources (Groww URLs)
- Chunking parameters
- Retrieval thresholds
- LLM model settings (Groq)
- Embedding model settings (BGE)
- Vector store paths
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# API Keys
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ============================================
# Data Sources — Groww URLs (ONLY external sources)
# ============================================
GROWW_URLS = [
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
]

# Scheme name mapping (URL slug → display name)
SCHEME_NAMES = {
    "hdfc-large-cap-fund-direct-growth": "HDFC Large Cap Fund – Direct Plan Growth",
    "hdfc-mid-cap-fund-direct-growth": "HDFC Mid-Cap Fund – Direct Plan Growth",
    "hdfc-small-cap-fund-direct-growth": "HDFC Small Cap Fund – Direct Plan Growth",
    "hdfc-gold-etf-fund-of-fund-direct-plan-growth": "HDFC Gold ETF Fund of Fund – Direct Plan Growth",
    "hdfc-silver-etf-fof-direct-growth": "HDFC Silver ETF FoF – Direct Plan Growth",
}

# Scheme category mapping
SCHEME_CATEGORIES = {
    "hdfc-large-cap-fund-direct-growth": "Large Cap",
    "hdfc-mid-cap-fund-direct-growth": "Mid Cap",
    "hdfc-small-cap-fund-direct-growth": "Small Cap",
    "hdfc-gold-etf-fund-of-fund-direct-plan-growth": "Gold ETF FoF",
    "hdfc-silver-etf-fof-direct-growth": "Silver ETF FoF",
}

# ============================================
# Web Scraping Settings
# ============================================
SCRAPER_TIMEOUT = 30           # seconds
SCRAPER_MAX_RETRIES = 3
SCRAPER_RETRY_BACKOFF = 2      # exponential backoff multiplier
SCRAPER_MAX_HTML_SIZE = 2 * 1024 * 1024  # 2MB cap
SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ============================================
# Text Chunking Parameters
# ============================================
CHUNK_SIZE = 400               # tokens
CHUNK_OVERLAP = 80             # tokens

# ============================================
# Embedding Model (BGE)
# ============================================
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

# ============================================
# Vector Store (ChromaDB)
# ============================================
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
COLLECTION_NAME = "hdfc_mf_facts"

# ============================================
# Retrieval Parameters
# ============================================
TOP_K = 3                      # number of chunks to retrieve
SIMILARITY_THRESHOLD = 0.40    # minimum cosine similarity score

# ============================================
# LLM Parameters (Groq)
# ============================================
GROQ_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.0         # deterministic, factual responses
LLM_MAX_TOKENS = 150          # enforces conciseness (~3 sentences)

# ============================================
# Input Guardrails
# ============================================
MAX_QUERY_LENGTH = 500         # characters

# Advisory intent trigger keywords
ADVISORY_KEYWORDS = [
    "should i",
    "which is better",
    "recommend",
    "suggest",
    "worth investing",
    "good fund",
    "best fund",
    "better fund",
    "invest in",
    "buy",
    "sell",
]

# ============================================
# Response Templates
# ============================================
REFUSAL_MESSAGE = (
    "I can only provide factual information about mutual fund schemes. "
    "For investment guidance, please consult a SEBI-registered financial advisor "
    "or visit https://www.amfiindia.com/investor-corner for investor education resources."
)

PII_WARNING_MESSAGE = (
    "⚠️ I detected personal information (e.g., PAN, Aadhaar, phone, email) in your query. "
    "For your privacy and security, I cannot process queries containing personal data. "
    "Please rephrase your question without including any personal information."
)

OUT_OF_SCOPE_MESSAGE = (
    "I currently have data for the following 5 HDFC mutual fund schemes only:\n"
    "• HDFC Large Cap Fund – Direct Plan Growth\n"
    "• HDFC Mid-Cap Fund – Direct Plan Growth\n"
    "• HDFC Small Cap Fund – Direct Plan Growth\n"
    "• HDFC Gold ETF Fund of Fund – Direct Plan Growth\n"
    "• HDFC Silver ETF FoF – Direct Plan Growth\n\n"
    "Please ask a question about one of these schemes."
)

FALLBACK_MESSAGE = (
    "I don't have this information in my current data. "
    "Please visit the official Groww page for the latest details."
)

SERVICE_UNAVAILABLE_MESSAGE = (
    "Service temporarily unavailable. Please try again shortly."
)

# ============================================
# UI Settings
# ============================================
APP_TITLE = "🏦 Mutual Fund FAQ Assistant"
DISCLAIMER_TEXT = "⚠️ Facts-only. No investment advice."
WELCOME_MESSAGE = (
    "👋 Welcome to the Mutual Fund FAQ Assistant!\n\n"
    "I can help you with factual information about HDFC mutual fund schemes.\n"
    "Try asking me:"
)
EXAMPLE_QUESTIONS = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the minimum SIP amount for HDFC Small Cap Fund?",
    "What is the exit load for HDFC Mid-Cap Fund?",
]

# ============================================
# Rate Limiting
# ============================================
RATE_LIMIT_MAX_QUERIES = 30    # per minute per session

# ============================================
# System Prompt for LLM
# ============================================
SYSTEM_PROMPT = """You are a facts-only mutual fund FAQ assistant. You answer questions
about HDFC mutual fund schemes using ONLY the provided context.

RULES:
1. Answer in a maximum of 3 sentences.
2. Include exactly ONE citation link from the source_url in the context.
3. End every response with: "Last updated from sources: <scraped_at date>"
4. If the context does not contain the answer, say:
   "I don't have this information in my current data. Please visit
   the official Groww page for the latest details."
5. NEVER provide investment advice, opinions, or recommendations.
6. NEVER compare fund performance or calculate returns.
7. For performance-related queries, direct the user to the Groww scheme page.
8. Always respond in English."""
