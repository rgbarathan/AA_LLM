# Telecom Architecture Advisor (RAG + Streamlit)

AI-powered telecom architecture advisor using Retrieval-Augmented Generation (RAG), hybrid search, and a Streamlit web UI. It integrates with Google Gemini for high-quality responses grounded in a telecom knowledge base.

> Looking for the complete enhancement details? See `docs/ENHANCEMENTS.md`.

## 🎯 Overview

This app helps telecom architects and engineers make informed design decisions. It combines:

- **Google Gemini 2.5 Flash** (LLM via REST API)
- **ChromaDB** vector store with Sentence-Transformers embeddings (all-MiniLM-L6-v2)
- **Hybrid retrieval** (semantic + BM25 keyword)
- **Dynamic knowledge loading** from markdown/PDF/DOCX with metadata
- **Citations** with normalized relevance scoring
- **Streamlit web interface** + interactive CLI
- **Auto-reload** external sources via JSON config

### Key Features
✅ RAG implementation with vector database  
✅ Dynamic knowledge ingestion (no hardcoded content)  
✅ YAML front matter support for metadata  
✅ Multi-format support (MD, TXT, PDF, DOCX)  
✅ Hybrid search (semantic + keyword)  
✅ Conversation history and context awareness  
✅ Citation tracking with source attribution  
✅ Export conversations (Markdown, PDF)  
✅ Analytics dashboard  
✅ Architecture comparison mode  
✅ CLI reload command for dynamic updates

## 🏗️ Architecture

```
User Input → [Dynamic Knowledge Loading] → ChromaDB + Metadata
                                              ↓
User Query → [Hybrid Search] → Context + History → Prompt → Gemini → Answer + Citations
              ├─ ChromaDB (semantic vectors)
              └─ BM25 (keyword matching)
```

**Flow:**
1. **Initialization**: Load knowledge from `knowledge_base/` and `knowledge_sources.json`
2. **Ingestion**: Parse front matter → chunk text → embed → store in ChromaDB
3. **Query**: User question → hybrid search → retrieve top-N chunks with metadata
4. **Generation**: Build prompt with context + conversation history → Gemini API
5. **Response**: Answer + citations (topic, domain, relevance, preview)

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (check with `python3 --version`)
- **pip** (package manager, usually comes with Python)
- **Git** (for cloning, optional)
- **A Google Gemini API key** (free tier available)

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

**Step 1: Clone or navigate to the project directory**
```bash
# If cloning from GitHub:
git clone https://github.com/rgbarathan/AA_LLM.git
cd AA_LLM
```

**Step 2: Create a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Step 3: Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Configure your Gemini API key**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your GEMINI_API_KEY
# Example:
# GEMINI_API_KEY=your_actual_api_key_here
```

**Step 5: Start the application**

Option A — Web Interface (Recommended):
```bash
streamlit run streamlit_app.py
# Opens automatically at http://localhost:8501
```

Option B — CLI Mode:
```bash
python telecom_advisor_enhanced.py
# Interactive command-line interface with fallback to Streamlit
```

**Automated Setup (Optional)**
```bash
# For a more automated setup with security checks:
chmod +x setup_secure.sh
./setup_secure.sh
```

See `SETUP_SECURITY.md` for additional security configuration details.

## � What you can do

- Chat with the advisor about telecom architecture
- See citations with normalized relevance scores and text previews
- Upload PDFs/DOCX/TXT/MD to expand the knowledge base (UI or CLI)
- Compare architectures (e.g., Microservices vs Monolith)
- View analytics (topics and recent queries)
- Export conversations (Markdown or PDF)
- Reload knowledge sources dynamically without restart

### CLI Commands
When using interactive CLI mode (`python telecom_advisor_enhanced.py`):
- `compare <arch1> vs <arch2>` — Compare two architectures
- `upload <file_path>` — Upload PDF/DOCX/TXT/MD file
- `reload` — Reload external sources from knowledge_sources.json
- `export md` — Export conversation to Markdown
- `export pdf` — Export conversation to PDF
- `analytics` — Show analytics dashboard
- `help` — Show available commands
- `quit` or `exit` — Exit program

## 📂 Key Files

- `telecom_advisor_enhanced.py` — Core RAG logic, Gemini integration, CLI, dynamic knowledge loading
- `streamlit_app.py` — Web UI (Chat, Compare, Upload, Analytics, Export)
- `requirements.txt` — Python dependencies (install with `pip install -r requirements.txt`)
- `.env.example` — Template for environment variables (copy to `.env` and fill in your API key)
- `knowledge_base/` — Markdown/PDF/DOCX files with domain knowledge (auto-loaded on startup)
- `knowledge_sources.json` — Config for external source auto-loading
- `knowledge_sources.example.json` — Template for custom knowledge source configuration
- `chroma_db/` — Vector database (auto-created, persistent)
- `telecom_advisor.log` — Application logs
- `analytics.json` — Query analytics (auto-created)

### Optional/Legacy Files
- `AA_LLM.py` — Minimal Gemini API example
- `telecom_advisor_rag.py` — Original/simple RAG demo
- `SECURITY.md` — Security best practices
- `SETUP_SECURITY.md` — Automated security setup guide
- `docs/ENHANCEMENTS.md` — Detailed enhancement documentation

## ⚙️ Configuration

Environment variables (via `.env`):

- `GEMINI_API_KEY` — your Google Gemini API key (required)
- `KNOWLEDGE_DIR` — custom knowledge directory path (optional, defaults to `knowledge_base`)

Configuration files:

- `knowledge_sources.json` — External knowledge sources (auto-loaded on startup)
- `.env` — API keys and environment config
- `analytics.json` — Query analytics (auto-created)
- `chroma_db/` — Vector database (auto-created, persistent)

Logs and data:

- `telecom_advisor.log` — app logs (rotating)
- `analytics.json` — stores query history and topic stats

## 📚 Knowledge Base (Dynamic Loading)

### Overview
The system now uses **dynamic knowledge loading** instead of hardcoded content. Knowledge is loaded from external files with optional metadata.

### Supported Formats
- **Markdown (.md)**: With optional YAML front matter for metadata
- **Text (.txt)**: Plain text files, can include front matter
- **PDF (.pdf)**: Extracted via PyPDF2
- **Word (.docx)**: Extracted via python-docx

### Adding Knowledge Files

#### Method 1: Drop files in knowledge_base/ (Recommended)
1. Create markdown files in `knowledge_base/` directory
2. Optionally add YAML front matter for metadata:

```markdown
---
topic: 5g
domain: network
priority: high
source_type: seed
---
Your content here. The system will chunk and embed this automatically.
```

**Available metadata fields:**
- `topic`: Category (e.g., microservices, 5g, standards)
- `domain`: Domain area (architecture, network, compliance, infrastructure, services)
- `priority`: high | medium | low
- `source_type`: seed | external | upload
- `source`: Filename (auto-filled if not provided)

#### Method 2: Configure External Sources (Auto-load on startup)
Create or edit `knowledge_sources.json`:

```json
{
  "local_files": [
    {
      "enabled": true,
      "path": "docs/my_document.pdf",
      "topic": "5g",
      "domain": "network"
    }
  ],
  "directories": [
    {
      "enabled": true,
      "path": "knowledge_base",
      "topic": "external",
      "domain": "architecture",
      "recursive": true
    }
  ]
}
```

See `knowledge_sources.example.json` for template.

#### Method 3: Upload via UI or CLI
- **Streamlit UI**: Upload tab → select PDF/DOCX/TXT/MD → set topic/domain → Upload
- **CLI**: Use `upload <file_path>` or `reload` commands

#### Method 4: Programmatic Add
```python
from telecom_advisor_enhanced import add_knowledge_to_db
docs = ["Your custom telecom knowledge..."]
meta = [{"topic": "5g", "domain": "network", "priority": "high"}]
add_knowledge_to_db(docs, meta)
```

### Current Knowledge Included
- **TMF Standards PDFs**: TMF622 (Product Ordering), TMF629 (Customer), TMF638 (Service Inventory)
- **TOGAF PDF**: Enterprise architecture framework (423 chunks)
- **Prompt Engineering DOCX**: AI prompt design
- **Seed Markdown**: Microservices, Monolithic, TM Forum standards

## 🔎 Retrieval & Citations

- Hybrid search combines semantic similarity (ChromaDB) and keyword BM25
- Citations display topic, domain, a text preview, and relevance (normalized score)


## 🧪 Testing & Evaluation

Testing and evaluation artifacts (automated tests, evaluation scripts, and detailed test docs) have been removed from this repository. The core application and runtime scripts remain functional and fully operational. 

For quick sanity checks:
```bash
# 1. Verify Python and dependencies installed
python3 --version
pip list | grep -E "chromadb|streamlit|requests"

# 2. Check if GEMINI_API_KEY is configured
grep GEMINI_API_KEY .env

# 3. Test knowledge base initialization
python3 -c "from telecom_advisor_enhanced import collection; print(f'KB chunks: {collection.count()}')"

# 4. Run a quick manual test via the web interface
streamlit run streamlit_app.py
# Try a sample query: "What is a microservices architecture?"
```

If you need comprehensive automated testing restored, please let me know.

## 🛡️ Security

Never commit secrets. Use `.env` and see `SETUP_SECURITY.md` and `SECURITY.md` for best practices.

## 🧪 Troubleshooting

### Common Issues

**1. Missing API key error**
```
GEMINI_API_KEY not found in environment variables
```
Solution:
- Create a `.env` file in the project root (use `.env.example` as template)
- Set `GEMINI_API_KEY=your_actual_key_here`
- Ensure the venv is activated

**2. Streamlit command not found**
```
command not found: streamlit
```
Solution:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**3. ChromaDB errors or corrupted vector store**
```
ChromaDB initialization error
```
Solution:
```bash
# Backup any important data, then delete the vector store
rm -rf chroma_db/
# Restart the app to rebuild
streamlit run streamlit_app.py
```

**4. Knowledge base not loading**
- Verify `knowledge_sources.json` paths exist and are correct
- Ensure `enabled: true` for sources you want loaded
- Check file permissions and formats (PDF text-based, not scanned images)
- For new knowledge, place files in `knowledge_base/` directory

**5. PDF extraction fails**
Solution:
- Ensure PDFs are text-based (not scanned images)
- Convert scanned PDFs using OCR tools (tesseract, etc.) first
- Try uploading via the UI with different PDFs to isolate the issue

**6. Slow response or timeout errors**
- Check your internet connection
- Verify Gemini API quota hasn't been exceeded
- Reduce query complexity (shorter, more specific questions)
- Increase `REQUEST_TIMEOUT` in `telecom_advisor_enhanced.py` if needed

**7. Environment activation issues**
```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Verify activation (prompt should show (.venv))
which python  # Should point to .venv/bin/python
```

## � License

Educational project — free to use for learning.
