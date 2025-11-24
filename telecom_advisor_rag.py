import requests
import chromadb
from chromadb.utils import embedding_functions
import os

# Google Gemini API Configuration
API_KEY = "AIzaSyCTCIjTodpzZ7KxFQgNtr_8qIwU7ppw3bs"
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# Initialize ChromaDB client and embedding function
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="telecom_knowledge",
    embedding_function=embedding_function
)


def chunk_text(text, chunk_size=500):
    """Split text into smaller chunks for better retrieval."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def add_knowledge_to_db(documents, metadata_list=None):
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
            chunk_id = f"doc_{idx}_chunk_{chunk_idx}"
            all_ids.append(chunk_id)
            
            # Add metadata
            metadata = metadata_list[idx] if metadata_list else {}
            metadata['chunk_index'] = chunk_idx
            all_metadata.append(metadata)
    
    # Add to collection
    if all_chunks:
        collection.add(
            documents=all_chunks,
            metadatas=all_metadata,
            ids=all_ids
        )
        print(f"✓ Added {len(all_chunks)} chunks to knowledge base")


def retrieve_context(query, n_results=3):
    """
    Retrieve relevant context from the vector database.
    
    Args:
        query: User's question
        n_results: Number of relevant chunks to retrieve
        
    Returns:
        Combined context string
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    if results['documents'] and results['documents'][0]:
        context_chunks = results['documents'][0]
        context = "\n\n".join(context_chunks)
        return context
    return ""


def get_architecture_advice_with_rag(prompt, use_rag=True):
    """
    Get architecture advice using RAG (Retrieval-Augmented Generation).
    
    Args:
        prompt: User's question
        use_rag: Whether to use RAG or just direct LLM
        
    Returns:
        LLM response
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    # Retrieve relevant context if using RAG
    if use_rag:
        context = retrieve_context(prompt)
        if context:
            full_prompt = f"""You are an expert telecom architect. Use the following knowledge base context to answer the question accurately.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION:
{prompt}

Provide a detailed, accurate answer based on the context provided. If the context doesn't contain enough information, acknowledge this and provide general guidance."""
        else:
            full_prompt = f"You are an expert telecom architect.\n\n{prompt}"
    else:
        full_prompt = f"You are an expert telecom architect.\n\n{prompt}"
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate:
                if "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
                elif "text" in candidate["content"]:
                    return candidate["content"]["text"]
        return f"Unexpected response structure: {result}"
    else:
        return f"Error: {response.status_code}, {response.text}"


def initialize_knowledge_base():
    """Initialize the knowledge base with telecom architecture documents."""
    
    # Check if knowledge base already has documents
    count = collection.count()
    if count > 0:
        print(f"Knowledge base already contains {count} chunks. Skipping initialization.")
        return
    
    # Telecom architecture knowledge documents
    documents = [
        """
        Microservices Architecture for Telecom Billing Systems:
        Microservices architecture breaks down the billing system into smaller, independent services.
        Key benefits include:
        - Scalability: Individual services can be scaled independently based on load
        - Independent deployment: Update billing engine without affecting rating service
        - Technology flexibility: Use different technologies for different services
        - Fault isolation: Failure in one service doesn't crash the entire system
        
        Challenges:
        - Distributed system complexity: Network latency, service discovery
        - Data consistency: Managing transactions across multiple services
        - Monitoring and debugging: Requires sophisticated tools like distributed tracing
        - Orchestration overhead: Need for API gateways, service meshes
        
        Best for: High-volume telecom billing with frequent updates and need for high availability
        """,
        
        """
        Monolithic Architecture for Telecom Billing Systems:
        Monolithic architecture builds the entire billing system as a single unified application.
        Key benefits:
        - Simplicity: Easier to develop, test, and deploy initially
        - Performance: No network overhead between components
        - Consistency: ACID transactions are straightforward
        - Easier debugging: Single codebase, simpler stack traces
        
        Challenges:
        - Scaling limitations: Must scale the entire application, not individual components
        - Update complexity: Small changes require full system deployment
        - Technology lock-in: Difficult to adopt new technologies
        - Single point of failure: One bug can crash the entire system
        
        Best for: Small to medium telecom operators with stable requirements
        """,
        
        """
        TM Forum Standards for Telecom OSS/BSS:
        TM Forum (TeleManagement Forum) provides industry standards for OSS/BSS systems.
        
        Key frameworks:
        - Open Digital Architecture (ODA): Component-based architecture framework
        - Application Framework (TAM): Technical architecture model
        - Information Framework (SID): Shared information/data model
        - Integration Framework (eTOM): Business process framework
        
        Open APIs:
        - TMF620: Product Catalog Management
        - TMF637: Product Inventory Management
        - TMF678: Customer Bill Management
        - TMF622: Product Ordering
        
        Compliance ensures interoperability, reduces vendor lock-in, and accelerates time-to-market.
        """,
        
        """
        High Availability Requirements for Telecom Systems:
        Telecom billing and OSS systems typically require 99.99% or higher availability (four nines).
        
        Key strategies:
        - Redundancy: Active-active or active-passive configurations
        - Load balancing: Distribute traffic across multiple instances
        - Database replication: Multi-master or master-slave configurations
        - Geographic distribution: Multiple data centers for disaster recovery
        - Health checks: Automated monitoring and failover mechanisms
        - Circuit breakers: Prevent cascade failures
        
        Latency requirements:
        - Real-time charging: <50ms response time
        - Batch billing: Process within maintenance windows
        - API calls: <200ms for synchronous operations
        """,
        
        """
        Cloud-Native Architecture for Telecom:
        Cloud-native telecom systems leverage containerization, orchestration, and cloud services.
        
        Key components:
        - Containers: Docker for packaging applications
        - Orchestration: Kubernetes for container management
        - Service mesh: Istio or Linkerd for service-to-service communication
        - CI/CD: Automated deployment pipelines
        - Observability: Prometheus, Grafana, ELK stack
        
        Benefits:
        - Auto-scaling based on demand
        - Rolling updates with zero downtime
        - Multi-cloud portability
        - Cost optimization through resource efficiency
        
        Considerations for telecom:
        - Data residency and compliance requirements
        - Network function virtualization (NFV) integration
        - 5G core network compatibility
        """
    ]
    
    metadata = [
        {"topic": "microservices", "domain": "architecture"},
        {"topic": "monolithic", "domain": "architecture"},
        {"topic": "standards", "domain": "compliance"},
        {"topic": "high_availability", "domain": "infrastructure"},
        {"topic": "cloud_native", "domain": "architecture"}
    ]
    
    add_knowledge_to_db(documents, metadata)
    print("✓ Knowledge base initialized successfully!")


if __name__ == "__main__":
    print("=" * 70)
    print("Telecom Architecture Advisor with RAG")
    print("=" * 70)
    
    # Initialize knowledge base
    initialize_knowledge_base()
    
    print("\n" + "=" * 70)
    print("Testing with sample queries...")
    print("=" * 70)
    
    # Test queries
    test_queries = [
        "Compare microservices and monolithic architecture for telecom billing.",
        "What are the key TM Forum standards I should consider?",
        "What latency requirements should I plan for real-time charging?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"QUERY: {query}")
        print(f"{'='*70}\n")
        
        response = get_architecture_advice_with_rag(query, use_rag=True)
        print(response)
        print()
