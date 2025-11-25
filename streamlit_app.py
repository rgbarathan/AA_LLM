import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telecom_advisor_enhanced import (
    get_architecture_advice_with_rag,
    upload_pdf_to_knowledge_base,
    initialize_knowledge_base,
    compare_architectures,
    export_to_markdown,
    export_to_pdf,
    load_analytics,
    collection
)
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Telecom Architecture Advisor",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .citation-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .source-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'initialized' not in st.session_state:
    with st.spinner("Initializing knowledge base..."):
        initialize_knowledge_base()
    st.session_state.initialized = True

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Telecom+Advisor", use_container_width=True)
    
    st.markdown("### 🎯 Features")
    
    mode = st.radio(
        "Select Mode:",
        ["💬 Chat", "⚖️ Compare", "📤 Upload", "📊 Analytics", "💾 Export"]
    )
    
    st.markdown("---")
    
    # Knowledge base stats
    st.markdown("### 📚 Knowledge Base")
    kb_count = collection.count()
    st.metric("Total Chunks", kb_count)
    
    st.markdown("---")
    
    # Settings
    st.markdown("### ⚙️ Settings")
    use_rag = st.checkbox("Use RAG", value=True, help="Retrieve context from knowledge base")
    show_citations = st.checkbox("Show Citations", value=True, help="Display source references")
    
    st.markdown("---")
    
    st.markdown("### ℹ️ About")
    st.info("AI-powered telecom architecture advisor using RAG and Google Gemini")

# Main content
st.markdown('<div class="main-header">🏗️ Telecom Architecture Advisor</div>', unsafe_allow_html=True)

# Chat Mode
if mode == "💬 Chat":
    st.markdown("### Ask me anything about telecom architecture!")
    
    # Display conversation history
    for exchange in st.session_state.conversation:
        with st.chat_message("user"):
            st.write(exchange['user'])
        
        with st.chat_message("assistant"):
            st.write(exchange['assistant'])
            
            if show_citations and exchange.get('citations'):
                with st.expander("📚 View Sources"):
                    for cite in exchange['citations']:
                        st.markdown(f"""
                        <div class="citation-box">
                            <span class="source-badge">Source {cite['source_id']}</span>
                            <b>{cite['topic']}</b> ({cite['domain']}) - Relevance: {cite['relevance_score']:.2f}
                            <br/><small>{cite['text_preview']}</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, citations = get_architecture_advice_with_rag(
                    user_input,
                    use_rag=use_rag,
                    include_citations=show_citations,
                    conversation_context=st.session_state.conversation
                )
                
                st.write(response)
                
                if show_citations and citations:
                    with st.expander("📚 View Sources"):
                        for cite in citations:
                            # Gracefully handle missing relevance_score (new citation schema may not include it)
                            score = cite.get('relevance_score')
                            if isinstance(score, (int, float)):
                                score_text = f"{score:.2f}"
                            else:
                                score_text = "N/A"
                            st.markdown(
                                f"""
                                <div class="citation-box">
                                    <span class="source-badge">Source {cite.get('source_id','?')}</span>
                                    <b>{cite.get('topic','unknown')}</b> ({cite.get('domain','telecom')}) - Relevance: {score_text}
                                    <br/><small>{cite.get('text_preview','(no preview)')}</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        
        # Save to conversation
        st.session_state.conversation.append({
            'user': user_input,
            'assistant': response,
            'citations': citations,
            'timestamp': datetime.now().isoformat()
        })
        
        st.rerun()

# Compare Mode
elif mode == "⚖️ Compare":
    st.markdown("### Compare Architecture Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        arch1 = st.text_input("First Architecture", placeholder="e.g., Microservices")
    
    with col2:
        arch2 = st.text_input("Second Architecture", placeholder="e.g., Monolithic")
    
    context = st.text_input("Context", placeholder="e.g., telecom billing system", value="telecom systems")
    
    if st.button("🔄 Generate Comparison", type="primary"):
        if arch1 and arch2:
            with st.spinner("Generating comparison..."):
                comparison = compare_architectures(arch1, arch2, context)
                
                st.markdown("### 📊 Comparison Results")
                st.markdown(comparison)
                
                # Save to conversation
                st.session_state.conversation.append({
                    'user': f"Compare {arch1} vs {arch2} for {context}",
                    'assistant': comparison,
                    'citations': [],
                    'timestamp': datetime.now().isoformat()
                })
        else:
            st.warning("Please enter both architectures to compare")

# Upload Mode
elif mode == "📤 Upload":
    st.markdown("### Upload Documents to Knowledge Base")
    
    st.info("Upload PDF documents to expand the knowledge base. The system will automatically extract text and add it to the vector database.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Topic Tag", placeholder="e.g., 5g, billing, standards")
    with col2:
        domain = st.selectbox("Domain", ["architecture", "network", "compliance", "infrastructure", "services"])
    
    if uploaded_file is not None and st.button("📥 Upload to Knowledge Base", type="primary"):
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Processing PDF..."):
            chunks_added = upload_pdf_to_knowledge_base(temp_path, topic or "uploaded", domain)
        
        # Clean up
        os.remove(temp_path)
        
        if chunks_added > 0:
            st.success(f"✅ Successfully added {chunks_added} chunks from {uploaded_file.name}")
        else:
            st.error("❌ Failed to extract text from PDF")

# Analytics Mode
elif mode == "📊 Analytics":
    st.markdown("### Analytics Dashboard")
    
    analytics = load_analytics()
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Queries", analytics.get('total_queries', 0))
    
    with col2:
        st.metric("Unique Topics", len(analytics.get('topics', {})))
    
    with col3:
        st.metric("KB Chunks", collection.count())
    
    st.markdown("---")
    
    # Topic distribution
    if analytics.get('topics'):
        st.markdown("#### 📈 Topic Distribution")
        
        topics_data = analytics['topics']
        fig = go.Figure(data=[
            go.Bar(
                x=list(topics_data.keys()),
                y=list(topics_data.values()),
                marker_color='#1f77b4'
            )
        ])
        fig.update_layout(
            title="Queries by Topic",
            xaxis_title="Topic",
            yaxis_title="Number of Queries",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Pie chart
        fig2 = go.Figure(data=[
            go.Pie(
                labels=list(topics_data.keys()),
                values=list(topics_data.values()),
                hole=0.3
            )
        ])
        fig2.update_layout(title="Topic Distribution", height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Recent queries
    if analytics.get('queries'):
        st.markdown("#### 📝 Recent Queries")
        
        recent_queries = analytics['queries'][-10:][::-1]  # Last 10, reversed
        
        for idx, query in enumerate(recent_queries, 1):
            timestamp = datetime.fromisoformat(query['timestamp']).strftime('%Y-%m-%d %H:%M')
            with st.expander(f"{idx}. {query['query'][:80]}... - {timestamp}"):
                st.write(f"**Query:** {query['query']}")
                st.write(f"**Topics:** {', '.join(query.get('topics', []))}")
                st.write(f"**Time:** {timestamp}")

# Export Mode
elif mode == "💾 Export":
    st.markdown("### Export Conversation")
    
    if not st.session_state.conversation:
        st.warning("No conversation to export yet. Start chatting first!")
    else:
        st.info(f"Current conversation has {len(st.session_state.conversation)} exchanges")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as Markdown", type="primary"):
                filename = export_to_markdown(st.session_state.conversation)
                st.success(f"✅ Exported to {filename}")
                
                with open(filename, 'r') as f:
                    st.download_button(
                        label="⬇️ Download Markdown",
                        data=f.read(),
                        file_name=filename,
                        mime="text/markdown"
                    )
        
        with col2:
            if st.button("📕 Export as PDF", type="primary"):
                filename = export_to_pdf(st.session_state.conversation)
                st.success(f"✅ Exported to {filename}")
                
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=f.read(),
                        file_name=filename,
                        mime="application/pdf"
                    )
        
        st.markdown("---")
        
        st.markdown("#### 💬 Conversation Preview")
        for idx, exchange in enumerate(st.session_state.conversation, 1):
            with st.expander(f"Exchange {idx}: {exchange['user'][:60]}..."):
                st.markdown(f"**Question:** {exchange['user']}")
                st.markdown(f"**Answer:** {exchange['assistant']}")
                if exchange.get('citations'):
                    st.markdown(f"**Sources:** {len(exchange['citations'])} citations")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🏗️ Telecom Architecture Advisor | Powered by Google Gemini & RAG</p>
    <p><small>Built with Streamlit | ChromaDB | Sentence Transformers</small></p>
</div>
""", unsafe_allow_html=True)
