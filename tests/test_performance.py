"""
Performance benchmarking tests.
"""
import sys
import os
import time
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        "network",
        "design",
        "scalability",
        "distributed",
        "service",
    ] * (num_queries // 10 + 1)
    queries = queries[:num_queries]
    
    times = []
    for i, q in enumerate(queries):
        start = time.time()
        docs, metadata, scores = hybrid_search(q, n_results=5)
        elapsed = time.time() - start
        times.append(elapsed)
        
        if (i + 1) % max(1, num_queries // 10) == 0:
            print(f"  Completed {i + 1}/{num_queries} queries...")
    
    avg = sum(times) / len(times)
    p50 = sorted(times)[len(times) // 2]
    p95 = sorted(times)[int(0.95 * len(times))]
    p99 = sorted(times)[int(0.99 * len(times))]
    min_t = min(times)
    max_t = max(times)
    
    print(f"\n=== Retrieval Performance ===")
    print(f"Queries: {len(times)}")
    print(f"Min latency: {min_t*1000:.1f}ms")
    print(f"Avg latency: {avg*1000:.1f}ms")
    print(f"P50 latency: {p50*1000:.1f}ms")
    print(f"P95 latency: {p95*1000:.1f}ms")
    print(f"P99 latency: {p99*1000:.1f}ms")
    print(f"Max latency: {max_t*1000:.1f}ms")
    
    print(f"\nTargets:")
    print(f"  Avg < 500ms: {'✓' if avg < 0.5 else '✗'}")
    print(f"  P95 < 1000ms: {'✓' if p95 < 1.0 else '✗'}")
    
    return {"avg": avg, "p95": p95, "p99": p99}


def benchmark_generation(num_queries: int = 5):
    """Benchmark end-to-end answer generation."""
    print(f"\nBenchmarking generation with {num_queries} queries...")
    
    queries = [
        "What is the difference between monolithic and microservices architectures?",
        "Explain the key features of 5G network architecture.",
        "What are the main TM Forum standards for telecom service management?",
        "What is cloud-native design and how does it relate to microservices?",
        "Describe the benefits and challenges of distributed systems.",
    ][:num_queries]
    
    times = []
    responses = []
    
    for i, q in enumerate(queries):
        print(f"  Query {i+1}/{len(queries)}: {q[:50]}...")
        start = time.time()
        answer, context, citations = get_architecture_advice_with_rag(q)
        elapsed = time.time() - start
        times.append(elapsed)
        responses.append({"query": q, "answer_length": len(answer), "citations": len(citations)})
    
    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)
    
    print(f"\n=== Generation Performance ===")
    print(f"Queries: {len(times)}")
    print(f"Min latency: {min_t:.1f}s")
    print(f"Avg latency: {avg:.1f}s")
    print(f"Max latency: {max_t:.1f}s")
    
    print(f"\nResponse stats:")
    for resp in responses:
        print(f"  - {resp['query'][:40]}...")
        print(f"    Answer length: {resp['answer_length']} chars, Citations: {resp['citations']}")
    
    print(f"\nTargets:")
    print(f"  Avg < 15s: {'✓' if avg < 15 else '✗'}")
    
    return {"avg": avg, "min": min_t, "max": max_t}


def benchmark_kb_size():
    """Report knowledge base size and stats."""
    count = collection.count()
    
    print(f"\n=== Knowledge Base Stats ===")
    print(f"Total chunks: {count}")
    
    # Estimate docs
    avg_chunks_per_doc = 50  # typical estimate
    estimated_docs = max(1, count // avg_chunks_per_doc)
    print(f"Estimated documents (assume {avg_chunks_per_doc} chunks/doc): {estimated_docs}")
    
    return {"chunk_count": count}


def run_performance_benchmarks():
    """Run all performance tests."""
    print("=== Performance Benchmarks ===\n")
    
    try:
        kb_stats = benchmark_kb_size()
        retrieval_stats = benchmark_retrieval(num_queries=50)
        generation_stats = benchmark_generation(num_queries=3)
        
        print("\n" + "="*50)
        print("✓ All performance benchmarks completed!")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  KB: {kb_stats['chunk_count']} chunks")
        print(f"  Retrieval avg: {retrieval_stats['avg']*1000:.0f}ms")
        print(f"  Generation avg: {generation_stats['avg']:.1f}s")
        
        return True
    except Exception as e:
        print(f"\n✗ Benchmark error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_performance_benchmarks()
    sys.exit(0 if success else 1)
