# Mutual Fund FAQ Assistant

## Overview
A strict, facts-only RAG (Retrieval-Augmented Generation) Q&A assistant built for HDFC mutual fund schemes. This application ensures users receive pure factual information directly from Groww, without any risk of hallucinations or unintended financial advice.

## Supported Schemes
Currently, the assistant tracks the following 5 schemes from HDFC Mutual Fund:
1. HDFC Large Cap Fund – Direct Plan Growth
2. HDFC Mid-Cap Fund – Direct Plan Growth
3. HDFC Small Cap Fund – Direct Plan Growth
4. HDFC Gold ETF Fund of Fund – Direct Plan Growth
5. HDFC Silver ETF FoF – Direct Plan Growth

## Architecture & Tech Stack
The assistant uses a standard RAG pipeline highly optimized for factual retrieval:
- **Ingestion Pipeline (`requests` + `BeautifulSoup`)**: Scrapes live HTML from Groww, extracts key structural metrics (NAV, Expense Ratios) and narrative sections.
- **Chunking Strategy**: Key metrics are kept intact. Long narratives are recursively split with the Scheme Name injected into every chunk to ensure context isn't lost.
- **Embedding & Storage (`sentence-transformers` + `ChromaDB`)**: Text is embedded using the highly efficient `BAAI/bge-small-en-v1.5` model (384 dimensions) and stored locally in ChromaDB using strict Cosine Similarity.
- **Guardrails**: Regex-based PII blocking and keyword-based Advisory Intent interception.
- **LLM (`llama-3.3-70b-versatile` via Groq)**: Instructed to be ultra-concise (max 3 sentences) and provide exactly one citation link per response.
- **User Interface (`Streamlit`)**: A clean chat interface featuring persistent disclaimers and proactive client-side API rate-limiting.

## Setup Instructions

### 1. Clone & Environment
```bash
git clone <repository_url>
cd mutual-fund-faq-assistant
python -m venv venv
```

Activate the environment:
- Windows: `.\venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. API Keys
Copy the environment template and insert your Groq API Key:
```bash
cp .env.example .env
```
Open `.env` and add: `GROQ_API_KEY=your_api_key_here`

### 4. Run Ingestion Pipeline
This will fetch the live data, chunk it, embed it, and populate the local ChromaDB database.
```bash
python retrieval/vector_store.py
```
*(Optional)* Verify the embeddings:
```bash
python verify_embeddings.py
```

### 5. Launch the Application
```bash
streamlit run ui/app.py
```

## Known Limitations
- Only the 5 listed HDFC schemes are supported. Out-of-scope queries are automatically rejected.
- Data freshness depends on how frequently the ingestion pipeline (`retrieval/vector_store.py`) is run.
- Conversation memory is restricted to the current session (stateless).
- Strict rate limiting (20 RPM) is enforced in the UI to protect against Groq API constraints.

## Disclaimer
⚠️ **Facts-only. No investment advice.** This tool is for educational and informational purposes only. Always consult a SEBI-registered financial advisor before making investment decisions.
