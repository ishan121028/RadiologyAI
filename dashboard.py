#!/usr/bin/env python3
"""
CriticalAlert AI Dashboard

Real-time Streamlit dashboard for monitoring radiology reports and critical medical findings.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time
import asyncio
import websockets
from datetime import datetime, timedelta
import os
from pathlib import Path
import glob

# Configure Streamlit page
st.set_page_config(
    page_title="CriticalAlert AI Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-red {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-orange {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-yellow {
        background-color: #fffde7;
        border-left: 4px solid #ffeb3b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-green {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class CriticalAlertDashboard:
    def __init__(self):
        self.api_base_url = "http://localhost:49001"
        self.mcp_base_url = "http://localhost:8123/mcp"
        self.extraction_results_dir = Path("data/extraction_results")
        # Pathway server endpoints
        self.pathway_endpoints = {
            "statistics": "/v1/statistics",
            "retrieve": "/v1/retrieve", 
            "answer": "/v1/pw_ai_answer",
            "list_documents": "/v1/pw_list_documents"
        }
        
    def get_processing_stats(self):
        """Get real-time processing statistics."""
        # Try to get stats from Pathway server first
        try:
            response = requests.post(
                f"{self.api_base_url}{self.pathway_endpoints['statistics']}", 
                json={},
                timeout=5
            )
            if response.status_code == 200:
                pathway_stats = response.json()
                # Extract relevant statistics from Pathway response
                if isinstance(pathway_stats, dict) and 'statistics' in pathway_stats:
                    stats_data = pathway_stats['statistics']
                    return {
                        "total_documents": stats_data.get('total_documents', 0),
                        "processed_documents": stats_data.get('processed_documents', 0),
                        "successful_extractions": stats_data.get('successful_extractions', 0),
                        "success_rate": stats_data.get('success_rate', 0),
                        "failed_extractions": stats_data.get('failed_extractions', 0)
                    }
        except Exception as e:
            st.warning(f"Could not get stats from Pathway server: {e}")
        
        # Fallback to file system stats
        try:
            if self.extraction_results_dir.exists():
                json_files = list(self.extraction_results_dir.glob("*.json"))
                fallback_files = list((self.extraction_results_dir / "fallback").glob("*.json")) if (self.extraction_results_dir / "fallback").exists() else []
                
                total_files = len(json_files) + len(fallback_files)
                successful_extractions = len(json_files)
                success_rate = (successful_extractions / total_files * 100) if total_files > 0 else 0
                
                return {
                    "total_documents": total_files,
                    "processed_documents": total_files,
                    "successful_extractions": successful_extractions,
                    "success_rate": success_rate,
                    "failed_extractions": len(fallback_files)
                }
        except Exception as e:
            st.error(f"Error getting processing stats: {e}")
        
        return {
            "total_documents": 0,
            "processed_documents": 0,
            "successful_extractions": 0,
            "success_rate": 0,
            "failed_extractions": 0
        }
    
    def get_recent_documents(self, limit=10):
        """Get recently processed documents."""
        documents = []
        
        try:
            if self.extraction_results_dir.exists():
                # Get all JSON files sorted by modification time
                json_files = sorted(
                    self.extraction_results_dir.glob("*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )[:limit]
                
                for file_path in json_files:
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            
                        # Extract relevant information
                        extraction = data.get('extraction', {})
                        metadata = data.get('metadata', {})
                        
                        doc_info = {
                            "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime),
                            "filename": metadata.get('filename', file_path.name),
                            "patient_id": extraction.get('patient_id', 'N/A'),
                            "study_type": extraction.get('study_type', 'N/A'),
                            "findings": extraction.get('findings', 'N/A'),
                            "impression": extraction.get('impression', 'N/A'),
                            "critical_findings": extraction.get('critical_findings', ''),
                            "alert_level": self.determine_alert_level(extraction),
                            "processing_time": metadata.get('processing_time_ms', 0),
                            "extraction_success": data.get('extraction_error') is None
                        }
                        
                        documents.append(doc_info)
                        
                    except Exception as e:
                        st.warning(f"Error reading {file_path}: {e}")
                        
        except Exception as e:
            st.error(f"Error getting recent documents: {e}")
            
        return documents
    
    def determine_alert_level(self, extraction):
        """Determine alert level based on extraction content."""
        critical_findings = str(extraction.get('critical_findings', '')).lower()
        findings = str(extraction.get('findings', '')).lower()
        impression = str(extraction.get('impression', '')).lower()
        
        # Check for critical/emergency keywords
        critical_keywords = ['emergency', 'urgent', 'critical', 'immediate', 'stat', 'acute']
        if any(keyword in critical_findings for keyword in critical_keywords):
            return "RED"
        
        # Check for abnormal findings
        abnormal_keywords = ['abnormal', 'lesion', 'fracture', 'mass', 'tumor', 'hemorrhage', 'infarct']
        if any(keyword in findings or keyword in impression for keyword in abnormal_keywords):
            return "ORANGE"
        
        # Check for minor concerns
        concern_keywords = ['mild', 'slight', 'minimal', 'small', 'trace']
        if any(keyword in findings or keyword in impression for keyword in concern_keywords):
            return "YELLOW"
        
        # Normal findings
        normal_keywords = ['normal', 'no abnormality', 'unremarkable', 'within normal limits']
        if any(keyword in findings or keyword in impression for keyword in normal_keywords):
            return "GREEN"
        
        return "YELLOW"  # Default for unclear cases
    
    def get_critical_alerts(self):
        """Get current critical alerts."""
        documents = self.get_recent_documents(50)  # Check more documents for alerts
        
        critical_alerts = []
        for doc in documents:
            if doc['alert_level'] in ['RED', 'ORANGE']:
                critical_alerts.append(doc)
        
        return sorted(critical_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def render_header(self):
        """Render the dashboard header."""
        st.title("🏥 CriticalAlert AI Dashboard")
        st.markdown("Real-time monitoring of radiology reports and critical medical findings")
        
        # Status indicator
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.markdown("**System Status**")
            # Check if the main app is running using statistics endpoint
            try:
                response = requests.post(
                    f"{self.api_base_url}{self.pathway_endpoints['statistics']}", 
                    json={},
                    timeout=2
                )
                if response.status_code == 200:
                    st.success("🟢 Online")
                else:
                    st.error("🔴 Offline")
            except:
                st.error("🔴 Offline")
        
        with col2:
            st.markdown("**Last Update**")
            st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
        
        with col3:
            if st.button("🔄 Refresh Dashboard", type="primary"):
                st.rerun()
    
    def render_metrics(self):
        """Render key metrics."""
        stats = self.get_processing_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📄 Total Documents",
                value=stats["total_documents"],
                delta=None
            )
        
        with col2:
            st.metric(
                label="✅ Successful Extractions", 
                value=stats["successful_extractions"],
                delta=None
            )
        
        with col3:
            st.metric(
                label="📊 Success Rate",
                value=f"{stats['success_rate']:.1f}%",
                delta=None
            )
        
        with col4:
            st.metric(
                label="❌ Failed Extractions",
                value=stats["failed_extractions"],
                delta=None
            )
    
    def render_critical_alerts(self):
        """Render critical alerts section."""
        st.subheader("🚨 Critical Alerts")
        
        alerts = self.get_critical_alerts()
        
        if not alerts:
            st.success("✅ No critical alerts at this time")
            return
        
        # Alert summary
        red_alerts = len([a for a in alerts if a['alert_level'] == 'RED'])
        orange_alerts = len([a for a in alerts if a['alert_level'] == 'ORANGE'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔴 Critical (RED)", red_alerts)
        with col2:
            st.metric("🟠 Warning (ORANGE)", orange_alerts)
        
        # Display alerts
        for alert in alerts[:5]:  # Show top 5 alerts
            alert_class = f"alert-{alert['alert_level'].lower()}"
            
            with st.container():
                st.markdown(f"""
                <div class="{alert_class}">
                    <h4>🚨 {alert['alert_level']} Alert - Patient {alert['patient_id']}</h4>
                    <p><strong>Study:</strong> {alert['study_type']}</p>
                    <p><strong>Time:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Findings:</strong> {alert['findings'][:200]}...</p>
                    <p><strong>Impression:</strong> {alert['impression']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_recent_documents(self):
        """Render recent documents table."""
        st.subheader("📋 Recent Documents")
        
        documents = self.get_recent_documents(20)
        
        if not documents:
            st.info("No documents processed yet")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(documents)
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Color code by alert level
        def color_alert_level(val):
            colors = {
                'RED': 'background-color: #ffcdd2',
                'ORANGE': 'background-color: #ffe0b2', 
                'YELLOW': 'background-color: #fff9c4',
                'GREEN': 'background-color: #c8e6c9'
            }
            return colors.get(val, '')
        
        # Display table
        styled_df = df[['timestamp', 'patient_id', 'study_type', 'alert_level', 'impression']].style.applymap(
            color_alert_level, subset=['alert_level']
        )
        
        st.dataframe(styled_df, use_container_width=True)
    
    def render_analytics(self):
        """Render analytics charts."""
        st.subheader("📊 Analytics")
        
        documents = self.get_recent_documents(100)
        
        if not documents:
            st.info("No data available for analytics")
            return
        
        df = pd.DataFrame(documents)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Alert level distribution
            alert_counts = df['alert_level'].value_counts()
            fig_pie = px.pie(
                values=alert_counts.values,
                names=alert_counts.index,
                title="Alert Level Distribution",
                color_discrete_map={
                    'RED': '#f44336',
                    'ORANGE': '#ff9800', 
                    'YELLOW': '#ffeb3b',
                    'GREEN': '#4caf50'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Processing time distribution
            if 'processing_time' in df.columns:
                fig_hist = px.histogram(
                    df,
                    x='processing_time',
                    title="Processing Time Distribution (ms)",
                    nbins=20
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        
        # Study type distribution
        if len(df) > 0:
            study_counts = df['study_type'].value_counts()
            fig_bar = px.bar(
                x=study_counts.index,
                y=study_counts.values,
                title="Study Type Distribution"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    def render_sidebar(self):
        """Render sidebar with controls."""
        st.sidebar.title("⚙️ Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
            time.sleep(refresh_interval)
            st.rerun()
        
        # Alert filters
        st.sidebar.subheader("🔍 Alert Filters")
        show_red = st.sidebar.checkbox("🔴 Critical (RED)", value=True)
        show_orange = st.sidebar.checkbox("🟠 Warning (ORANGE)", value=True)
        show_yellow = st.sidebar.checkbox("🟡 Caution (YELLOW)", value=False)
        show_green = st.sidebar.checkbox("🟢 Normal (GREEN)", value=False)
        
        # System info
        st.sidebar.subheader("ℹ️ System Info")
        st.sidebar.info(f"""
        **API Endpoint:** {self.api_base_url}
        **MCP Server:** {self.mcp_base_url}
        **Data Directory:** {self.extraction_results_dir}
        """)
    
    def run(self):
        """Run the dashboard."""
        self.render_header()
        self.render_sidebar()
        
        # Main content
        self.render_metrics()
        st.divider()
        
        # Two column layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.render_critical_alerts()
        
        with col2:
            self.render_recent_documents()
        
        st.divider()
        self.render_analytics()


def main():
    """Main dashboard function."""
    dashboard = CriticalAlertDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
