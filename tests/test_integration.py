"""
Integration tests for end-to-end workflows.
"""
import sys
import os
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telecom_advisor_enhanced import (
    get_architecture_advice_with_rag,
    compare_architectures,
    upload_text_file_to_knowledge_base,
    export_to_markdown,
    export_to_pdf,
    collection
)


def test_chat_workflow():
    """Test basic chat flow."""
    print("Testing chat workflow...")
    
    query = "What is a monolithic architecture?"
    answer, context, citations = get_architecture_advice_with_rag(query)
    
    assert answer and len(answer) > 50, f"Answer too short: {len(answer)} chars"
    assert citations and len(citations) > 0, f"No citations: {len(citations)}"
    
    print(f"✓ Chat workflow OK")
    print(f"  - Answer: {answer[:100]}...")
    print(f"  - Citations: {len(citations)}")


def test_compare_workflow():
    """Test architecture comparison."""
    print("Testing compare workflow...")
    
    arch1 = "Microservices"
    arch2 = "Monolithic"
    comparison = compare_architectures(arch1, arch2)
    
    assert comparison and len(comparison) > 50, f"Comparison too short: {len(comparison)}"
    
    # Check that both architectures are mentioned (case-insensitive)
    lower_comparison = comparison.lower()
    assert arch1.lower() in lower_comparison or "microservice" in lower_comparison, \
        "Microservices not mentioned in comparison"
    assert arch2.lower() in lower_comparison or "monolith" in lower_comparison, \
        "Monolithic not mentioned in comparison"
    
    print(f"✓ Compare workflow OK")
    print(f"  - Comparison length: {len(comparison)} chars")


def test_upload_workflow():
    """Test file upload and re-ingestion."""
    print("Testing upload workflow...")
    
    # Create a temp test file with front matter
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("---\ntopic: test\ndomain: testing\npriority: high\n---\n")
        f.write("Test knowledge content about telecom architecture systems.\n")
        f.write("This is additional test content to ensure proper chunking.")
        temp_path = f.name
    
    try:
        before_count = collection.count()
        upload_text_file_to_knowledge_base(temp_path)
        after_count = collection.count()
        
        added = after_count - before_count
        assert added > 0, f"No new chunks added (before={before_count}, after={after_count})"
        
        print(f"✓ Upload workflow OK")
        print(f"  - KB before: {before_count} chunks")
        print(f"  - KB after: {after_count} chunks")
        print(f"  - Added: {added} chunks")
    finally:
        os.remove(temp_path)


def test_export_markdown_workflow():
    """Test conversation export to Markdown."""
    print("Testing Markdown export workflow...")
    
    conversation = [
        {"role": "user", "content": "What is RAG?"},
        {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation, a technique that combines information retrieval with language models. [Source 1]"}
    ]
    
    md = export_to_markdown(conversation)
    
    assert md, "Markdown export is empty"
    assert "What is RAG?" in md, "User question not in export"
    assert "RAG is Retrieval-Augmented Generation" in md or "Retrieval" in md, "Answer not in export"
    
    print(f"✓ Markdown export workflow OK")
    print(f"  - Export length: {len(md)} chars")


def test_export_pdf_workflow():
    """Test conversation export to PDF."""
    print("Testing PDF export workflow...")
    
    conversation = [
        {"role": "user", "content": "What is microservices?"},
        {"role": "assistant", "content": "Microservices is an architectural style that structures applications as loosely coupled services. [Source 2]"}
    ]
    
    pdf_path = export_to_pdf(conversation)
    
    assert pdf_path, "PDF export returned no path"
    assert os.path.exists(pdf_path), f"PDF not created at {pdf_path}"
    
    file_size = os.path.getsize(pdf_path)
    assert file_size > 0, f"PDF file is empty (size={file_size})"
    
    print(f"✓ PDF export workflow OK")
    print(f"  - PDF path: {pdf_path}")
    print(f"  - PDF size: {file_size} bytes")


def run_all_integration_tests():
    """Run all integration tests."""
    print("=== Integration Tests ===\n")
    
    try:
        test_chat_workflow()
        print()
        test_compare_workflow()
        print()
        test_upload_workflow()
        print()
        test_export_markdown_workflow()
        print()
        test_export_pdf_workflow()
        
        print("\n" + "="*50)
        print("✓ All integration tests passed!")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
