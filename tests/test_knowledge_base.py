"""
Test suite for knowledge base initialization and operations.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    assert len(results["metadatas"]) > 0, "No metadata found"
    
    for meta in results["metadatas"]:
        # Check that metadata dict exists
        assert isinstance(meta, dict), f"Metadata is not a dict: {meta}"
        # At least one of these should be present
        has_metadata = "topic" in meta or "domain" in meta or "source" in meta
        assert has_metadata, f"Missing key metadata: {meta}"
    
    print(f"✓ Metadata present on chunks (checked {len(results['metadatas'])} samples)")


def test_kb_chunk_content():
    """Test that chunks have actual content."""
    results = collection.get(limit=10, include=["documents"])
    assert len(results["documents"]) > 0, "No documents found"
    
    for doc in results["documents"]:
        assert isinstance(doc, str), f"Document is not a string: {type(doc)}"
        assert len(doc) > 10, f"Document too short: {len(doc)} chars"
    
    print(f"✓ Chunks have content (checked {len(results['documents'])} samples)")


if __name__ == "__main__":
    print("=== Knowledge Base Tests ===\n")
    test_kb_init()
    test_kb_metadata()
    test_kb_chunk_content()
    print("\n✓ All knowledge base tests passed!")
