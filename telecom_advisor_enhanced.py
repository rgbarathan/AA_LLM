import requests
import chromadb
from chromadb.utils import embedding_functions
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
import PyPDF2
from rank_bm25 import BM25Okapi
import re

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

# Analytics storage
ANALYTICS_FILE = "analytics.json"
conversation_history = []


def load_analytics():
    """Load analytics data from file."""
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    return {"queries": [], "topics": {}, "total_queries": 0}


def save_analytics(analytics):
    """Save analytics data to file."""
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(analytics, f, indent=2)


def log_query(query: str, topics: List[str]):
    """Log query for analytics."""
    analytics = load_analytics()
    analytics["queries"].append({
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "topics": topics
    })
    analytics["total_queries"] += 1
    
    for topic in topics:
        analytics["topics"][topic] = analytics["topics"].get(topic, 0) + 1
    
    save_analytics(analytics)


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
                    combined_scores.append(1.0)  # Semantic match
        
        # Add top BM25 results
        for idx in top_bm25_indices[:3]:
            doc = all_docs['documents'][idx]
            if doc not in combined_docs:
                combined_docs.append(doc)
                combined_metadata.append(all_docs['metadatas'][idx])
                combined_scores.append(0.8)  # Keyword match
        
        return combined_docs[:n_results], combined_metadata[:n_results], combined_scores[:n_results]
    
    # Fallback to semantic only
    if semantic_results['documents'] and semantic_results['documents'][0]:
        return (semantic_results['documents'][0], 
                semantic_results['metadatas'][0], 
                [1.0] * len(semantic_results['documents'][0]))
    
    return [], [], []


def retrieve_context_with_citations(query: str, n_results: int = 3) -> Tuple[str, List[Dict]]:
    """
    Retrieve relevant context with citation information.
    
    Args:
        query: User's question
        n_results: Number of relevant chunks to retrieve
        
    Returns:
        Tuple of (context string, citations list)
    """
    docs, metadata, scores = hybrid_search(query, n_results)
    
    citations = []
    context_parts = []
    
    for idx, (doc, meta, score) in enumerate(zip(docs, metadata, scores), 1):
        context_parts.append(f"[Source {idx}]: {doc}")
        citations.append({
            "source_id": idx,
            "topic": meta.get('topic', 'general'),
            "domain": meta.get('domain', 'telecom'),
            "relevance_score": score,
            "text_preview": doc[:100] + "..." if len(doc) > 100 else doc
        })
    
    context = "\n\n".join(context_parts)
    return context, citations


def get_architecture_advice_with_rag(
    prompt: str, 
    use_rag: bool = True, 
    include_citations: bool = True,
    conversation_context: List[Dict] = None
) -> Tuple[str, List[Dict]]:
    """
    Get architecture advice using RAG with citations and conversation history.
    
    Args:
        prompt: User's question
        use_rag: Whether to use RAG
        include_citations: Whether to include citations
        conversation_context: Previous conversation messages
        
    Returns:
        Tuple of (response, citations)
    """
    headers = {
        "Content-Type": "application/json"
    }
    
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
                    answer = candidate["content"]["parts"][0]["text"]
                    
                    # Log query for analytics
                    topics = [cite.get('topic', 'general') for cite in citations]
                    log_query(prompt, topics)
                    
                    return answer, citations
                elif "text" in candidate["content"]:
                    return candidate["content"]["text"], citations
        return f"Unexpected response structure: {result}", []
    else:
        return f"Error: {response.status_code}, {response.text}", []


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


def initialize_knowledge_base():
    """Initialize the knowledge base with comprehensive telecom architecture documents."""
    
    # Check if knowledge base already has documents
    count = collection.count()
    if count > 10:  # More than initial docs means likely already initialized
        print(f"Knowledge base already contains {count} chunks. Skipping initialization.")
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


if __name__ == "__main__":
    # Initialize knowledge base
    initialize_knowledge_base()
    
    # Start interactive CLI
    interactive_cli()
