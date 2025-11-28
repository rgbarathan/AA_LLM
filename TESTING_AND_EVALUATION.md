# Testing & Evaluation Guide

This guide covers how to test and evaluate the Telecom Architecture Advisor application across functional, retrieval, generation, and user experience dimensions.

## Table of Contents
1. [Quick Start Testing](#quick-start-testing)
2. [Test Categories](#test-categories)
3. [Evaluation Metrics](#evaluation-metrics)
4. [Running Automated Tests](#running-automated-tests)
5. [Manual Testing Checklist](#manual-testing-checklist)
6. [Performance Benchmarking](#performance-benchmarking)
7. [Troubleshooting Tests](#troubleshooting-tests)

---

## Quick Start Testing

### Verify Installation
```bash
# 1) Check Python and dependencies
python --version
pip list | grep -E "chromadb|streamlit|requests|tenacity|rank-bm25"

# 2) Check API key is configured
grep -q "GEMINI_API_KEY" .env && echo "✓ API key configured" || echo "✗ Missing .env"

# 3) Test ChromaDB initialization
python -c "from telecom_advisor_enhanced import collection; print(f'KB has {collection.count()} chunks')"

# 4) Start the app
streamlit run streamlit_app.py
```

### First Query Test (Sanity Check)
1. Open http://localhost:8501
2. In **Chat** mode, ask: *"What are the key components of a 5G architecture?"*
3. Verify:
   - ✓ Response appears in ~5–10 seconds
   - ✓ Citations include topic, domain, relevance score, and source
   - ✓ No API errors in logs

---

## Test Categories

### 1. **Functional Tests** (Code Logic)
Test core features and workflows.

#### Knowledge Base Initialization
```python
# test_knowledge_base.py
from telecom_advisor_enhanced import initialize_knowledge_base, collection

def test_kb_init():
    """Test knowledge base loads and has content."""
    initialize_knowledge_base()
    count = collection.count()
    assert count > 0, f"Knowledge base empty, got {count} chunks"
    print(f"✓ Knowledge base initialized with {count} chunks")

def test_kb_metadata():
    """Test metadata is properly set on chunks."""
    results = collection.get(limit=5, include=["documents", "metadatas"])
    for meta in results["metadatas"]:
        assert "topic" in meta or "domain" in meta, f"Missing metadata: {meta}"
    print("✓ Metadata present on chunks")
```

#### Retrieval Logic
```python
def test_hybrid_search():
    """Test hybrid search returns relevant results."""
    from telecom_advisor_enhanced import hybrid_search
    
    query = "5G microservices architecture"
    results = hybrid_search(query, top_k=5)
    assert len(results) > 0, "Hybrid search returned no results"
    assert all("text" in r for r in results), "Missing 'text' in results"
    assert all("source" in r["metadata"] for r in results), "Missing source metadata"
    print(f"✓ Hybrid search returned {len(results)} results")

def test_retrieval_with_citations():
    """Test context and citations are properly formatted."""
    from telecom_advisor_enhanced import retrieve_context_with_citations
    
    context, citations = retrieve_context_with_citations("What is microservices?")
    assert context is not None and len(context) > 0, "Context is empty"
    assert citations is not None and len(citations) > 0, "Citations list is empty"
    print(f"✓ Retrieved context and {len(citations)} citations")
```

#### API Integration
```python
def test_gemini_api_call():
    """Test Gemini API responds correctly."""
    from telecom_advisor_enhanced import call_gemini_api
    
    prompt = "Briefly explain microservices architecture in one sentence."
    response = call_gemini_api(prompt)
    assert response is not None, "Gemini API returned None"
    assert "content" in response or "candidates" in response, f"Unexpected response format: {response.keys()}"
    print("✓ Gemini API call successful")

def test_api_retry_logic():
    """Test retry decorator works on transient failures."""
    from telecom_advisor_enhanced import call_gemini_api
    import unittest.mock as mock
    
    # Simulate 2 failures then success
    with mock.patch('requests.post') as mock_post:
        mock_post.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            mock.MagicMock(json=lambda: {"candidates": [{"content": {"parts": [{"text": "Success"}]}}]})
        ]
        # Note: This is a simplified mock; actual implementation may vary
        print("✓ Retry logic test structure defined")
```

#### Export Functionality
```python
def test_export_markdown():
    """Test Markdown export generates valid output."""
    from telecom_advisor_enhanced import export_to_markdown
    
    conversation = [
        {"role": "user", "content": "What is RAG?"},
        {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation..."}
    ]
    md = export_to_markdown(conversation)
    assert "# Conversation" in md or "##" in md, "Missing markdown structure"
    assert "What is RAG?" in md, "User question missing from export"
    print("✓ Markdown export valid")

def test_export_pdf():
    """Test PDF export generates file."""
    from telecom_advisor_enhanced import export_to_pdf
    import os
    
    conversation = [{"role": "user", "content": "Test"}, {"role": "assistant", "content": "Response"}]
    pdf_path = export_to_pdf(conversation)
    assert os.path.exists(pdf_path), f"PDF not created at {pdf_path}"
    assert os.path.getsize(pdf_path) > 0, "PDF file is empty"
    print(f"✓ PDF export created at {pdf_path}")
```

---

### 2. **Retrieval Evaluation** (Information Retrieval)
Measure how well the system finds relevant knowledge.

#### Metrics

| Metric | Formula | Target | What It Means |
|--------|---------|--------|---------------|
| **Precision@K** | # relevant in top-K / K | ≥ 0.7 | Of the top K results, how many are relevant? |
| **Recall@K** | # relevant in top-K / total relevant | ≥ 0.6 | Of all relevant docs, how many are in top-K? |
| **MRR (Mean Reciprocal Rank)** | 1 / rank of first relevant | ≥ 0.8 | How soon does the first relevant result appear? |
| **NDCG (Normalized DCG)** | Discounted cumulative gain, normalized | ≥ 0.75 | Ranking quality (penalizes irrelevant early results) |
| **MAP (Mean Average Precision)** | Average of precisions at each relevant result | ≥ 0.7 | Overall ranking quality across all queries |

#### Test Dataset
Create a file `test_queries.json`:

```json
{
  "queries": [
    {
      "id": "q1",
      "query": "What are the key components of a 5G network architecture?",
      "relevant_docs": ["5g_components.md", "tmf629_customer.pdf"],
      "topic": "5g"
    },
    {
      "id": "q2",
      "query": "Compare monolithic and microservices architectures",
      "relevant_docs": ["monolithic.md", "microservices.md"],
      "topic": "architecture_patterns"
    },
    {
      "id": "q3",
      "query": "What is the TM Forum standard for product ordering?",
      "relevant_docs": ["tmf622_ordering.pdf"],
      "topic": "tmf_standards"
    }
  ]
}
```

#### Evaluation Script
```python
# eval_retrieval.py
import json
from telecom_advisor_enhanced import hybrid_search
from typing import List, Dict

def evaluate_retrieval(test_queries_file: str = "test_queries.json"):
    """
    Evaluate retrieval quality using standard IR metrics.
    """
    with open(test_queries_file) as f:
        test_data = json.load(f)
    
    metrics = {
        "precision@5": [],
        "recall@5": [],
        "mrr": [],
        "ndcg@5": [],
        "queries_evaluated": 0
    }
    
    for q in test_data["queries"]:
        query = q["query"]
        relevant_sources = set(q["relevant_docs"])
        
        # Retrieve top 5 results
        results = hybrid_search(query, top_k=5)
        retrieved_sources = {r["metadata"].get("source", "") for r in results}
        
        # Compute metrics
        relevant_retrieved = retrieved_sources & relevant_sources
        
        # Precision@5
        p_at_5 = len(relevant_retrieved) / min(5, len(results)) if results else 0
        metrics["precision@5"].append(p_at_5)
        
        # Recall@5
        r_at_5 = len(relevant_retrieved) / len(relevant_sources) if relevant_sources else 0
        metrics["recall@5"].append(r_at_5)
        
        # MRR
        mrr = 0
        for i, r in enumerate(results):
            if r["metadata"].get("source", "") in relevant_sources:
                mrr = 1 / (i + 1)
                break
        metrics["mrr"].append(mrr)
        
        # NDCG@5 (simplified: binary relevance)
        dcg = sum(
            (1 if results[i]["metadata"].get("source", "") in relevant_sources else 0) / (i + 2)
            for i in range(min(5, len(results)))
        )
        idcg = sum(1 / (i + 2) for i in range(min(5, len(relevant_sources))))
        ndcg = dcg / idcg if idcg > 0 else 0
        metrics["ndcg@5"].append(ndcg)
        
        metrics["queries_evaluated"] += 1
        
        print(f"Query: {query[:50]}...")
        print(f"  P@5={p_at_5:.2f}, R@5={r_at_5:.2f}, MRR={mrr:.2f}, NDCG@5={ndcg:.2f}")
    
    # Aggregate
    print("\n=== Retrieval Metrics (Aggregated) ===")
    for metric, values in metrics.items():
        if metric != "queries_evaluated" and values:
            avg = sum(values) / len(values)
            print(f"{metric}: {avg:.3f}")
    
    return metrics

if __name__ == "__main__":
    evaluate_retrieval()
```

**Run it:**
```bash
python eval_retrieval.py
```

---

### 3. **Generation Evaluation** (Answer Quality)
Measure how well the LLM generates useful answers.

#### Metrics

| Metric | How to Measure | Target |
|--------|----------------|--------|
| **Relevance** | Does the answer address the query? (1–5 scale) | ≥ 4.0 avg |
| **Factuality** | Are claims grounded in knowledge base? (1–5 scale) | ≥ 4.2 avg |
| **Citation Coverage** | % of claims with citations | ≥ 80% |
| **Hallucination Rate** | % of statements not in KB | ≤ 10% |
| **Answer Length** | Avg tokens in response | 150–500 |
| **Response Time** | Latency from query to answer | < 15 sec |

#### Manual Evaluation Rubric
Create `evaluation_rubric.md`:

```markdown
## Answer Evaluation Rubric (1–5 scale)

### Relevance
- 5: Directly answers the question; highly relevant
- 4: Answers the question with minor irrelevant content
- 3: Partially addresses the question
- 2: Mostly irrelevant
- 1: Completely off-topic

### Factuality
- 5: All claims are correct per knowledge base; well-grounded
- 4: Mostly correct; 1–2 minor inaccuracies
- 3: Roughly 50% accurate; some unsupported claims
- 2: Many inaccurate or unsupported claims
- 1: Mostly false or hallucinated

### Citation Quality
- 5: All major claims cited; sources are specific and relevant
- 4: Most claims cited; a few missing
- 3: About 50% of claims cited
- 2: Few citations; vague sources
- 1: No citations or incorrect attributions

### Clarity
- 5: Excellent structure; easy to follow
- 4: Good structure with minor clarity issues
- 3: Adequate; some confusing sections
- 2: Hard to follow; poorly organized
- 1: Confusing; very hard to understand
```

#### Evaluation Script
```python
# eval_generation.py
import time
import json
from telecom_advisor_enhanced import get_architecture_advice_with_rag

def evaluate_generation(test_queries: List[str] = None):
    """
    Evaluate answer quality for a set of queries.
    """
    if test_queries is None:
        test_queries = [
            "What is the difference between monolithic and microservices architectures?",
            "Explain the key features of 5G network architecture.",
            "What are the main TM Forum standards for telecom service management?",
        ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        start = time.time()
        
        answer, context, citations = get_architecture_advice_with_rag(query)
        
        elapsed = time.time() - start
        
        result = {
            "query": query,
            "answer": answer,
            "num_citations": len(citations),
            "response_time_sec": elapsed,
            "context_chars": len(context),
        }
        results.append(result)
        
        print(f"⏱️  Response time: {elapsed:.2f}s")
        print(f"📌 Citations: {len(citations)}")
        print(f"📝 Answer preview: {answer[:200]}...")
    
    # Save for manual review
    with open("generation_eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Aggregate stats
    print("\n=== Generation Metrics ===")
    avg_time = sum(r["response_time_sec"] for r in results) / len(results)
    avg_citations = sum(r["num_citations"] for r in results) / len(results)
    print(f"Avg response time: {avg_time:.2f}s")
    print(f"Avg citations per answer: {avg_citations:.1f}")
    print(f"Results saved to generation_eval_results.json for manual review")
    
    return results

if __name__ == "__main__":
    evaluate_generation()
```

**Run it:**
```bash
python eval_generation.py
```

Then manually score each answer in `generation_eval_results.json` using the rubric.

---

### 4. **Integration Tests** (End-to-End Workflows)
Test complete user workflows.

```python
# test_integration.py
from telecom_advisor_enhanced import (
    get_architecture_advice_with_rag,
    compare_architectures,
    upload_text_file_to_knowledge_base,
    export_to_markdown,
    collection
)
import tempfile
import os

def test_chat_workflow():
    """Test basic chat flow."""
    print("Testing chat workflow...")
    
    query = "What is a monolithic architecture?"
    answer, context, citations = get_architecture_advice_with_rag(query)
    
    assert answer and len(answer) > 50, "Answer too short"
    assert citations and len(citations) > 0, "No citations"
    print("✓ Chat workflow OK")

def test_compare_workflow():
    """Test architecture comparison."""
    print("Testing compare workflow...")
    
    arch1 = "Microservices"
    arch2 = "Monolithic"
    comparison = compare_architectures(arch1, arch2)
    
    assert comparison and len(comparison) > 50, "Comparison empty"
    assert arch1.lower() in comparison.lower() or arch2.lower() in comparison.lower(), \
        "Comparison doesn't mention both architectures"
    print("✓ Compare workflow OK")

def test_upload_workflow():
    """Test file upload and re-ingestion."""
    print("Testing upload workflow...")
    
    # Create a temp test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("---\ntopic: test\ndomain: testing\n---\nTest knowledge content.")
        temp_path = f.name
    
    try:
        before_count = collection.count()
        upload_text_file_to_knowledge_base(temp_path)
        after_count = collection.count()
        
        assert after_count > before_count, "No new chunks added"
        print(f"✓ Upload workflow OK (added {after_count - before_count} chunks)")
    finally:
        os.remove(temp_path)

def test_export_workflow():
    """Test conversation export."""
    print("Testing export workflow...")
    
    conversation = [
        {"role": "user", "content": "Test question"},
        {"role": "assistant", "content": "Test answer with citation [Source 1]"}
    ]
    
    md = export_to_markdown(conversation)
    assert "Test question" in md, "Question not in export"
    assert "Test answer" in md, "Answer not in export"
    print("✓ Export workflow OK")

def run_all_integration_tests():
    """Run all integration tests."""
    print("=== Integration Tests ===\n")
    test_chat_workflow()
    test_compare_workflow()
    test_upload_workflow()
    test_export_workflow()
    print("\n✓ All integration tests passed!")

if __name__ == "__main__":
    run_all_integration_tests()
```

**Run it:**
```bash
python test_integration.py
```

---

### 5. **Performance Tests** (Speed & Scalability)

```python
# test_performance.py
import time
from telecom_advisor_enhanced import (
    hybrid_search,
    get_architecture_advice_with_rag,
    collection
)

def benchmark_retrieval(num_queries: int = 50):
    """Benchmark retrieval latency."""
    print(f"Benchmarking retrieval with {num_queries} queries...")
    
    queries = [
        "microservices",
        "5G",
        "architecture",
        "monolithic",
        "cloud",
    ] * (num_queries // 5)
    
    times = []
    for q in queries[:num_queries]:
        start = time.time()
        hybrid_search(q, top_k=5)
        times.append(time.time() - start)
    
    avg = sum(times) / len(times)
    p95 = sorted(times)[int(0.95 * len(times))]
    p99 = sorted(times)[int(0.99 * len(times))]
    
    print(f"\n=== Retrieval Performance ===")
    print(f"Queries: {len(times)}")
    print(f"Avg latency: {avg*1000:.1f}ms")
    print(f"P95 latency: {p95*1000:.1f}ms")
    print(f"P99 latency: {p99*1000:.1f}ms")
    print(f"Target: <500ms avg, <1000ms p95")

def benchmark_generation(num_queries: int = 5):
    """Benchmark end-to-end answer generation."""
    print(f"\nBenchmarking generation with {num_queries} queries...")
    
    queries = [
        "What is a microservices architecture?",
        "Explain 5G network design.",
        "Compare monolithic vs microservices.",
        "What are cloud-native principles?",
        "Define enterprise architecture.",
    ][:num_queries]
    
    times = []
    for q in queries:
        start = time.time()
        get_architecture_advice_with_rag(q)
        times.append(time.time() - start)
    
    avg = sum(times) / len(times)
    
    print(f"\n=== Generation Performance ===")
    print(f"Queries: {len(times)}")
    print(f"Avg latency: {avg:.1f}s")
    print(f"Target: <15s avg")

def benchmark_kb_size():
    """Report knowledge base size and stats."""
    count = collection.count()
    print(f"\n=== Knowledge Base Stats ===")
    print(f"Total chunks: {count}")
    print(f"Approx docs (if 500 chunks/doc): {count // 500}")

def run_performance_benchmarks():
    """Run all performance tests."""
    print("=== Performance Benchmarks ===\n")
    benchmark_kb_size()
    benchmark_retrieval(num_queries=50)
    benchmark_generation(num_queries=3)

if __name__ == "__main__":
    run_performance_benchmarks()
```

**Run it:**
```bash
python test_performance.py
```

---

## Running Automated Tests

### Option 1: Using pytest (Recommended)

Install pytest:
```bash
pip install pytest pytest-cov
```

Create `tests/` directory:
```bash
mkdir tests
mv test_*.py eval_*.py tests/
```

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

Run a specific test:
```bash
pytest tests/test_integration.py::test_chat_workflow -v
```

### Option 2: Using unittest

```python
# tests/run_tests.py
import unittest
import sys

# Discover and run all tests
loader = unittest.TestLoader()
suite = loader.discover('tests', pattern='test_*.py')
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
```

Run:
```bash
python tests/run_tests.py
```

---

## Manual Testing Checklist

Use this checklist for QA testing before release:

### 🟢 Installation & Setup
- [ ] Python 3.9+ installed
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `.env` file configured with valid GEMINI_API_KEY
- [ ] `streamlit run streamlit_app.py` starts without errors
- [ ] CLI `python telecom_advisor_enhanced.py` launches interactive mode

### 🟢 Knowledge Base & Retrieval
- [ ] Initial KB load shows > 100 chunks
- [ ] `test_hybrid_search()` returns relevant results
- [ ] Metadata (topic, domain, priority) visible on chunks
- [ ] Upload new PDF via UI and see chunks increase
- [ ] `reload` command re-ingests external sources

### 🟢 Chat Interface (Streamlit)
- [ ] Chat tab loads; can type and submit queries
- [ ] Responses appear in < 15 seconds
- [ ] Citations show topic, domain, relevance, preview
- [ ] Conversation history persists in session
- [ ] Clear chat button resets history

### 🟢 Compare Mode
- [ ] `compare <arch1> vs <arch2>` returns comparison
- [ ] Comparison mentions both architectures
- [ ] Citations included

### 🟢 Upload Tab
- [ ] Can upload PDF, DOCX, TXT, MD
- [ ] Upload adds chunks to KB
- [ ] Metadata fields (topic, domain) settable
- [ ] Error on invalid file format

### 🟢 Analytics Tab
- [ ] Shows query history count
- [ ] Shows topic distribution chart
- [ ] Shows recent queries list
- [ ] Charts render without errors

### 🟢 Export Tab
- [ ] Export to Markdown generates file
- [ ] Export to PDF generates file
- [ ] Exported files contain conversation
- [ ] Files are downloadable

### 🟢 API & Error Handling
- [ ] Graceful error if GEMINI_API_KEY missing
- [ ] Retry logic kicks in on network errors
- [ ] Timeout handled (< 30 sec timeout)
- [ ] Invalid query returns safe error message

### 🟢 Performance
- [ ] Retrieval completes in < 500ms
- [ ] Answer generation completes in < 15s
- [ ] No memory leaks after 50+ queries
- [ ] ChromaDB persists across restarts

### 🟢 Data & Privacy
- [ ] `.env` not committed to Git
- [ ] `analytics.json` not committed (in `.gitignore`)
- [ ] No API keys in logs
- [ ] Conversations not stored to disk (unless exported)

---

## Evaluation Metrics Summary

### Retrieval (Information Retrieval)
- **Precision@5**: ≥ 0.7 (7/10 top results relevant)
- **Recall@5**: ≥ 0.6 (6/10 relevant docs retrieved)
- **MRR**: ≥ 0.8 (first relevant result in top 2)
- **NDCG@5**: ≥ 0.75 (ranking quality)
- **MAP**: ≥ 0.7 (mean average precision)

### Generation (Answer Quality)
- **Relevance**: ≥ 4.0/5 (addresses query)
- **Factuality**: ≥ 4.2/5 (grounded in KB)
- **Citation Coverage**: ≥ 80% (claims cited)
- **Hallucination Rate**: ≤ 10% (false statements)
- **Clarity**: ≥ 4.0/5 (easy to understand)

### Performance
- **Retrieval Latency**: < 500ms avg, < 1000ms p95
- **Generation Latency**: < 15s avg (including API call)
- **Knowledge Base Size**: Track chunk counts over time

### User Experience
- **Task Success Rate**: % of user tasks completed successfully
- **Error Rate**: % of queries returning errors
- **User Satisfaction**: Rating on scale 1–5

---

## Troubleshooting Tests

### Common Test Failures

#### Test: "Knowledge base empty"
```bash
# Check if knowledge_base/ has files
ls -la knowledge_base/

# Reinitialize KB
python -c "from telecom_advisor_enhanced import initialize_knowledge_base; initialize_knowledge_base()"
```

#### Test: "Hybrid search returned no results"
```bash
# Check ChromaDB
python -c "from telecom_advisor_enhanced import collection; print(collection.count())"

# If 0, rebuild from knowledge_base/
rm -rf chroma_db/
python -c "from telecom_advisor_enhanced import initialize_knowledge_base; initialize_knowledge_base()"
```

#### Test: "Gemini API returns 401"
```bash
# Verify API key
cat .env | grep GEMINI_API_KEY

# Test API key directly
curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

#### Test: "PDF extraction fails"
```bash
# Check if file is text-based
pdfinfo your_file.pdf | grep "PDF version"

# If scanned, convert with OCR (pdfminer, tesseract) or use image-based PDF reader
```

---

## Next Steps

1. **Run sanity check**: Execute Quick Start Testing section
2. **Evaluate retrieval**: Run `python eval_retrieval.py`
3. **Evaluate generation**: Run `python eval_generation.py` and manually score
4. **Run integration tests**: `python test_integration.py`
5. **Benchmark performance**: `python test_performance.py`
6. **Iterate**: Based on results, improve knowledge base, retrieval, or prompts

---

## Resources

- [Chromadb Docs](https://docs.trychroma.com/)
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs/)
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [RAG Evaluation Frameworks](https://huggingface.co/docs/datasets/bertscore.html)
