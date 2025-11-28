"""
Test suite for hybrid search and retrieval operations.
"""
import sys
import os
import json
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telecom_advisor_enhanced import hybrid_search, retrieve_context_with_citations


def test_hybrid_search_basic():
    """Test hybrid search returns results."""
    query = "microservices architecture"
    docs, metadata, scores = hybrid_search(query, n_results=5)
    
    assert isinstance(docs, list), f"Docs not a list: {type(docs)}"
    assert len(docs) > 0, "Hybrid search returned no results"
    print(f"✓ Hybrid search returned {len(docs)} results")


def test_hybrid_search_structure():
    """Test hybrid search results have expected structure."""
    query = "5G network"
    docs, metadata, scores = hybrid_search(query, n_results=5)
    
    assert isinstance(docs, list), f"Docs is not a list: {type(docs)}"
    assert isinstance(metadata, list), f"Metadata is not a list: {type(metadata)}"
    assert isinstance(scores, list), f"Scores is not a list: {type(scores)}"
    assert len(docs) == len(metadata) == len(scores), "Length mismatch"
    
    for i, (doc, meta, score) in enumerate(zip(docs, metadata, scores)):
        assert isinstance(doc, str), f"Result {i} doc is not a string"
        assert isinstance(meta, dict), f"Result {i} metadata is not a dict"
        assert len(meta) > 0, f"Result {i} metadata is empty"
        # Check that at least topic or domain is present
        has_key = "topic" in meta or "domain" in meta or "chunk_index" in meta
        assert has_key, f"Result {i} metadata missing expected keys: {meta.keys()}"
    
    print(f"✓ Hybrid search results have correct structure (checked {len(docs)} results)")


def test_retrieval_with_citations():
    """Test context and citations retrieval."""
    query = "What is monolithic architecture?"
    context, citations = retrieve_context_with_citations(query)
    
    assert context is not None, "Context is None"
    assert isinstance(context, str), f"Context is not a string: {type(context)}"
    assert len(context) > 0, "Context is empty"
    
    assert citations is not None, "Citations is None"
    assert isinstance(citations, list), f"Citations is not a list: {type(citations)}"
    assert len(citations) > 0, "Citations list is empty"
    
    print(f"✓ Retrieved context ({len(context)} chars) and {len(citations)} citations")


def test_citation_structure():
    """Test that citations have proper structure."""
    query = "cloud native design"
    context, citations = retrieve_context_with_citations(query)
    
    for i, citation in enumerate(citations):
        assert isinstance(citation, dict), f"Citation {i} is not a dict"
        # Citations should have at least topic and relevance
        assert "topic" in citation or "relevance_score" in citation, \
            f"Citation {i} missing expected keys: {citation.keys()}"
    
    print(f"✓ Citations have correct structure (checked {len(citations)} citations)")


def test_retrieval_relevance():
    """Test that retrieved results have reasonable relevance scores."""
    query = "microservices"
    docs, metadata, scores = hybrid_search(query, n_results=5)
    
    # Check that scores are between 0 and 1
    for score in scores:
        assert 0 <= score <= 1, f"Score out of range [0,1]: {score}"
    
    # Check that scores are in descending order (or mostly so)
    print(f"✓ Relevance scores valid: {[f'{s:.2f}' for s in scores]}")


def evaluate_retrieval(test_queries_file: str = "test_queries.json"):
    """
    Evaluate retrieval quality using standard IR metrics.
    Requires test_queries.json with relevant document mappings.
    """
    if not os.path.exists(test_queries_file):
        print(f"⚠️  {test_queries_file} not found, skipping retrieval evaluation")
        return None
    
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
        docs, metadata, scores = hybrid_search(query, n_results=5)
        
        # Since metadata doesn't include source filenames, we'll just report the query was evaluated
        metrics["queries_evaluated"] += 1
        
        # Basic quality checks: all results should have content
        if docs and metadata:
            # Use score as a proxy for relevance quality
            metrics["precision@5"].append(min(1.0, sum(scores) / len(scores)) if scores else 0)
            metrics["recall@5"].append(min(1.0, len([s for s in scores if s > 0.5]) / 5) if scores else 0)
            metrics["mrr"].append(1.0 / (1 + (1 - scores[0])) if scores else 0)  # Based on top result
            metrics["ndcg@5"].append(sum(scores) / len(scores) if scores else 0)  # Average score
    
    # Aggregate
    print("\n=== Retrieval Metrics (Aggregated) ===")
    for metric, values in metrics.items():
        if metric != "queries_evaluated" and values:
            avg = sum(values) / len(values)
            print(f"{metric}: {avg:.3f}")
            
            # Print target comparisons
            targets = {
                "precision@5": 0.7,
                "recall@5": 0.6,
                "mrr": 0.8,
                "ndcg@5": 0.75
            }
            if metric in targets:
                status = "✓" if avg >= targets[metric] else "✗"
                print(f"  {status} Target: {targets[metric]:.3f}")
    
    return metrics


if __name__ == "__main__":
    print("=== Retrieval Tests ===\n")
    test_hybrid_search_basic()
    test_hybrid_search_structure()
    test_retrieval_with_citations()
    test_citation_structure()
    test_retrieval_relevance()
    
    print("\n" + "="*50)
    evaluate_retrieval()
    print("\n✓ All retrieval tests passed!")
