# How to Test & Evaluate - Getting Started

## 🎯 Your Question: "How do i test and evaluate the application? any metrics to be used?"

## ✅ Answer

I've created a **comprehensive testing and evaluation framework** with:

1. **5 Documentation Files** explaining how to test and what metrics to use
2. **4 Test Modules** with executable test code
3. **Evaluation Metrics** for retrieval, generation, and performance
4. **Manual Testing Checklist** for web UI and CLI
5. **Test Runner Scripts** that work with or without pytest

---

## 📖 Where to Start

### Option 1: Quick Testing (5-10 minutes)
**File:** `TESTING_QUICK_START.md`
- Prerequisites
- Sanity checks
- How to run each test module
- Expected results
- Common troubleshooting

### Option 2: Complete Understanding (30-45 minutes)
**File:** `TESTING_AND_EVALUATION.md`
- 7 test categories with code examples
- Evaluation metrics and targets
- Manual testing rubric
- IR metrics (Precision, Recall, MRR, NDCG)
- Performance benchmarking
- Advanced troubleshooting

### Option 3: Visual Reference (5 minutes)
**File:** `TESTING_ROADMAP.md`
- Command reference (copy & paste)
- Test coverage matrix
- Expected test results
- Quick start template
- Testing checklist

### Option 4: Overview of Results (5 minutes)
**File:** `TESTING_SUMMARY.md`
- What was created
- Test results
- Recommended workflow
- Known limitations

### Option 5: Complete File Index (5 minutes)
**File:** `TESTING_INDEX.md`
- All files and purposes
- Use cases and which file to read
- File structure
- Quick reference by use case

---

## 🧪 Test Modules (Execute These)

Located in `tests/` directory:

### 1. Knowledge Base Tests
```bash
python3 -m tests.test_knowledge_base
```
**Tests:** KB initialization, metadata, content quality  
**Expected:** ✓ All knowledge base tests passed!

### 2. Retrieval Tests
```bash
python3 -m tests.test_retrieval
```
**Tests:** Hybrid search, citations, relevance scores, IR metrics  
**Expected:** ✓ All retrieval tests passed!

### 3. Integration Tests
```bash
python3 -m tests.test_integration
```
**Tests:** Chat, compare, upload, export workflows  
**Expected:** ✓ All integration tests passed!

### 4. Performance Tests
```bash
python3 -m tests.test_performance
```
**Tests:** Latency, throughput, KB size analysis  
**Expected:** Retrieval <500ms, Generation <15s

---

## 📊 Key Evaluation Metrics

### Retrieval Quality (Information Retrieval)
| Metric | Target | Meaning |
|--------|--------|---------|
| Precision@5 | ≥ 0.7 | Of top 5 results, 70% are relevant |
| Recall@5 | ≥ 0.6 | Of all relevant docs, 60% are found |
| MRR | ≥ 0.8 | First relevant result in top 2 |
| NDCG@5 | ≥ 0.75 | Ranking quality is good |

### Generation Quality (Manual Scoring)
| Metric | Target | How to Score |
|--------|--------|--------------|
| Relevance | 4+/5 | Does it answer the question? |
| Factuality | 4+/5 | Is it grounded in the KB? |
| Citation Coverage | ≥ 80% | Are claims attributed to sources? |
| Clarity | 4+/5 | Is it well-structured? |

### Performance (Automated)
| Metric | Target |
|--------|--------|
| Retrieval Latency | < 500ms avg |
| Generation Latency | < 15s avg |
| KB Size | > 100 chunks |

---

## 🚀 Fast Start (Copy & Paste)

### Sanity Check (1 minute)
```bash
python3 -c "from telecom_advisor_enhanced import collection; \
            print(f'✓ KB: {collection.count()} chunks')"
```

### Run All Tests (5-10 minutes)
```bash
python3 run_tests.py
```

### Run Individual Tests (1-2 minutes each)
```bash
python3 -m tests.test_knowledge_base
python3 -m tests.test_retrieval
python3 -m tests.test_integration
python3 -m tests.test_performance
```

### Manual Web UI Testing (15 minutes)
```bash
streamlit run streamlit_app.py
```

Then in browser (http://localhost:8501):
- **Chat Tab:** Ask a question → Verify citations
- **Compare Tab:** Compare 2 architectures
- **Upload Tab:** Upload a file
- **Analytics Tab:** View query history
- **Export Tab:** Export conversation

### CLI Testing (5 minutes)
```bash
python3 telecom_advisor_enhanced.py
```

Then type:
```
> compare Microservices vs Monolithic
> help
> analytics
> reload
> quit
```

---

## 📋 Recommended Testing Workflow

### Phase 1: Quick Check (1 minute)
✓ Verify Python, dependencies, API key, KB has content

### Phase 2: Automated Unit Tests (10 minutes)
✓ Run test_knowledge_base.py  
✓ Run test_retrieval.py  
✓ Run test_integration.py  
✓ Run test_performance.py  

### Phase 3: Manual Testing (15 minutes)
✓ Test Web UI: Chat, Compare, Upload, Analytics, Export  
✓ Test CLI: commands, reload, export  

### Phase 4: Document Results (5 minutes)
✓ Save test output  
✓ Document findings  
✓ Note any issues  

**Total: ~45 minutes**

---

## 📚 Documentation Files Summary

| File | Size | Purpose | Time |
|------|------|---------|------|
| TESTING_QUICK_START.md | 5.5 KB | Step-by-step guide | 5-10 min |
| TESTING_AND_EVALUATION.md | 23 KB | Complete framework | Deep dive |
| TESTING_ROADMAP.md | 7.4 KB | Visual + commands | 5 min |
| TESTING_SUMMARY.md | 7.7 KB | Results + workflow | 5 min |
| TESTING_INDEX.md | 5.8 KB | File structure | 5 min |

---

## ✅ What Tests to Run for Your Assignment

### Minimum (20 minutes)
1. Run sanity check
2. Run all tests: `python3 run_tests.py`
3. Manual test via Streamlit
4. Document results

### Recommended (45 minutes)
1. Run sanity check
2. Run each test module individually
3. Run performance benchmarks
4. Manual test via Streamlit + CLI
5. Score answers using rubric
6. Document everything

### Comprehensive (60+ minutes)
1. Everything above
2. Read TESTING_AND_EVALUATION.md
3. Create custom test queries
4. Analyze metrics deeply
5. Write detailed report

---

## 🎯 Next Steps

### Immediate (Now)
1. Choose a documentation file above based on your need
2. Run the quick start test: `python3 run_tests.py`
3. Review the results

### Short Term (Today)
1. Read TESTING_QUICK_START.md
2. Run all test modules
3. Test via Streamlit
4. Document results

### Long Term (For Assignment)
1. Reference TESTING_AND_EVALUATION.md for metrics
2. Run comprehensive evaluation
3. Score answers manually
4. Write detailed test report
5. Include results in assignment

---

## 📞 Quick Reference

**To test everything:**
```bash
python3 run_tests.py
```

**To test specific component:**
```bash
python3 -m tests.test_knowledge_base    # KB
python3 -m tests.test_retrieval          # Search
python3 -m tests.test_integration        # Workflows
python3 -m tests.test_performance        # Speed
```

**To test manually:**
```bash
streamlit run streamlit_app.py           # Web UI
python3 telecom_advisor_enhanced.py      # CLI
```

**To understand metrics:**
```bash
# Read:
- TESTING_AND_EVALUATION.md    (Retrieval metrics section)
- TESTING_ROADMAP.md           (Key Evaluation Metrics section)
```

---

## 🎓 Learning Path

If you want to **understand the concepts:**
1. Start: TESTING_QUICK_START.md (what to run)
2. Learn: TESTING_AND_EVALUATION.md (how things work)
3. Reference: TESTING_ROADMAP.md (commands)
4. Apply: Run tests and evaluate

If you want to **get started fast:**
1. Run: `python3 run_tests.py`
2. Read: TESTING_QUICK_START.md
3. Understand: Results vs expected values

If you want **everything documented:**
1. Read: TESTING_INDEX.md (overview)
2. Run: All test modules
3. Review: TESTING_SUMMARY.md (what was created)
4. Document: Your findings

---

## 💡 Key Insights

### Why These Metrics?
- **Retrieval metrics** measure if you're finding the right knowledge
- **Generation metrics** measure if answers are good quality
- **Performance metrics** measure if the system is fast
- **Manual scoring** captures nuances automated metrics miss

### Why Multiple Test Types?
- **Unit tests** verify individual components work
- **Integration tests** verify workflows work end-to-end
- **Performance tests** verify speed is acceptable
- **Manual tests** verify user experience is good

### Why Both Automated and Manual?
- **Automated** tests are fast, repeatable, objective
- **Manual** tests capture quality, context, user experience

---

## 🏁 Summary

You now have everything you need to:

✅ **Test** the application thoroughly  
✅ **Evaluate** quality with standard metrics  
✅ **Document** your findings  
✅ **Understand** what metrics mean  
✅ **Run** automated tests  
✅ **Manual test** via UI and CLI  

**Start with:** `TESTING_QUICK_START.md`  
**Run:** `python3 run_tests.py`  
**Understand:** `TESTING_AND_EVALUATION.md`  

Good luck! 🚀
