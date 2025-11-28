# Quick Start Test Guide

Run these commands in order to test and evaluate the Telecom Architecture Advisor.

## Prerequisites
```bash
# Ensure you're in the project directory
cd "/Users/rbarat738@cable.comcast.com/Documents/Drexel/Books and Assignments/Assignments/Assignment 4/Project Architecture Advisor"

# Activate virtual environment (if using venv)
source .venv/bin/activate

# Install test dependencies (optional, but recommended)
pip install pytest pytest-cov
```

## Quick Sanity Check (1 minute)

```bash
# Test Python and dependencies
python --version
pip list | grep -E "chromadb|streamlit|requests"

# Test API key configuration
grep -q "GEMINI_API_KEY" .env && echo "✓ API key configured" || echo "✗ Missing .env"

# Test ChromaDB initialization
python -c "from telecom_advisor_enhanced import collection; print(f'KB has {collection.count()} chunks')"
```

## Test Individual Modules (5-10 minutes)

### Test Knowledge Base
```bash
python -m tests.test_knowledge_base
```
Expected output:
- Knowledge base initialized with > 100 chunks
- Metadata present on chunks
- Chunks have content

### Test Retrieval & Search
```bash
python -m tests.test_retrieval
```
Expected output:
- Hybrid search returns results
- Results have correct structure
- Citations are properly formatted
- Relevance scores are in valid range [0, 1]

### Test Integration (Chat, Compare, Upload, Export)
```bash
python -m tests.test_integration
```
Expected output:
- Chat workflow completes in < 15 seconds
- Compare returns comparison between architectures
- Upload adds chunks to knowledge base
- Markdown export creates valid markdown
- PDF export creates valid PDF file

### Test Performance & Benchmarks
```bash
python -m tests.test_performance
```
Expected output:
- Retrieval latency: avg < 500ms, p95 < 1000ms
- Generation latency: avg < 15s
- Knowledge base stats

## Run All Tests at Once

### Option 1: Using the test runner (no pytest required)
```bash
python run_tests.py
```

### Option 2: Using pytest (recommended if installed)
```bash
pytest tests/ -v --tb=short
```

### Option 3: Run with coverage report
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

## Manual Testing Checklist (15 minutes)

### Start the Web App
```bash
streamlit run streamlit_app.py
```

Then test these workflows in your browser (http://localhost:8501):

- [ ] **Chat Tab**: Ask "What is microservices architecture?" → Get answer with citations in < 10 seconds
- [ ] **Compare Tab**: Compare "Microservices" vs "Monolithic" → Get detailed comparison
- [ ] **Upload Tab**: Try uploading a test PDF or text file → Verify chunks are added
- [ ] **Analytics Tab**: View query history and topic distribution charts
- [ ] **Export Tab**: Export a conversation to both Markdown and PDF

### CLI Testing
```bash
python telecom_advisor_enhanced.py
```

Then try these commands:
```
> compare Microservices vs Monolithic
> help
> analytics
> quit
```

## Evaluation Metrics to Track

### Retrieval Quality (after running test_retrieval.py)
- [ ] Precision@5 ≥ 0.7
- [ ] Recall@5 ≥ 0.6
- [ ] MRR ≥ 0.8
- [ ] NDCG@5 ≥ 0.75

### Generation Quality (manual scoring)
- [ ] Relevance: 4+/5 (answers the question)
- [ ] Factuality: 4+/5 (grounded in knowledge base)
- [ ] Citation Coverage: ≥ 80% of claims cited

### Performance Benchmarks (after running test_performance.py)
- [ ] Retrieval avg latency < 500ms
- [ ] Generation avg latency < 15s
- [ ] Knowledge base > 100 chunks

## Troubleshooting

### Test: "Knowledge base empty"
```bash
# Reinitialize
rm -rf chroma_db/
python -c "from telecom_advisor_enhanced import initialize_knowledge_base; initialize_knowledge_base()"
python -m tests.test_knowledge_base
```

### Test: "Hybrid search returned no results"
```bash
# Check KB status
python -c "from telecom_advisor_enhanced import collection; print(f'Chunks: {collection.count()}')"

# Reload from knowledge sources
python -c "from telecom_advisor_enhanced import initialize_knowledge_base; initialize_knowledge_base()"
```

### Test: "Gemini API returns 401"
```bash
# Verify API key is correct
cat .env | grep GEMINI_API_KEY

# Test API key directly
curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

## Test Results Documentation

After running tests, capture results for your assignment:

```bash
# Save test output to file
python run_tests.py > test_results.txt 2>&1

# Run performance benchmarks with output
python -m tests.test_performance > performance_results.txt 2>&1

# Run retrieval evaluation
python -m tests.test_retrieval > retrieval_results.txt 2>&1
```

## Files Created for Testing

- `tests/test_knowledge_base.py` - KB initialization and metadata tests
- `tests/test_retrieval.py` - Retrieval quality and IR metrics tests
- `tests/test_integration.py` - End-to-end workflow tests
- `tests/test_performance.py` - Performance and benchmark tests
- `test_queries.json` - Query dataset for retrieval evaluation
- `run_tests.py` - Test runner script
- `TESTING_AND_EVALUATION.md` - Comprehensive testing guide (in root)

## Next Steps

1. **Quick Sanity Check** (1 min): Verify Python, dependencies, API key, KB
2. **Run Individual Tests** (5-10 min): Test each module separately
3. **Run All Tests** (10-15 min): Use run_tests.py
4. **Manual Testing** (15 min): Test via Streamlit UI
5. **Document Results** (5 min): Save output to files for assignment

---

For detailed evaluation metrics and advanced testing scenarios, see `TESTING_AND_EVALUATION.md`.
