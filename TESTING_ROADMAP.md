# Testing Roadmap & Quick Commands

## 📋 Complete Testing Command Reference

### 🟢 Sanity Check (1 minute)
Test Python, dependencies, API key, and knowledge base initialization:

```bash
# Check Python version
python3 --version

# Check dependencies
pip list | grep -E "chromadb|streamlit|requests|tenacity"

# Check API key configuration
grep -q "GEMINI_API_KEY" .env && echo "✓ API key configured"

# Check knowledge base has content
python3 -c "from telecom_advisor_enhanced import collection; print(f'✓ KB: {collection.count()} chunks')"
```

### 🟢 Unit Tests (10-15 minutes)

Run individual test modules:

```bash
# Test knowledge base (initialization, metadata, content)
python3 -m tests.test_knowledge_base

# Test retrieval (hybrid search, citations, relevance scores)
python3 -m tests.test_retrieval

# Test integration (chat, compare, upload, export workflows)
python3 -m tests.test_integration

# Test performance (latency, throughput, knowledge base size)
python3 -m tests.test_performance
```

### 🟢 Run All Tests at Once

```bash
# Option 1: Using the test runner (no dependencies)
python3 run_tests.py

# Option 2: Using pytest (if installed)
pip install pytest pytest-cov
pytest tests/ -v

# Option 3: Run with coverage report
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### 🟢 Manual Testing via Web UI (15-20 minutes)

Start the Streamlit application and test manually:

```bash
streamlit run streamlit_app.py
```

Then in your browser (http://localhost:8501):
- **Chat Tab**: Ask "What is microservices architecture?" → Verify citation format
- **Compare Tab**: Compare "Microservices" vs "Monolithic" → Verify comparison logic
- **Upload Tab**: Upload a test file → Verify chunks are added to KB
- **Analytics Tab**: View query history and topic charts → Verify data logging
- **Export Tab**: Export conversation to PDF/Markdown → Verify file format

### 🟢 CLI Testing (5 minutes)

Test via command-line interface:

```bash
python3 telecom_advisor_enhanced.py

# Then try these commands:
> compare Microservices vs Monolithic
> help
> analytics
> reload
> export md
> exit
```

## 📊 Test Coverage Matrix

| Component | Unit Test | Integration | Manual | Performance |
|-----------|-----------|-------------|--------|-------------|
| Knowledge Base | ✅ test_knowledge_base.py | ✅ test_integration | ✅ Upload Tab | ✅ test_performance |
| Retrieval/Search | ✅ test_retrieval.py | ✅ Chat workflow | ✅ Chat Tab | ✅ test_performance |
| Answer Generation | ✅ (via integration) | ✅ Chat workflow | ✅ Chat Tab | ✅ test_performance |
| Architecture Compare | ✅ (via integration) | ✅ Compare workflow | ✅ Compare Tab | - |
| File Upload | ✅ (via integration) | ✅ Upload workflow | ✅ Upload Tab | - |
| PDF Export | ✅ (via integration) | ✅ Export workflow | ✅ Export Tab | - |
| Markdown Export | ✅ (via integration) | ✅ Export workflow | ✅ Export Tab | - |
| Analytics | - | - | ✅ Analytics Tab | - |
| API Integration | ✅ (via integration) | ✅ Chat workflow | ✅ Chat Tab | - |

## 📈 Expected Test Results

### Knowledge Base Tests
```
✓ KB initialized with 8,000+ chunks
✓ Metadata present (topic, domain, chunk_index)
✓ Chunks have actual content (text > 10 chars)
```

### Retrieval Tests
```
✓ Hybrid search returns 3-5 results per query
✓ Results structure valid (text, metadata, scores)
✓ Relevance scores in range [0, 1]
✓ Citations include topic, domain, relevance_score, text_preview
```

### Integration Tests
```
✓ Chat: Answer generated in ~4-5 seconds with 2+ citations
✓ Compare: Comparison returns both architectures mentioned
✓ Upload: File adds chunks to knowledge base
✓ Export MD: Markdown file created with conversation
✓ Export PDF: PDF file created with conversation
```

### Performance Tests
```
✓ Retrieval: avg < 100ms, p95 < 500ms (sub-second)
✓ Generation: avg ~ 4-5 seconds (includes Gemini API)
✓ KB Size: 8,000-10,000 chunks depending on loads
```

## 🎯 Key Evaluation Metrics

### Retrieval Quality (from test_retrieval.py)
- **Precision@5**: Should be ≥ 0.7 (7 of top 10 results relevant)
- **Recall@5**: Should be ≥ 0.6 (60% of relevant docs retrieved)
- **MRR (Mean Reciprocal Rank)**: Should be ≥ 0.8 (first relevant in top 2)
- **NDCG@5**: Should be ≥ 0.75 (good ranking quality)

### Generation Quality (manual scoring)
- **Relevance**: 4+/5 (directly addresses the question)
- **Factuality**: 4+/5 (grounded in knowledge base)
- **Citation Coverage**: ≥ 80% (claims have [Source N])
- **Clarity**: 4+/5 (well-structured, easy to follow)

### Performance (from test_performance.py)
- **Retrieval Latency**: < 500ms avg (target: < 100ms)
- **Generation Latency**: < 15s avg (target: 5-10s)
- **KB Health**: > 100 chunks (actual: 8,000+)

## 🔧 Troubleshooting

### If tests fail:
1. **"KB empty"**: Reinit with `python3 -c "from telecom_advisor_enhanced import initialize_knowledge_base; initialize_knowledge_base()"`
2. **"Hybrid search no results"**: Check ChromaDB with `collection.count()`
3. **"API 401 error"**: Verify `.env` has valid `GEMINI_API_KEY`
4. **"Import errors"**: Run `pip install -r requirements.txt`

## 📝 Testing Checklist for Assignment

Use this checklist to track your testing progress:

- [ ] **Sanity Check** (1 min) - Python, dependencies, API key, KB initialization
- [ ] **Knowledge Base Tests** (2 min) - Run test_knowledge_base.py
- [ ] **Retrieval Tests** (2 min) - Run test_retrieval.py
- [ ] **Integration Tests** (3 min) - Run test_integration.py
- [ ] **Performance Tests** (3 min) - Run test_performance.py
- [ ] **Web UI Chat** (5 min) - Test chat with various queries
- [ ] **Web UI Features** (5 min) - Test Compare, Upload, Analytics, Export
- [ ] **CLI Testing** (3 min) - Test help, reload, analytics, export commands
- [ ] **Documentation** (2 min) - Review TESTING_AND_EVALUATION.md
- [ ] **Document Results** (5 min) - Save test output to file

**Total Time: ~30-45 minutes**

## 📚 Documentation Files

1. **TESTING_AND_EVALUATION.md** - Comprehensive guide (400+ lines)
   - Full test categories with code examples
   - Evaluation rubrics and metrics
   - Troubleshooting and advanced scenarios

2. **TESTING_QUICK_START.md** - Quick reference guide
   - Step-by-step testing workflow
   - Expected outputs for each test
   - Common troubleshooting

3. **TESTING_SUMMARY.md** - This file
   - Test results summary
   - Complete command reference
   - Recommended testing workflow

4. **TESTING_ROADMAP.md** - This visual guide
   - Command reference with expected outputs
   - Coverage matrix
   - Evaluation metrics

## 🚀 Quick Start Template

Copy and run this to test everything:

```bash
#!/bin/bash
set -e

echo "🧪 Testing Telecom Architecture Advisor"
echo "========================================"

echo ""
echo "1️⃣  Sanity Check..."
python3 -c "from telecom_advisor_enhanced import collection; print(f'   ✓ KB: {collection.count()} chunks')"

echo ""
echo "2️⃣  Knowledge Base Tests..."
python3 -m tests.test_knowledge_base 2>&1 | tail -3

echo ""
echo "3️⃣  Integration Tests..."
python3 -m tests.test_integration 2>&1 | tail -3

echo ""
echo "4️⃣  Performance Benchmarks..."
python3 -m tests.test_performance 2>&1 | tail -5

echo ""
echo "✅ Testing complete!"
```

Save as `test_all.sh`, then run:
```bash
chmod +x test_all.sh
./test_all.sh
```

---

**Last Updated:** November 28, 2025  
**Status:** Ready to use for testing and evaluation
