#!/usr/bin/env python3

"""
CriticalAlert AI - Emergency Physician Dashboard
Real-time radiology alert dashboard for emergency departments
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dashboard configuration
st.set_page_config(
    page_title="🚨 CriticalAlert AI - Emergency Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EmergencyDashboard:
    """Emergency physician dashboard for critical radiology alerts"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.alerts_dir = self.data_dir / "alerts"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directories if they don't exist
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session state
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
    
    def generate_sample_alerts(self) -> List[Dict]:
        """Generate sample critical alerts for demonstration"""
        
        sample_alerts = [
            {
                "alert_id": "ALERT_001",
                "timestamp": datetime.now() - timedelta(minutes=5),
                "patient_id": "P12345",
                "severity": "RED",
                "study_type": "CT Pulmonary Angiogram",
                "critical_findings": ["Massive Pulmonary Embolism", "Right Heart Strain"],
                "findings": "Large filling defect in main pulmonary artery extending into both main pulmonary arteries",
                "impression": "Massive pulmonary embolism with signs of right heart strain. IMMEDIATE MEDICAL ATTENTION REQUIRED.",
                "radiologist": "Dr. Sarah Johnson, MD",
                "acknowledged": False,
                "response_time": None,
                "confidence": 0.95
            },
            {
                "alert_id": "ALERT_002", 
                "timestamp": datetime.now() - timedelta(minutes=12),
                "patient_id": "P67890",
                "severity": "RED",
                "study_type": "Head CT",
                "critical_findings": ["Intracranial Hemorrhage", "Mass Effect"],
                "findings": "Large intraparenchymal hemorrhage in right frontal lobe with surrounding edema",
                "impression": "Acute intracranial hemorrhage with mass effect. Immediate neurosurgical consultation required.",
                "radiologist": "Dr. Michael Chen, MD",
                "acknowledged": True,
                "response_time": 3.2,
                "confidence": 0.92
            },
            {
                "alert_id": "ALERT_003",
                "timestamp": datetime.now() - timedelta(minutes=25),
                "patient_id": "P11223",
                "severity": "ORANGE", 
                "study_type": "Chest CT",
                "critical_findings": ["Pneumonia", "Pleural Effusion"],
                "findings": "Consolidation in right lower lobe with air bronchograms, small pleural effusion",
                "impression": "Right lower lobe pneumonia with small pleural effusion. Recommend antibiotic therapy.",
                "radiologist": "Dr. Lisa Wang, MD",
                "acknowledged": True,
                "response_time": 8.5,
                "confidence": 0.88
            },
            {
                "alert_id": "ALERT_004",
                "timestamp": datetime.now() - timedelta(minutes=35),
                "patient_id": "P44556",
                "severity": "YELLOW",
                "study_type": "Chest X-Ray",
                "critical_findings": ["Pneumothorax"],
                "findings": "Small left-sided pneumothorax, approximately 10%",
                "impression": "Small left pneumothorax. Monitor and consider chest tube if enlarging.",
                "radiologist": "Dr. James Brown, MD",
                "acknowledged": True,
                "response_time": 12.0,
                "confidence": 0.85
            }
        ]
        
        return sample_alerts
    
    def get_severity_color(self, severity: str) -> str:
        """Get color code for severity level"""
        colors = {
            "RED": "#FF0000",
            "ORANGE": "#FF8C00", 
            "YELLOW": "#FFD700"
        }
        return colors.get(severity, "#999999")
    
    def get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level"""
        emojis = {
            "RED": "🚨",
            "ORANGE": "⚠️",
            "YELLOW": "⚡"
        }
        return emojis.get(severity, "ℹ️")
    
    def display_header(self):
        """Display dashboard header"""
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.title("🚨 CriticalAlert AI")
            st.caption("Emergency Radiology Alert System")
        
        with col2:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.metric("Current Time", current_time)
        
        with col3:
            if st.button("🔄 Refresh", type="primary"):
                st.session_state.last_refresh = datetime.now()
                st.rerun()
    
    def display_alert_summary(self, alerts: List[Dict]):
        """Display alert summary metrics"""
        
        # Calculate metrics
        total_alerts = len(alerts)
        red_alerts = len([a for a in alerts if a['severity'] == 'RED'])
        orange_alerts = len([a for a in alerts if a['severity'] == 'ORANGE']) 
        yellow_alerts = len([a for a in alerts if a['severity'] == 'YELLOW'])
        unacknowledged = len([a for a in alerts if not a['acknowledged']])
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🚨 Critical (RED)", red_alerts, delta=None)
        
        with col2:
            st.metric("⚠️ Urgent (ORANGE)", orange_alerts, delta=None)
        
        with col3:
            st.metric("⚡ Alert (YELLOW)", yellow_alerts, delta=None)
        
        with col4:
            st.metric("📢 Unacknowledged", unacknowledged, delta=None)
        
        with col5:
            avg_response_time = sum([a['response_time'] for a in alerts if a['response_time']]) / max(len([a for a in alerts if a['response_time']]), 1)
            st.metric("⏱️ Avg Response Time", f"{avg_response_time:.1f} min")
    
    def display_critical_alerts(self, alerts: List[Dict]):
        """Display critical alerts requiring immediate attention"""
        
        st.subheader("🚨 Critical Alerts - Immediate Action Required")
        
        critical_alerts = [a for a in alerts if a['severity'] == 'RED' and not a['acknowledged']]
        
        if not critical_alerts:
            st.success("✅ No unacknowledged critical alerts")
            return
        
        for alert in critical_alerts:
            with st.container():
                # Alert header
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"### {alert['severity']} ALERT: {alert['patient_id']}")
                    time_ago = datetime.now() - alert['timestamp']
                    st.caption(f"📅 {time_ago.seconds // 60} minutes ago • {alert['study_type']}")
                
                with col2:
                    st.markdown(f"**Radiologist:** {alert['radiologist']}")
                    st.markdown(f"**Confidence:** {alert['confidence']:.0%}")
                
                with col3:
                    if st.button(f"✅ Acknowledge", key=f"ack_{alert['alert_id']}", type="primary"):
                        alert['acknowledged'] = True
                        alert['response_time'] = (datetime.now() - alert['timestamp']).total_seconds() / 60
                        st.success("Alert acknowledged!")
                        st.rerun()
                
                # Alert details
                st.markdown(f"**🔍 Findings:** {alert['findings']}")
                st.markdown(f"**📋 Impression:** {alert['impression']}")
                
                # Critical findings tags
                if alert['critical_findings']:
                    st.markdown("**🚨 Critical Conditions:**")
                    for finding in alert['critical_findings']:
                        st.markdown(f"🔸 {finding}")
                
                st.markdown("---")
    
    def display_alert_history(self, alerts: List[Dict]):
        """Display historical alerts table"""
        
        st.subheader("📊 Alert History")
        
        if not alerts:
            st.info("No alerts to display")
            return
        
        # Prepare data for table
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "Time": alert['timestamp'].strftime("%H:%M:%S"),
                "Severity": f"{self.get_severity_emoji(alert['severity'])} {alert['severity']}",
                "Patient ID": alert['patient_id'],
                "Study Type": alert['study_type'],
                "Critical Findings": ", ".join(alert['critical_findings'][:2]) + ("..." if len(alert['critical_findings']) > 2 else ""),
                "Status": "✅ Acknowledged" if alert['acknowledged'] else "🔔 Pending",
                "Response Time": f"{alert['response_time']:.1f} min" if alert['response_time'] else "-",
                "Confidence": f"{alert['confidence']:.0%}"
            })
        
        # Display table
        df = pd.DataFrame(alert_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def display_analytics(self, alerts: List[Dict]):
        """Display analytics charts"""
        
        if not alerts:
            return
        
        st.subheader("📈 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Severity distribution pie chart
            severity_counts = {}
            for alert in alerts:
                severity = alert['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if severity_counts:
                fig_pie = px.pie(
                    values=list(severity_counts.values()),
                    names=list(severity_counts.keys()),
                    title="Alert Severity Distribution",
                    color_discrete_map={
                        "RED": "#FF0000",
                        "ORANGE": "#FF8C00",
                        "YELLOW": "#FFD700"
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Response time distribution
            response_times = [a['response_time'] for a in alerts if a['response_time']]
            if response_times:
                fig_hist = px.histogram(
                    x=response_times,
                    title="Response Time Distribution (minutes)",
                    nbins=10
                )
                fig_hist.update_xaxes(title="Response Time (minutes)")
                fig_hist.update_yaxes(title="Number of Alerts")
                st.plotly_chart(fig_hist, use_container_width=True)
    
    def display_sidebar(self):
        """Display sidebar with controls and info"""
        
        with st.sidebar:
            st.header("🎛️ Dashboard Controls")
            
            # Auto-refresh toggle
            auto_refresh = st.toggle("🔄 Auto-refresh (30s)", value=False)
            
            if auto_refresh:
                time.sleep(30)
                st.rerun()
            
            st.markdown("---")
            
            # System status
            st.header("⚡ System Status")
            st.success("🟢 LandingAI Parser: Online")
            st.success("🟢 Alert System: Active")
            st.success("🟢 File Monitor: Running")
            
            st.markdown("---")
            
            # Recent activity
            st.header("📋 Recent Activity")
            st.info("🔍 5 reports processed in last hour")
            st.info("🚨 2 critical alerts generated")
            st.info("✅ 3 alerts acknowledged")
            
            st.markdown("---")
            
            # Emergency contacts
            st.header("📞 Emergency Contacts")
            st.markdown("**Radiology:** Ext. 2345")
            st.markdown("**Cardiology:** Ext. 3456") 
            st.markdown("**Neurosurgery:** Ext. 4567")
            st.markdown("**ER Attending:** Ext. 5678")
    
    def run(self):
        """Run the dashboard"""
        
        # Display header
        self.display_header()
        
        # Display sidebar
        self.display_sidebar()
        
        # Get alerts (using sample data for demo)
        alerts = self.generate_sample_alerts()
        st.session_state.alerts = alerts
        
        # Main dashboard content
        
        # Alert summary
        self.display_alert_summary(alerts)
        
        st.markdown("---")
        
        # Critical alerts section
        self.display_critical_alerts(alerts)
        
        st.markdown("---")
        
        # Alert history
        self.display_alert_history(alerts)
        
        st.markdown("---")
        
        # Analytics
        self.display_analytics(alerts)
        
        # Footer
        st.markdown("---")
        st.caption("🏥 CriticalAlert AI Emergency Dashboard • Last updated: " + 
                  st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S"))

def main():
    """Main function"""
    dashboard = EmergencyDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
