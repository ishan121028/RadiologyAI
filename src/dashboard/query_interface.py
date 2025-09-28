#!/usr/bin/env python3

"""
CriticalAlert AI - Simple Document Query Interface
Simple UI for querying radiology documents using RAG
"""

import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Configure Streamlit
st.set_page_config(
    page_title="🔍 CriticalAlert AI - Document Query",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class DocumentQueryInterface:
    """Simple interface for querying radiology documents"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:49001"
        
        # Initialize session state
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
    
    def check_api_status(self) -> bool:
        """Check if the API is running"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def query_documents(self, query: str) -> dict:
        """Query the document store"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={"query": query},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def search_documents(self, query: str, k: int = 5) -> dict:
        """Search for relevant documents"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/search",
                json={"query": query, "k": k},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def display_header(self):
        """Display the header"""
        st.title("🔍 CriticalAlert AI - Document Query")
        st.markdown("Query your radiology documents using natural language")
        
        # API status indicator
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if self.check_api_status():
                st.success("🟢 API Online")
            else:
                st.error("🔴 API Offline")
                st.warning("Make sure the CriticalAlert AI service is running on port 49001")
    
    def display_query_interface(self):
        """Display the main query interface"""
        
        st.markdown("---")
        
        # Query input section
        st.subheader("💬 Ask a Question")
        
        # Sample queries
        with st.expander("💡 Sample Queries", expanded=False):
            sample_queries = [
                "What are the critical findings in the latest reports?",
                "Show me all cases with pulmonary embolism",
                "Find reports mentioning intracranial hemorrhage",
                "What imaging studies were performed today?",
                "Are there any urgent conditions that need attention?",
                "Show me CT scan results with abnormal findings"
            ]
            
            for i, sample in enumerate(sample_queries):
                if st.button(f"📝 {sample}", key=f"sample_{i}"):
                    st.session_state.current_query = sample
                    st.rerun()
        
        # Main query input
        query = st.text_area(
            "Enter your question:",
            value=st.session_state.current_query,
            height=100,
            placeholder="e.g., 'What are the critical findings in recent CT scans?'"
        )
        
        # Query options
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            query_type = st.radio(
                "Query Type:",
                ["🤖 AI Answer (RAG)", "🔍 Document Search"],
                horizontal=True
            )
        
        with col2:
            if query_type == "🔍 Document Search":
                num_results = st.slider("Results", 1, 10, 5)
            else:
                num_results = 5
        
        with col3:
            st.write("")  # Spacing
            search_button = st.button("🚀 Query", type="primary", use_container_width=True)
        
        # Execute query
        if search_button and query.strip():
            st.session_state.current_query = query
            
            with st.spinner("🔍 Searching documents..."):
                if query_type == "🤖 AI Answer (RAG)":
                    result = self.query_documents(query)
                else:
                    result = self.search_documents(query, num_results)
                
                # Add to history
                st.session_state.query_history.insert(0, {
                    "timestamp": datetime.now(),
                    "query": query,
                    "type": query_type,
                    "result": result
                })
                
                # Display result
                self.display_query_result(result, query_type)
        
        elif search_button:
            st.warning("⚠️ Please enter a question")
    
    def display_query_result(self, result: dict, query_type: str):
        """Display query results"""
        
        st.markdown("---")
        st.subheader("📋 Results")
        
        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
            return
        
        if query_type == "🤖 AI Answer (RAG)":
            # Display AI-generated answer
            if "answer" in result:
                st.markdown("### 🤖 AI Answer")
                st.markdown(result["answer"])
                
                # Display sources if available
                if "sources" in result and result["sources"]:
                    with st.expander("📚 Sources", expanded=False):
                        for i, source in enumerate(result["sources"], 1):
                            st.markdown(f"**Source {i}:**")
                            st.markdown(f"- **Confidence:** {source.get('confidence', 'N/A')}")
                            if 'text' in source:
                                st.markdown(f"- **Content:** {source['text'][:200]}...")
                            st.markdown("---")
            else:
                st.warning("⚠️ No answer generated")
        
        else:
            # Display search results
            if "results" in result and result["results"]:
                st.markdown(f"### 🔍 Found {len(result['results'])} relevant documents")
                
                for i, doc in enumerate(result["results"], 1):
                    with st.expander(f"📄 Document {i} (Score: {doc.get('score', 'N/A'):.3f})", expanded=i==1):
                        
                        # Document metadata
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Source:** {doc.get('source', 'Unknown')}")
                            st.markdown(f"**Confidence:** {doc.get('confidence', 'N/A')}")
                        
                        with col2:
                            if 'timestamp' in doc:
                                st.markdown(f"**Date:** {doc['timestamp']}")
                        
                        # Document content
                        st.markdown("**Content:**")
                        content = doc.get('text', 'No content available')
                        st.markdown(content[:500] + ("..." if len(content) > 500 else ""))
            else:
                st.warning("⚠️ No documents found matching your query")
    
    def display_query_history(self):
        """Display query history"""
        
        if not st.session_state.query_history:
            return
        
        st.markdown("---")
        st.subheader("📚 Query History")
        
        # Show last 5 queries
        for i, entry in enumerate(st.session_state.query_history[:5]):
            with st.expander(
                f"🕐 {entry['timestamp'].strftime('%H:%M:%S')} - {entry['query'][:50]}...",
                expanded=False
            ):
                st.markdown(f"**Query:** {entry['query']}")
                st.markdown(f"**Type:** {entry['type']}")
                st.markdown(f"**Time:** {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if st.button(f"🔄 Repeat Query", key=f"repeat_{i}"):
                    st.session_state.current_query = entry['query']
                    st.rerun()
    
    def display_sidebar(self):
        """Display sidebar with information"""
        
        with st.sidebar:
            st.header("ℹ️ About")
            st.markdown("""
            This interface allows you to query your radiology documents using:
            
            **🤖 AI Answer (RAG):**
            - Get intelligent answers based on document content
            - Powered by retrieval-augmented generation
            - Provides sources for transparency
            
            **🔍 Document Search:**
            - Find relevant documents by similarity
            - Adjust number of results
            - See confidence scores
            """)
            
            st.markdown("---")
            
            st.header("🎯 Tips")
            st.markdown("""
            - Be specific in your questions
            - Use medical terminology when appropriate
            - Try different phrasings if no results
            - Check the API status indicator
            """)
            
            st.markdown("---")
            
            # Clear history button
            if st.button("🗑️ Clear History"):
                st.session_state.query_history = []
                st.session_state.current_query = ""
                st.success("History cleared!")
                st.rerun()
    
    def run(self):
        """Run the query interface"""
        
        # Display header
        self.display_header()
        
        # Display sidebar
        self.display_sidebar()
        
        # Main interface
        self.display_query_interface()
        
        # Query history
        self.display_query_history()
        
        # Footer
        st.markdown("---")
        st.caption("🏥 CriticalAlert AI Document Query Interface")

def main():
    """Main function"""
    interface = DocumentQueryInterface()
    interface.run()

if __name__ == "__main__":
    main()
