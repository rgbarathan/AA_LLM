import requests
import chromadb
from chromadb.utils import embedding_functions
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import PyPDF2
from rank_bm25 import BM25Okapi
import re
import docx  # python-docx for Word documents
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telecom_advisor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
MIN_RETRY_WAIT = 1  # seconds
MAX_RETRY_WAIT = 10  # seconds

# Configuration constants
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
MIN_RETRY_WAIT = 1  # seconds
MAX_RETRY_WAIT = 10  # seconds

# ChromaDB collection initialization (copied from telecom_advisor_rag.py)
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = chroma_client.get_or_create_collection(
        name="telecom_knowledge",
        embedding_function=embedding_function
    )
    logger.info("ChromaDB initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB: {e}")
    raise

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    error_msg = "GEMINI_API_KEY not found in environment variables. Please create a .env file with your Gemini API key."
    logger.error(error_msg)
    raise ValueError(error_msg)
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
logger.info("Gemini API configured successfully")


# Retry decorator for API calls
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=MIN_RETRY_WAIT, max=MAX_RETRY_WAIT),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def call_gemini_api(prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> Dict:
    """
    Call Gemini API with retry logic and error handling.
    
    Args:
        prompt: The prompt to send to Gemini
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in response
        
    Returns:
        JSON response from Gemini API
        
    Raises:
        requests.exceptions.RequestException: For API call failures
    """
    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        logger.debug(f"Calling Gemini API with prompt length: {len(prompt)}")
        response = requests.post(
            API_URL, 
            headers=headers, 
            json=data, 
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info("Gemini API call successful")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Gemini API request timed out after {REQUEST_TIMEOUT} seconds")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini API HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API request failed: {e}")
        raise

def get_architecture_advice_with_rag(
    prompt: str,
    use_rag: bool = True,
    include_citations: bool = True,
    conversation_context: List[Dict] = None
) -> Tuple[str, List[Dict]]:
    """
    Get architecture advice using RAG with citations and conversation history.
    Uses Google Gemini API for LLM responses.
    """
    citations = []

    # Build conversation history
    conversation_prompt = ""
    if conversation_context:
        conversation_prompt = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in conversation_context[-3:]:  # Last 3 exchanges
            conversation_prompt += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n"

    # Retrieve relevant context if using RAG
    if use_rag:
        context, citations = retrieve_context_with_citations(prompt)
        if context:
            full_prompt = f"""You are an expert telecom architect. Use the following knowledge base context to answer the question accurately.

CONTEXT FROM KNOWLEDGE BASE:
{context}
{conversation_prompt}

USER QUESTION:
{prompt}

Provide a detailed, accurate answer based on the context provided. Reference sources using [Source N] notation when applicable."""
        else:
            full_prompt = f"You are an expert telecom architect.{conversation_prompt}\n\n{prompt}"
    else:
        full_prompt = f"You are an expert telecom architect.{conversation_prompt}\n\n{prompt}"

    # Call Google Gemini API with retry logic
    try:
        logger.info(f"Processing query: {prompt[:100]}...")
        result = call_gemini_api(full_prompt)
        
        # Handle Gemini response structure
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                answer = candidate["content"]["parts"][0]["text"]
                logger.info("Successfully generated response")
            else:
                error_msg = "Unexpected response structure from Gemini API"
                logger.error(f"{error_msg}: {result}")
                answer = f"Error: {error_msg}. Please try again."
        else:
            error_msg = "No candidates in Gemini API response"
            logger.warning(f"{error_msg}: {result}")
            answer = f"Error: {error_msg}. The API may have filtered the content. Please try rephrasing your question."

        # Log query for analytics
        topics = [c['topic'] for c in citations] if citations else []
        log_query(prompt, topics)
        return answer, citations
        
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {REQUEST_TIMEOUT} seconds. The service may be experiencing high load."
        logger.error(error_msg)
        return f"⚠️ {error_msg} Please try again in a moment.", citations
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"API error occurred: {e.response.status_code}"
        logger.error(f"{error_msg} - {e.response.text}")
        return f"⚠️ {error_msg}. Please check your API key and try again.", citations
        
    except requests.exceptions.RequestException as e:
        error_msg = "Network error occurred"
        logger.error(f"{error_msg}: {e}")
        return f"⚠️ {error_msg}. Please check your internet connection and try again.", citations
        
    except Exception as e:
        error_msg = "Unexpected error occurred"
        logger.exception(f"{error_msg}: {e}")
        return f"⚠️ {error_msg}: {str(e)}. Please contact support if this persists.", citations


# --- Minimal retrieve_context_with_citations implementation ---
def retrieve_context_with_citations(query: str, n_results: int = 3) -> Tuple[str, List[Dict]]:
    """
    Hybrid retrieve context with citation scoring.
    
    Uses hybrid_search to combine semantic embedding similarity and keyword BM25 scores.
    Produces a unified context string and structured citations including relevance scores.
    
    Args:
        query: User query text
        n_results: Number of chunks to return
    Returns:
        (context, citations)
        context: Concatenated text with source markers
        citations: List of dicts containing source metadata and relevance_score
    """
    try:
        logger.debug(f"Hybrid retrieving context for query: {query[:120]}...")
        docs, metadatas, scores = hybrid_search(query, n_results=n_results)
        if not docs:
            logger.info("Hybrid search returned no documents")
            return "", []

        # Normalize scores (simple max normalization) for display if mixed scales appear later
        max_score = max(scores) if scores else 1.0
        norm_scores = [s / max_score if max_score else 0.0 for s in scores]

        context_parts = []
        citations: List[Dict] = []
        for idx, (doc, meta, raw_score, norm_score) in enumerate(zip(docs, metadatas, scores, norm_scores), 1):
            context_parts.append(f"[Source {idx}] {doc}")
            citations.append({
                "source_id": idx,
                "topic": meta.get('topic', 'general'),
                "domain": meta.get('domain', 'telecom'),
                "relevance_score": round(norm_score, 4),
                "raw_score": round(raw_score, 4),
                "doc_id": meta.get('doc_id'),
                "chunk_index": meta.get('chunk_index'),
                "text_preview": (doc[:140] + "...") if len(doc) > 140 else doc
            })

        context = "\n\n".join(context_parts)
        logger.info(f"Hybrid search assembled {len(citations)} citations")
        return context, citations
    except Exception as e:
        logger.exception(f"Failed hybrid retrieval: {e}")
        return "", []


# --- Analytics Functions ---
def log_query(query: str, topics: List[str]) -> None:
    """
    Append a query and its topics to analytics.json with error handling.
    
    Args:
        query: User query
        topics: List of topics extracted from the query
    """
    analytics_file = "analytics.json"
    try:
        if os.path.exists(analytics_file):
            with open(analytics_file, "r") as f:
                analytics = json.load(f)
        else:
            analytics = {"queries": [], "topics": {}, "total_queries": 0}

        # Add query
        analytics["queries"].append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "topics": topics
        })
        # Update topic counts
        for topic in topics:
            analytics["topics"][topic] = analytics["topics"].get(topic, 0) + 1
        analytics["total_queries"] = analytics.get("total_queries", 0) + 1

        with open(analytics_file, "w") as f:
            json.dump(analytics, f, indent=2)
        logger.debug(f"Query logged to analytics: {query[:50]}...")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analytics file: {e}")
    except IOError as e:
        logger.error(f"Failed to write to analytics file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error logging query: {e}")

def load_analytics() -> Dict:
    """
    Load analytics summary from analytics.json with error handling.
    
    Returns:
        Dictionary containing analytics data
    """
    analytics_file = "analytics.json"
    default_analytics = {"queries": [], "topics": {}, "total_queries": 0}
    
    if not os.path.exists(analytics_file):
        logger.info("Analytics file does not exist, returning default analytics")
        return default_analytics
        
    try:
        with open(analytics_file, "r") as f:
            analytics = json.load(f)
        logger.debug("Analytics loaded successfully")
        return analytics
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse analytics file: {e}")
        return default_analytics
    except IOError as e:
        logger.error(f"Failed to read analytics file: {e}")
        return default_analytics
    except Exception as e:
        logger.error(f"Unexpected error loading analytics: {e}")
        return {"queries": [], "topics": {}, "total_queries": 0}



def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into smaller chunks for better retrieval."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def add_knowledge_to_db(documents: List[str], metadata_list: List[Dict] = None):
    """
    Add knowledge documents to the vector database.
    
    Args:
        documents: List of text documents
        metadata_list: Optional list of metadata dicts for each document
    """
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for idx, doc in enumerate(documents):
        chunks = chunk_text(doc)
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_id = f"doc_{idx}_chunk_{chunk_idx}_{datetime.now().timestamp()}"
            all_ids.append(chunk_id)
            
            # Add metadata
            metadata = metadata_list[idx] if metadata_list else {}
            metadata['chunk_index'] = chunk_idx
            metadata['doc_id'] = idx
            all_metadata.append(metadata)
    
    # Add to collection
    if all_chunks:
        collection.add(
            documents=all_chunks,
            metadatas=all_metadata,
            ids=all_ids
        )
        print(f"✓ Added {len(all_chunks)} chunks to knowledge base")
        return len(all_chunks)
    return 0


def hybrid_search(query: str, n_results: int = 5) -> Tuple[List[str], List[Dict], List[float]]:
    """
    Perform hybrid search combining semantic and keyword-based search.
    
    Args:
        query: User's question
        n_results: Number of results to retrieve
        
    Returns:
        Tuple of (documents, metadata, scores)
    """
    # Semantic search using ChromaDB
    semantic_results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Get all documents for BM25 keyword search
    all_docs = collection.get()
    
    if all_docs['documents']:
        # Tokenize documents for BM25
        tokenized_docs = [doc.lower().split() for doc in all_docs['documents']]
        bm25 = BM25Okapi(tokenized_docs)
        
        # Get BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Get top BM25 results
        top_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:n_results]
        
        # Combine results (semantic + keyword)
        combined_docs = []
        combined_metadata = []
        combined_scores = []
        
        # Add semantic results
        if semantic_results['documents'] and semantic_results['documents'][0]:
            for doc, meta in zip(semantic_results['documents'][0], semantic_results['metadatas'][0]):
                if doc not in combined_docs:
                    combined_docs.append(doc)
                    combined_metadata.append(meta)
                    combined_scores.append(0.7)  # Default semantic score
        
        # Add top BM25 results
        for idx in top_bm25_indices:
            doc = all_docs['documents'][idx]
            if doc not in combined_docs:
                combined_docs.append(doc)
                combined_metadata.append(all_docs['metadatas'][idx])
                combined_scores.append(0.3)  # Default keyword score
        
        return combined_docs[:n_results], combined_metadata[:n_results], combined_scores[:n_results]
    
    # Fallback to semantic only
    if semantic_results['documents'] and semantic_results['documents'][0]:
        return (semantic_results['documents'][0], 
                semantic_results['metadatas'][0], 
                [1.0] * len(semantic_results['documents'][0]))
    
    return [], [], []


def upload_pdf_to_knowledge_base(pdf_path: str, topic: str = "uploaded", domain: str = "telecom") -> int:
    """
    Upload a PDF document to the knowledge base.
    
    Args:
        pdf_path: Path to PDF file
        topic: Topic tag for the document
        domain: Domain tag for the document
        
    Returns:
        Number of chunks added
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if text.strip():
                metadata = [{"topic": topic, "domain": domain, "source": os.path.basename(pdf_path)}]
                chunks_added = add_knowledge_to_db([text], metadata)
                print(f"✓ Successfully added PDF: {os.path.basename(pdf_path)}")
                return chunks_added
            else:
                print(f"✗ No text found in PDF: {os.path.basename(pdf_path)}")
                return 0
    except Exception as e:
        print(f"✗ Error uploading PDF: {e}")
        return 0


def upload_word_doc_to_knowledge_base(doc_path: str, topic: str = "uploaded", domain: str = "telecom") -> int:
    """
    Upload a Word document (.docx) to the knowledge base.
    
    Args:
        doc_path: Path to Word document
        topic: Topic tag for the document
        domain: Domain tag for the document
        
    Returns:
        Number of chunks added
    """
    try:
        doc = docx.Document(doc_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        if text.strip():
            metadata = [{"topic": topic, "domain": domain, "source": os.path.basename(doc_path)}]
            chunks_added = add_knowledge_to_db([text], metadata)
            print(f"✓ Successfully added Word document: {os.path.basename(doc_path)}")
            return chunks_added
        else:
            print(f"✗ No text found in document: {os.path.basename(doc_path)}")
            return 0
    except Exception as e:
        print(f"✗ Error uploading Word document: {e}")
        return 0


def upload_text_file_to_knowledge_base(file_path: str, topic: str = "uploaded", domain: str = "telecom") -> int:
    """
    Upload a text file (.txt, .md) to the knowledge base.
    
    Args:
        file_path: Path to text file
        topic: Topic tag for the document
        domain: Domain tag for the document
        
    Returns:
        Number of chunks added
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if text.strip():
            metadata = [{"topic": topic, "domain": domain, "source": os.path.basename(file_path)}]
            chunks_added = add_knowledge_to_db([text], metadata)
            print(f"✓ Successfully added text file: {os.path.basename(file_path)}")
            return chunks_added
        else:
            print(f"✗ No text found in file: {os.path.basename(file_path)}")
            return 0
    except Exception as e:
        print(f"✗ Error uploading text file: {e}")
        return 0


def upload_multiple_files(file_paths: List[str], topic: str = "batch", domain: str = "telecom") -> int:
    """
    Upload multiple files at once to the knowledge base.
    Supports PDF, Word, and text files.
    
    Args:
        file_paths: List of file paths
        topic: Topic tag for all files
        domain: Domain tag for all files
        
    Returns:
        Total number of chunks added
    """
    total_chunks = 0
    supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
    
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            total_chunks += upload_pdf_to_knowledge_base(file_path, topic, domain)
        elif ext == '.docx':
            total_chunks += upload_word_doc_to_knowledge_base(file_path, topic, domain)
        elif ext in {'.txt', '.md'}:
            total_chunks += upload_text_file_to_knowledge_base(file_path, topic, domain)
        else:
            print(f"⚠ Skipping unsupported file type: {file_path}")
            print(f"  Supported: {', '.join(supported_extensions)}")
    
    print(f"\n✓ Batch upload complete: {total_chunks} total chunks added from {len(file_paths)} files")
    return total_chunks


def upload_directory(directory_path: str, topic: str = "batch", domain: str = "telecom", 
                    recursive: bool = True) -> int:
    """
    Upload all supported documents from a directory to the knowledge base.
    
    Args:
        directory_path: Path to directory
        topic: Topic tag for all files
        domain: Domain tag for all files
        recursive: Whether to search subdirectories
        
    Returns:
        Total number of chunks added
    """
    supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
    file_paths = []
    
    if recursive:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if os.path.splitext(file)[1].lower() in supported_extensions:
                    file_paths.append(os.path.join(root, file))
    else:
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in supported_extensions:
                file_paths.append(file_path)
    
    if file_paths:
        print(f"Found {len(file_paths)} supported files in {directory_path}")
        return upload_multiple_files(file_paths, topic, domain)
    else:
        print(f"✗ No supported files found in {directory_path}")
        return 0


def compare_architectures(arch1: str, arch2: str, context: str) -> str:
    """
    Generate a detailed side-by-side comparison of two architectures.
    
    Args:
        arch1: First architecture
        arch2: Second architecture
        context: Context for comparison (e.g., "telecom billing")
        
    Returns:
        Formatted comparison
    """
    query = f"""Create a detailed side-by-side comparison table of {arch1} vs {arch2} for {context}.

Include the following aspects:
1. Scalability
2. Performance
3. Complexity
4. Cost
5. Deployment
6. Maintenance
7. Best Use Cases
8. Limitations

Format as a clear comparison table."""
    
    response, _ = get_architecture_advice_with_rag(query, use_rag=True)
    return response


def export_to_markdown(conversation: List[Dict], filename: str = None):
    """Export conversation to markdown file."""
    if filename is None:
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, 'w') as f:
        f.write(f"# Telecom Architecture Advisor - Conversation\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for idx, exchange in enumerate(conversation, 1):
            f.write(f"## Query {idx}\n\n")
            f.write(f"**Question:** {exchange['user']}\n\n")
            f.write(f"**Answer:**\n\n{exchange['assistant']}\n\n")
            
            if exchange.get('citations'):
                f.write(f"**Sources:**\n\n")
                for cite in exchange['citations']:
                    f.write(f"- Source {cite['source_id']}: {cite['topic']} ({cite['domain']})\n")
                f.write("\n")
            
            f.write("---\n\n")
    
    print(f"✓ Exported to {filename}")
    return filename


def export_to_pdf(conversation: List[Dict], filename: str = None):
    """Export conversation to PDF file."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    if filename is None:
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30
    )
    story.append(Paragraph("Telecom Architecture Advisor", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Conversation
    for idx, exchange in enumerate(conversation, 1):
        story.append(Paragraph(f"<b>Query {idx}</b>", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"<b>Question:</b> {exchange['user']}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Clean and format answer
        answer_text = exchange['assistant'].replace('\n', '<br/>')
        story.append(Paragraph(f"<b>Answer:</b><br/>{answer_text}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        if idx < len(conversation):
            story.append(PageBreak())
    
    doc.build(story)
    print(f"✓ Exported to {filename}")
    return filename


def show_analytics():
    """Display analytics dashboard."""
    analytics = load_analytics()
    
    print("\n" + "="*70)
    print("📊 ANALYTICS DASHBOARD")
    print("="*70)
    
    print(f"\n📈 Total Queries: {analytics['total_queries']}")
    
    if analytics['topics']:
        print(f"\n🏷️  Most Popular Topics:")
        sorted_topics = sorted(analytics['topics'].items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:5]:
            print(f"   - {topic}: {count} queries")
    
    if analytics['queries']:
        print(f"\n📝 Recent Queries:")
        for query in analytics['queries'][-5:]:
            timestamp = datetime.fromisoformat(query['timestamp']).strftime('%Y-%m-%d %H:%M')
            print(f"   [{timestamp}] {query['query'][:60]}...")
    
    print("\n" + "="*70 + "\n")


def interactive_cli():
    """Interactive command-line interface."""
    print("\n" + "="*70)
    print("🎯 TELECOM ARCHITECTURE ADVISOR - Interactive Mode")
    print("="*70)
    print("\nCommands:")
    print("  'compare <arch1> vs <arch2>' - Compare two architectures")
    print("  'upload <pdf_path>'          - Upload PDF to knowledge base")
    print("  'export md'                  - Export conversation to markdown")
    print("  'export pdf'                 - Export conversation to PDF")
    print("  'analytics'                  - Show analytics dashboard")
    print("  'help'                       - Show this help message")
    print("  'quit' or 'exit'             - Exit the program")
    print("\n" + "="*70 + "\n")
    
    conversation = []
    
    while True:
        try:
            user_input = input("\n💬 Your Question: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using Telecom Architecture Advisor!")
                break
            
            if user_input.lower() == 'help':
                print("\nCommands:")
                print("  'compare <arch1> vs <arch2>' - Compare architectures")
                print("  'upload <pdf_path>'          - Upload PDF")
                print("  'export md'                  - Export to markdown")
                print("  'export pdf'                 - Export to PDF")
                print("  'analytics'                  - Show analytics")
                print("  'quit' or 'exit'             - Exit")
                continue
            
            if user_input.lower() == 'analytics':
                show_analytics()
                continue
            
            if user_input.lower().startswith('upload '):
                pdf_path = user_input[7:].strip()
                chunks = upload_pdf_to_knowledge_base(pdf_path)
                if chunks > 0:
                    print(f"✓ Added {chunks} chunks from PDF")
                continue
            
            if user_input.lower().startswith('compare '):
                match = re.match(r'compare\s+(.+?)\s+vs\s+(.+?)(?:\s+for\s+(.+))?$', user_input, re.IGNORECASE)
                if match:
                    arch1, arch2, context = match.groups()
                    context = context or "telecom systems"
                    print(f"\n⚙️  Generating comparison...\n")
                    response = compare_architectures(arch1.strip(), arch2.strip(), context.strip())
                    print(f"\n📊 {response}\n")
                else:
                    print("Usage: compare <arch1> vs <arch2> [for <context>]")
                continue
            
            if user_input.lower() in ['export md', 'export markdown']:
                if conversation:
                    filename = export_to_markdown(conversation)
                else:
                    print("No conversation to export yet.")
                continue
            
            if user_input.lower() == 'export pdf':
                if conversation:
                    filename = export_to_pdf(conversation)
                else:
                    print("No conversation to export yet.")
                continue
            
            # Regular query
            print("\n⚙️  Processing your question...\n")
            response, citations = get_architecture_advice_with_rag(
                user_input, 
                use_rag=True,
                conversation_context=conversation
            )
            
            print(f"🤖 Answer:\n{response}\n")
            
            if citations:
                print(f"📚 Sources Used:")
                for cite in citations:
                    print(f"   [{cite['source_id']}] {cite['topic']} ({cite['domain']}) - Relevance: {cite['relevance_score']:.2f}")
                    print(f"       Preview: {cite['text_preview']}")
            
            # Save to conversation history
            conversation.append({
                "user": user_input,
                "assistant": response,
                "citations": citations,
                "timestamp": datetime.now().isoformat()
            })
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def load_external_sources_from_config():
    """
    Load external sources from knowledge_sources.json configuration file.
    This runs automatically on initialization to load local files and directories.
    """
    config_file = "knowledge_sources.json"
    
    if not os.path.exists(config_file):
        return 0
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        total_chunks = 0
        
        # Load local files
        for source in config.get('local_files', []):
            if source.get('enabled', False) and os.path.exists(source['path']):
                try:
                    ext = os.path.splitext(source['path'])[1].lower()
                    if ext == '.pdf':
                        chunks = upload_pdf_to_knowledge_base(
                            pdf_path=source['path'],
                            topic=source.get('topic', 'document'),
                            domain=source.get('domain', 'telecom')
                        )
                    elif ext == '.docx':
                        chunks = upload_word_doc_to_knowledge_base(
                            doc_path=source['path'],
                            topic=source.get('topic', 'document'),
                            domain=source.get('domain', 'telecom')
                        )
                    elif ext in ['.txt', '.md']:
                        chunks = upload_text_file_to_knowledge_base(
                            file_path=source['path'],
                            topic=source.get('topic', 'document'),
                            domain=source.get('domain', 'telecom')
                        )
                    else:
                        continue
                    total_chunks += chunks
                except Exception as e:
                    print(f"⚠️  Could not load {source['path']}: {e}")
        
        # Load directories
        for source in config.get('directories', []):
            if source.get('enabled', False) and os.path.isdir(source['path']):
                try:
                    chunks = upload_directory(
                        directory_path=source['path'],
                        topic=source.get('topic', 'directory'),
                        domain=source.get('domain', 'telecom'),
                        recursive=source.get('recursive', True)
                    )
                    total_chunks += chunks
                except Exception as e:
                    print(f"⚠️  Could not load {source['path']}: {e}")
        
        if total_chunks > 0:
            print(f"✓ Loaded {total_chunks} chunks from external sources")
        
        return total_chunks
        
    except Exception as e:
        print(f"⚠️  Error loading external sources: {e}")
        return 0


def initialize_knowledge_base():
    """Initialize the knowledge base with comprehensive telecom architecture documents."""
    
    # Check if knowledge base already has documents
    count = collection.count()
    if count > 10:  # More than initial docs means likely already initialized
        print(f"Knowledge base already contains {count} chunks. Skipping initialization.")
        # Still try to load external sources
        load_external_sources_from_config()
        return
    
    print("Initializing comprehensive knowledge base...")
    
    # Enhanced telecom architecture knowledge documents
    documents = [
        """
        Microservices Architecture for Telecom Billing Systems:
        Microservices architecture breaks down the billing system into smaller, independent services.
        Key benefits include:
        - Scalability: Individual services can be scaled independently based on load
        - Independent deployment: Update billing engine without affecting rating service
        - Technology flexibility: Use different technologies for different services
        - Fault isolation: Failure in one service doesn't crash the entire system
        - Team autonomy: Different teams can own different services
        
        Challenges:
        - Distributed system complexity: Network latency, service discovery
        - Data consistency: Managing transactions across multiple services
        - Monitoring and debugging: Requires sophisticated tools like distributed tracing
        - Orchestration overhead: Need for API gateways, service meshes
        - Testing complexity: Integration testing across services
        
        Best for: High-volume telecom billing with frequent updates and need for high availability
        Real-world examples: Netflix OSS, Uber's billing system, Amazon's service-oriented architecture
        """,
        
        """
        Monolithic Architecture for Telecom Billing Systems:
        Monolithic architecture builds the entire billing system as a single unified application.
        Key benefits:
        - Simplicity: Easier to develop, test, and deploy initially
        - Performance: No network overhead between components
        - Consistency: ACID transactions are straightforward
        - Easier debugging: Single codebase, simpler stack traces
        - Lower operational complexity: Single deployment unit
        
        Challenges:
        - Scaling limitations: Must scale the entire application, not individual components
        - Update complexity: Small changes require full system deployment
        - Technology lock-in: Difficult to adopt new technologies
        - Single point of failure: One bug can crash the entire system
        - Large codebase: Becomes harder to maintain over time
        
        Best for: Small to medium telecom operators with stable requirements
        Migration strategy: Can evolve to microservices using strangler fig pattern
        """,
        
        """
        TM Forum Standards for Telecom OSS/BSS:
        TM Forum (TeleManagement Forum) provides industry standards for OSS/BSS systems.
        
        Key frameworks:
        - Open Digital Architecture (ODA): Component-based architecture framework for digital transformation
        - Application Framework (TAM): Technical architecture model defining application layers
        - Information Framework (SID): Shared information/data model for consistent data across systems
        - Integration Framework (eTOM): Business process framework for operations and management
        
        Open APIs (TMF APIs):
        - TMF620: Product Catalog Management - manage product offerings
        - TMF637: Product Inventory Management - track provisioned products
        - TMF678: Customer Bill Management - billing and invoicing
        - TMF622: Product Ordering - order capture and fulfillment
        - TMF632: Party Management - customer and partner information
        - TMF666: Account Management - customer accounts
        - TMF674: Geographic Site Management - location data
        
        Benefits of compliance:
        - Interoperability between vendor solutions
        - Reduced integration costs (up to 40% savings)
        - Faster time-to-market for new services
        - Vendor independence and reduced lock-in
        - Industry-proven best practices
        """,
        
        """
        High Availability Requirements for Telecom Systems:
        Telecom billing and OSS systems typically require 99.99% or higher availability (four nines = 52 minutes downtime/year).
        
        Key strategies:
        - Redundancy: Active-active or active-passive configurations across data centers
        - Load balancing: Distribute traffic using DNS, hardware, or software load balancers
        - Database replication: Multi-master for write scaling, master-slave for read scaling
        - Geographic distribution: Multiple data centers for disaster recovery (RPO/RTO < 1 hour)
        - Health checks: Automated monitoring with Prometheus, Grafana, Nagios
        - Circuit breakers: Prevent cascade failures using Hystrix, Resilience4j
        - Chaos engineering: Netflix Chaos Monkey for testing resilience
        
        Latency requirements:
        - Real-time charging: <50ms response time (P95)
        - API calls: <200ms for synchronous operations
        - Batch billing: Process within maintenance windows (typically 2-4 hours)
        - Mediation: Near real-time processing (<5 minutes)
        
        SLA targets:
        - 99.999% (five nines) for critical charging systems
        - 99.99% for billing and customer management
        - 99.9% for reporting and analytics
        
        Monitoring metrics: Error rate, latency, saturation, traffic (Google's Four Golden Signals)
        """,
        
        """
        Cloud-Native Architecture for Telecom:
        Cloud-native telecom systems leverage containerization, orchestration, and cloud services.
        
        Key components:
        - Containers: Docker for packaging applications with dependencies
        - Orchestration: Kubernetes for container lifecycle management, auto-scaling
        - Service mesh: Istio or Linkerd for service-to-service communication, security, observability
        - CI/CD: Jenkins, GitLab CI, ArgoCD for automated deployment pipelines
        - Observability: Prometheus for metrics, Jaeger for tracing, ELK/EFK for logging
        - Infrastructure as Code: Terraform, Ansible for reproducible infrastructure
        
        Benefits:
        - Auto-scaling based on demand (horizontal pod autoscaling)
        - Rolling updates with zero downtime
        - Multi-cloud portability (avoid vendor lock-in)
        - Cost optimization through resource efficiency (right-sizing)
        - Faster recovery from failures (self-healing)
        
        Considerations for telecom:
        - Data residency and compliance (GDPR, data sovereignty)
        - Network function virtualization (NFV) integration
        - 5G core network compatibility (SBA - Service-Based Architecture)
        - Edge computing for low latency (MEC - Multi-access Edge Computing)
        - Security: Zero-trust networking, mutual TLS, policy enforcement
        
        Adoption path: Lift-and-shift → Re-platform → Re-architect (cloud-native)
        """,
        
        """
        5G Architecture and Network Slicing:
        5G networks introduce Service-Based Architecture (SBA) with cloud-native principles.
        
        Core components:
        - AMF (Access and Mobility Management): Connection and mobility management
        - SMF (Session Management): Session establishment and management
        - UPF (User Plane Function): Packet routing and forwarding
        - PCF (Policy Control): Policy and charging control
        - UDM (Unified Data Management): Subscription and authentication data
        - AUSF (Authentication Server): Authentication services
        
        Network Slicing:
        - eMBB (Enhanced Mobile Broadband): High bandwidth for video streaming
        - URLLC (Ultra-Reliable Low-Latency): Critical applications (autonomous vehicles)
        - mMTC (Massive Machine-Type Communications): IoT devices
        
        Charging considerations:
        - Real-time charging per slice
        - Dynamic pricing based on QoS
        - Converged charging (online + offline)
        - Usage-based and subscription models
        
        Integration with BSS:
        - TMF654 Prepay Balance Management
        - TMF635 Usage Management
        - Real-time policy control via PCF
        """,
        
        """
        NFV (Network Functions Virtualization) and SDN (Software-Defined Networking):
        
        NFV Overview:
        - Virtualizes network functions traditionally on dedicated hardware
        - VNF (Virtual Network Function): Software implementation of network function
        - NFVI (NFV Infrastructure): Hardware and software for hosting VNFs
        - MANO (Management and Orchestration): Lifecycle management
        
        Benefits:
        - Reduced CAPEX: Use commodity hardware
        - Faster service deployment: Minutes vs months
        - Scalability: Scale functions independently
        - Multi-tenancy: Share infrastructure across services
        
        SDN Overview:
        - Separates control plane from data plane
        - Centralized network intelligence
        - Programmable network infrastructure
        - OpenFlow protocol for switch control
        
        OSS/BSS Integration:
        - Service orchestration across virtual and physical resources
        - Dynamic resource allocation based on demand
        - Automated provisioning and configuration
        - Unified inventory management (TMF637)
        - Cost allocation and showback/chargeback
        
        Challenges:
        - Performance overhead of virtualization
        - Complex orchestration
        - Security in multi-tenant environments
        """,
        
        """
        Edge Computing and MEC (Multi-access Edge Computing):
        Edge computing brings computation closer to data sources for reduced latency.
        
        MEC Architecture:
        - Edge nodes at base stations or aggregation points
        - Local content caching and CDN
        - Application hosting at the edge
        - Integration with 5G network slicing
        
        Use cases in telecom:
        - AR/VR applications requiring <10ms latency
        - Real-time video analytics
        - IoT data processing
        - Local breakout for enterprise applications
        - Gaming and interactive media
        
        Billing and charging:
        - Edge-based micro-charging
        - Location-based pricing
        - QoS-based charging
        - Integration with central BSS
        
        Architecture considerations:
        - Distributed databases (Cassandra, CockroachDB)
        - Edge orchestration (KubeEdge, AWS Wavelength)
        - Data synchronization with central systems
        - Security at the edge
        - Offline operation capability
        
        Economic model:
        - Reduced bandwidth costs
        - Improved user experience (lower latency)
        - New revenue streams (edge services)
        """,
        
        """
        IoT Billing and Device Management:
        Internet of Things creates unique billing challenges for telecom operators.
        
        IoT Characteristics:
        - Massive scale: Millions of devices per operator
        - Low ARPU: Average Revenue Per User is minimal
        - Diverse protocols: MQTT, CoAP, LwM2M
        - Long device lifecycle: 10+ years
        - Low power requirements: NB-IoT, LTE-M
        
        Billing models:
        - Per-device subscription
        - Usage-based (data consumed)
        - Tiered pricing by device class
        - Pooled data plans for device fleets
        - Event-based charging (messages, API calls)
        
        Device management (TMF639):
        - Remote provisioning
        - Firmware updates OTA (Over-The-Air)
        - Diagnostic and monitoring
        - Lifecycle management
        - SIM/eSIM management
        
        Architecture requirements:
        - Scalable mediation for high-volume events
        - Real-time aggregation and rating
        - Batch processing for non-critical billing
        - API-first architecture for device onboarding
        - Integration with IoT platforms (AWS IoT, Azure IoT Hub)
        
        Challenges:
        - Micropayment processing costs
        - Data volume management
        - Security and device authentication
        - Roaming and global connectivity
        """,
        
        """
        Event-Driven Architecture for Telecom BSS:
        Event-driven architecture enables real-time responsiveness and loose coupling.
        
        Core concepts:
        - Event producers: Network elements, applications, users
        - Event brokers: Kafka, RabbitMQ, AWS SNS/SQS
        - Event consumers: Billing, analytics, notifications
        - Event sourcing: Store all changes as events
        - CQRS: Separate read and write models
        
        Benefits for telecom:
        - Real-time charging and policy decisions
        - Asynchronous processing for scalability
        - Audit trail and compliance
        - Loose coupling between systems
        - Easy integration of new services
        
        Use cases:
        - Usage event processing from network
        - Real-time fraud detection
        - Customer notification triggers
        - Order orchestration
        - Inventory updates
        
        Implementation patterns:
        - Apache Kafka for high-throughput streaming
        - Schema registry for event contracts
        - Dead letter queues for error handling
        - Event replay for system recovery
        - Partitioning for scalability
        
        Challenges:
        - Event ordering and idempotency
        - Eventual consistency
        - Debugging distributed flows
        - Schema evolution
        - Exactly-once processing semantics
        
        Best practices:
        - Design events for business domains
        - Version events from the start
        - Monitor lag and throughput
        - Implement circuit breakers
        """
    ]
    
    metadata = [
        {"topic": "microservices", "domain": "architecture", "priority": "high"},
        {"topic": "monolithic", "domain": "architecture", "priority": "high"},
        {"topic": "standards", "domain": "compliance", "priority": "high"},
        {"topic": "high_availability", "domain": "infrastructure", "priority": "high"},
        {"topic": "cloud_native", "domain": "architecture", "priority": "high"},
        {"topic": "5g", "domain": "network", "priority": "medium"},
        {"topic": "nfv_sdn", "domain": "network", "priority": "medium"},
        {"topic": "edge_computing", "domain": "infrastructure", "priority": "medium"},
        {"topic": "iot", "domain": "services", "priority": "medium"},
        {"topic": "event_driven", "domain": "architecture", "priority": "medium"}
    ]
    
    add_knowledge_to_db(documents, metadata)
    print("✓ Comprehensive knowledge base initialized successfully!")
    
    # Load external sources from configuration
    print("\nLoading external sources from configuration...")
    load_external_sources_from_config()


if __name__ == "__main__":
    import sys
    import subprocess
    
    # Initialize knowledge base
    initialize_knowledge_base()
    
    # Launch Streamlit web interface
    print("\n" + "="*70)
    print("🚀 LAUNCHING WEB INTERFACE")
    print("="*70)
    print("\n📱 Starting Streamlit app...")
    print("   Opening browser at: http://localhost:8501")
    print("\n💡 To stop: Press Ctrl+C in this terminal")
    print("="*70 + "\n")
    
    try:
        # Run streamlit app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
    except FileNotFoundError:
        print("\n❌ Error: Streamlit not found!")
        print("   Install with: pip3 install streamlit")
        print("\n💡 Falling back to CLI mode...\n")
        interactive_cli()
