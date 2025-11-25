# Telecom Architecture Advisor (RAG + Streamlit)

AI-powered telecom architecture advisor using Retrieval-Augmented Generation (RAG), hybrid search, and a Streamlit web UI. It integrates with Google Gemini for high-quality responses grounded in a telecom knowledge base.

## 🎯 Overview

This app helps telecom architects and engineers make informed design decisions. It combines:

- Google Gemini 2.5 Flash (LLM via REST API)
- ChromaDB vector store with Sentence-Transformers embeddings
- Hybrid retrieval (semantic + BM25 keyword)
- Citations with normalized relevance scoring
- Streamlit web interface + optional CLI

## 🏗️ Architecture

```
User → [Hybrid Search] → Context + History → Prompt → Gemini → Answer
           ├─ ChromaDB (vectors)
           └─ BM25 (keywords)
```

## 🚀 Quick Start

### Prerequisites

- macOS/Linux/Windows with Python 3.9+
- A Google Gemini API key

### Get a Gemini API key (first time)

1) Open Google AI Studio: https://aistudio.google.com/
2) Sign in with your Google account.
3) Go to "Get API key" (or visit https://ai.google.dev/gemini-api/docs/api-key) and click "Create API key".
4) Select a project (or accept the default) and create the key.
5) Copy the key and keep it secret. You’ll set it as `GEMINI_API_KEY` below.

Notes:
- Some regions may have restrictions; check availability in the official docs.
- Free tiers and quotas apply; see Google’s usage and pricing guidance.

### Setup

```bash
# 1) Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure your API key
cp .env.example .env
# edit .env and set GEMINI_API_KEY=...

# 4) Start the web app
streamlit run streamlit_app.py

# Alternative: run the enhanced script (launches Streamlit and has CLI fallback)
python telecom_advisor_enhanced.py
```

If you prefer one command setup, see SETUP_SECURITY.md or run `./setup_secure.sh`.

## � What you can do

- Chat with the advisor about telecom architecture
- See citations with normalized relevance scores and text previews
- Upload PDFs to expand the knowledge base (UI or CLI)
- Compare architectures (e.g., Microservices vs Monolith)
- View analytics (topics and recent queries)
- Export conversations (Markdown or PDF)

## 📂 Key Files

- `telecom_advisor_enhanced.py` — Core RAG logic, Gemini integration, CLI, helpers
- `streamlit_app.py` — Web UI (Chat, Compare, Upload, Analytics, Export)
- `AA_LLM.py` — Minimal Gemini example
- `telecom_advisor_rag.py` — Original/simple RAG demo
- `requirements.txt` — Python dependencies
- `analytics.json` — Query analytics (auto-created)
- `chroma_db/` — Vector store (auto-created, gitignored)

## ⚙️ Configuration

Environment variables (via `.env`):

- `GEMINI_API_KEY` — your Google Gemini API key (required)

Logs and data:

- `telecom_advisor.log` — app logs (rotating)
- `analytics.json` — stores query history and topic stats

## 📚 Knowledge Base

- Preloaded with telecom topics: microservices, monolith, TMF standards, HA, cloud-native, 5G, NFV/SDN, edge, IoT billing, event-driven
- Upload additional PDFs from the UI (Upload tab) or via CLI
- Programmatic add example:

```python
from telecom_advisor_enhanced import add_knowledge_to_db
docs = ["Your custom telecom knowledge..."]
meta = [{"topic": "5g", "domain": "network"}]
add_knowledge_to_db(docs, meta)
```

## 🔎 Retrieval & Citations

- Hybrid search combines semantic similarity (ChromaDB) and keyword BM25
- Citations display topic, domain, a text preview, and relevance (normalized score)

## � Security

Never commit secrets. Use `.env` and see `SETUP_SECURITY.md` and `SECURITY.md` for best practices.

## 🧪 Troubleshooting

- Missing API key: ensure `.env` has `GEMINI_API_KEY` and the venv is active
- Streamlit not found: `pip install -r requirements.txt`
- ChromaDB errors: delete `chroma_db/` to rebuild if corrupted (data loss)

## � License

Educational project — free to use for learning.
