# Telecom Architecture Advisor - LLM with RAG

An intelligent telecom architecture advisor that uses **Retrieval-Augmented Generation (RAG)** to provide domain-aware recommendations for telecom systems design.

## 🎯 Overview

This project implements an LLM-based AI system that assists telecom architects and engineers in making informed design decisions. It combines:

- **Google Gemini 2.5 Flash** - State-of-the-art LLM for generating responses
- **ChromaDB** - Vector database for efficient semantic search
- **Sentence Transformers** - For creating embeddings from text
- **RAG Architecture** - Retrieves relevant context before generating responses

## 🏗️ Architecture

```
[User Query] → [Embed Query] → [Vector DB Search] → [Retrieve Context] 
    → [Construct Prompt] → [LLM API] → [Response]
```

**Knowledge Base Pipeline:**
```
External Knowledge Sources → [Chunk] → [Embed] → [Store in Vector DB]
```

## 🚀 Features

- **Natural Language Understanding**: Interprets complex telecom architecture queries
- **Context-Aware Responses**: Uses RAG to provide accurate, knowledge-based answers
- **Domain Expertise**: Pre-loaded with telecom architecture best practices
- **Scalable Knowledge Base**: Easy to add new documents and domain knowledge

## 📋 Key AI Tasks

1. **Comparative Analysis** - Compare different architecture patterns
2. **Requirements Summarization** - Extract key points from RFPs and specifications
3. **Contextual Recommendations** - Suggest solutions based on requirements
4. **Domain-Specific Q&A** - Answer telecom-specific technical questions

## 📦 Files

- `AA_LLM.py` - Basic LLM integration with Google Gemini
- `telecom_advisor_rag.py` - Full RAG implementation with vector database
- `chroma_db/` - Persistent vector database storage (created on first run)

## 🛠️ Setup

### Prerequisites

- Python 3.9+
- Google Gemini API key

### Installation

```bash
# Install required packages
pip install requests chromadb sentence-transformers langchain langchain-community PyPDF2
```

### Configuration

The Google Gemini API key is already configured in the code. For production use, consider using environment variables:

```python
API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
```

## 💻 Usage

### Run the RAG-enabled advisor:

```bash
python telecom_advisor_rag.py
```

This will:
1. Initialize the vector database with telecom knowledge
2. Run sample queries demonstrating RAG capabilities
3. Display responses with context-aware recommendations

### Example Queries:

```python
from telecom_advisor_rag import get_architecture_advice_with_rag

# Query with RAG
response = get_architecture_advice_with_rag(
    "Compare microservices and monolithic architecture for telecom billing.",
    use_rag=True
)
print(response)
```

## 📚 Knowledge Base

The system includes pre-loaded knowledge about:

- **Microservices Architecture** - Benefits, challenges, and use cases
- **Monolithic Architecture** - When to use and limitations
- **TM Forum Standards** - ODA, TAM, SID, eTOM frameworks and Open APIs
- **High Availability** - Redundancy, latency requirements, failover strategies
- **Cloud-Native Architecture** - Containers, orchestration, and cloud services

### Adding New Knowledge:

```python
from telecom_advisor_rag import add_knowledge_to_db

documents = ["Your new telecom knowledge document..."]
metadata = [{"topic": "5g", "domain": "network"}]

add_knowledge_to_db(documents, metadata)
```

## 🎯 Example Use Cases

### 1. Architecture Comparison
**Input:** "Compare microservices and monolithic architecture for telecom billing."

**Output:** Detailed comparison with scalability, deployment, complexity, and use case analysis.

### 2. Standards Compliance
**Input:** "What are the key TM Forum standards I should consider?"

**Output:** List of frameworks (ODA, TAM, SID, eTOM) and Open APIs with descriptions.

### 3. Performance Requirements
**Input:** "What latency requirements should I plan for real-time charging?"

**Output:** Specific latency targets (<50ms) with architectural strategies.

## 🔧 Technical Stack

- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: ChromaDB with persistent storage
- **Embeddings**: all-MiniLM-L6-v2 (SentenceTransformers)
- **Chunking**: 500-word chunks for optimal retrieval
- **Retrieval**: Top-3 most relevant chunks per query

## 📊 RAG Benefits

✅ **Accuracy**: Responses grounded in verified telecom knowledge  
✅ **Consistency**: Same questions get consistent answers  
✅ **Transparency**: Can trace answers back to source documents  
✅ **Updatable**: Easy to add new standards and best practices  
✅ **Domain-Specific**: Focused on telecom architecture patterns  

## 🔍 Testing & Evaluation

**Strengths:**
- Handles domain-specific terminology effectively
- Provides clear, structured recommendations
- Retrieves relevant context accurately

**Limitations:**
- Requires good quality source documents
- May need prompt engineering for edge cases
- Limited by knowledge base coverage

## 🚦 Future Enhancements

- [ ] Add more telecom standards and frameworks
- [ ] Implement document upload functionality
- [ ] Add support for PDF/Word document ingestion
- [ ] Create web interface for easier interaction
- [ ] Add conversation history and follow-up questions
- [ ] Implement hybrid search (keyword + semantic)
- [ ] Add citation tracking to show source documents

## 📝 Project Requirements

This project fulfills the assignment requirements for:
- ✅ LLM integration with external knowledge
- ✅ RAG implementation with vector database
- ✅ Natural language understanding
- ✅ Domain-specific AI tasks
- ✅ Comparative analysis and recommendations
- ✅ Working demo with sample queries

## 👨‍💻 Author

Developed as part of Drexel University coursework - Assignment 4

## 📄 License

Educational project - feel free to use and modify for learning purposes.
