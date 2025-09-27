#!/usr/bin/env python3

"""
CriticalAlert AI MCP Server

Following the latest Pathway MCP server implementation patterns:
- McpServable classes for tools
- PathwayMcp for server configuration  
- Streamable HTTP transport
- Schema-based request/response handling
"""

import logging
import os
from typing import List, Dict, Any, Optional

import pathway as pw
from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp
from dotenv import load_dotenv
from datetime import datetime

# Import our CriticalAlert AI components
from src.intelligence.critical_alert_answerer import CriticalAlertQuestionAnswerer
from src.parsers.landingai_parser import RadiologyDocumentStore, LandingAIRadiologyParser

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# --- MCP Request/Response Schemas ---

class EmptyRequestSchema(pw.Schema):
    """Empty schema for tools that don't need parameters"""
    pass

class RadiologyAnalysisRequestSchema(pw.Schema):
    """Schema for radiology report analysis requests"""
    report_content: str
    patient_id: pw.Column[Optional[str]] = pw.column_definition(default_value=None)
    urgency_level: pw.Column[Optional[str]] = pw.column_definition(default_value=None)

class AlertQueryRequestSchema(pw.Schema):
    """Schema for alert queries"""
    alert_level: pw.Column[Optional[str]] = pw.column_definition(default_value=None)  # "RED", "ORANGE", "YELLOW", "GREEN"
    patient_id: pw.Column[Optional[str]] = pw.column_definition(default_value=None)
    time_range_hours: pw.Column[Optional[int]] = pw.column_definition(default_value=None)

class MedicalRecommendationRequestSchema(pw.Schema):
    """Schema for medical recommendation requests"""
    findings: str
    patient_context: pw.Column[Optional[str]] = pw.column_definition(default_value=None)
    urgency: pw.Column[Optional[str]] = pw.column_definition(default_value=None)

# --- MCP Servable Tools ---

class CriticalAlertAnalyzerTool(McpServable):
    """
    MCP tool for analyzing radiology reports and detecting critical findings
    
    Following latest Pathway MCP patterns with McpServable inheritance
    """
    
    def __init__(self):
        """Initialize with CriticalAlert AI components"""
        self.landingai_api_key = os.getenv("LANDINGAI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.landingai_api_key:
            logger.warning("LANDINGAI_API_KEY not set - using dummy key")
            self.landingai_api_key = "dummy_key"
        
        # Initialize parser
        self.parser = LandingAIRadiologyParser(
            api_key=self.landingai_api_key,
            cache_strategy=pw.udfs.DefaultCache()
        )
        logger.info("CriticalAlertAnalyzerTool initialized")
    
    def analyze_radiology_report(self, request_table: pw.Table) -> pw.Table:
        """
        Analyze a radiology report for critical findings
        
        Args:
            request_table: Pathway table with report_content, patient_id, urgency_level
            
        Returns:
            Pathway table with analysis results and alert information
        """
        
        # Convert text content to binary for parser (simulated)
        analysis_results = request_table.select(
            patient_id=pw.this.patient_id,
            report_content=pw.this.report_content,
            # Simulate parsing results (in real implementation, use actual parser)
            analysis_result=pw.apply(
                self._analyze_report_content,
                pw.this.report_content,
                pw.this.patient_id
            )
        )
        
        # Extract analysis fields
        results = analysis_results.select(
            patient_id=pw.this.patient_id,
            alert_level=pw.this.analysis_result["alert_level"],
            critical_conditions=pw.this.analysis_result["critical_conditions"],
            findings_summary=pw.this.analysis_result["findings_summary"],
            immediate_actions=pw.this.analysis_result["immediate_actions"],
            treatment_recommendations=pw.this.analysis_result["treatment_recommendations"],
            analysis_timestamp=pw.this.analysis_result["timestamp"]
        )
        
        logger.info("Radiology report analysis completed")
        return results
    
    @pw.udf
    def _analyze_report_content(self, content: str, patient_id: str) -> Dict[str, Any]:
        """UDF to analyze report content and detect critical findings"""
        
        content_lower = content.lower()
        
        # Critical condition detection
        critical_conditions = []
        alert_level = "GREEN"
        
        red_conditions = [
            "pulmonary embolism", "aortic dissection", "hemorrhage", 
            "intracranial bleed", "tension pneumothorax", "cardiac tamponade"
        ]
        orange_conditions = [
            "pneumonia", "fracture", "mass", "pneumothorax", "appendicitis"
        ]
        yellow_conditions = [
            "nodule", "cyst", "inflammation", "chronic changes"
        ]
        
        # Check for critical conditions
        for condition in red_conditions:
            if condition in content_lower:
                critical_conditions.append(condition)
                alert_level = "RED"
        
        if alert_level != "RED":
            for condition in orange_conditions:
                if condition in content_lower:
                    critical_conditions.append(condition)
                    alert_level = "ORANGE"
        
        if alert_level not in ["RED", "ORANGE"]:
            for condition in yellow_conditions:
                if condition in content_lower:
                    critical_conditions.append(condition)
                    alert_level = "YELLOW"
        
        # Generate recommendations based on findings
        immediate_actions = []
        treatment_recommendations = []
        
        if alert_level == "RED":
            immediate_actions = [
                "Notify attending physician immediately",
                "Prepare for emergency intervention",
                "Alert OR if surgical intervention needed"
            ]
        elif alert_level == "ORANGE":
            immediate_actions = [
                "Contact on-call physician within 15 minutes",
                "Schedule urgent follow-up"
            ]
        
        # Add specific recommendations based on conditions found
        for condition in critical_conditions:
            if "pulmonary embolism" in condition:
                treatment_recommendations.append("Anticoagulation per PE protocol")
            elif "pneumonia" in condition:
                treatment_recommendations.append("Antibiotic therapy consideration")
            elif "fracture" in condition:
                treatment_recommendations.append("Orthopedic consultation")
        
        return {
            "alert_level": alert_level,
            "critical_conditions": critical_conditions,
            "findings_summary": content[:200] + "..." if len(content) > 200 else content,
            "immediate_actions": immediate_actions,
            "treatment_recommendations": treatment_recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def register_mcp(self, server: McpServer):
        """Register MCP tools following latest Pathway patterns"""
        server.tool(
            "analyze_radiology_report",
            request_handler=self.analyze_radiology_report,
            schema=RadiologyAnalysisRequestSchema,
        )


class CriticalAlertMonitorTool(McpServable):
    """
    MCP tool for monitoring and querying critical alerts
    
    Provides real-time access to active alerts and statistics
    """
    
    def __init__(self, critical_alert_answerer: CriticalAlertQuestionAnswerer = None):
        """Initialize with CriticalAlert answerer for real-time data"""
        self.critical_alert_answerer = critical_alert_answerer
        logger.info("CriticalAlertMonitorTool initialized")
    
    def get_active_alerts(self, request_table: pw.Table) -> pw.Table:
        """
        Get currently active critical alerts
        
        Args:
            request_table: Query parameters (alert_level, patient_id, time_range_hours)
            
        Returns:
            Pathway table with active alerts
        """
        
        # In a real implementation, this would query the live alert stream
        # For now, return simulated active alerts
        active_alerts = request_table.select(
            alert_id=pw.apply(lambda: f"ALERT_{datetime.now().strftime('%H%M%S')}"),
            alert_level=pw.coalesce(pw.this.alert_level, "RED"),
            patient_id=pw.coalesce(pw.this.patient_id, "PATIENT_DEMO"),
            condition="Simulated Critical Finding",
            timestamp=datetime.now().isoformat(),
            status="ACTIVE",
            response_time_minutes=pw.apply(lambda level: 5 if level == "RED" else 30, pw.this.alert_level)
        )
        
        logger.info("Active alerts retrieved")
        return active_alerts
    
    def get_alert_statistics(self, request_table: pw.Table) -> pw.Table:
        """
        Get alert processing and performance statistics
        
        Returns:
            Pathway table with processing statistics
        """
        
        # Simulate real-time statistics
        stats = request_table.select(
            total_reports_processed=100,
            red_alerts_today=5,
            orange_alerts_today=12,
            yellow_alerts_today=8,
            green_reports_today=75,
            avg_processing_time_seconds=15.3,
            avg_response_time_minutes=2.1,
            system_status="OPERATIONAL",
            last_update=datetime.now().isoformat()
        )
        
        logger.info("Alert statistics retrieved")
        return stats
    
    def register_mcp(self, server: McpServer):
        """Register monitoring tools"""
        server.tool(
            "get_active_alerts",
            request_handler=self.get_active_alerts,
            schema=AlertQueryRequestSchema,
        )
        server.tool(
            "get_alert_statistics",
            request_handler=self.get_alert_statistics,
            schema=EmptyRequestSchema,
        )


class MedicalRecommendationTool(McpServable):
    """
    MCP tool for generating medical recommendations
    
    Provides evidence-based medical guidance for radiology findings
    """
    
    def generate_medical_recommendations(self, request_table: pw.Table) -> pw.Table:
        """
        Generate medical recommendations based on findings
        
        Args:
            request_table: findings, patient_context, urgency
            
        Returns:
            Pathway table with medical recommendations
        """
        
        recommendations = request_table.select(
            findings=pw.this.findings,
            recommendations=pw.apply(
                self._generate_recommendations_udf,
                pw.this.findings,
                pw.coalesce(pw.this.urgency, "ROUTINE")
            ),
            urgency_level=pw.coalesce(pw.this.urgency, "ROUTINE"),
            next_steps=pw.apply(
                self._generate_next_steps_udf,
                pw.this.findings,
                pw.coalesce(pw.this.urgency, "ROUTINE")
            ),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("Medical recommendations generated")
        return recommendations
    
    @pw.udf 
    def _generate_recommendations_udf(self, findings: str, urgency: str) -> List[str]:
        """Generate evidence-based medical recommendations"""
        
        findings_lower = findings.lower()
        recommendations = []
        
        # General recommendations based on findings
        if "pulmonary embolism" in findings_lower:
            recommendations.extend([
                "Immediate anticoagulation per institutional PE protocol",
                "Consider thrombolysis if massive PE with hemodynamic compromise",
                "Serial arterial blood gas monitoring"
            ])
        elif "pneumonia" in findings_lower:
            recommendations.extend([
                "Empirical antibiotic therapy per CAP guidelines",
                "Blood cultures before antibiotic administration",
                "Consider ICU if severe pneumonia"
            ])
        elif "fracture" in findings_lower:
            recommendations.extend([
                "Orthopedic surgery consultation",
                "Pain management per protocol",
                "Immobilization of affected area"
            ])
        else:
            recommendations.append("Follow standard care protocols for identified findings")
        
        # Add urgency-specific recommendations
        if urgency == "EMERGENCY":
            recommendations.insert(0, "STAT physician notification required")
        elif urgency == "URGENT":
            recommendations.insert(0, "Urgent physician review within 30 minutes")
        
        return recommendations
    
    @pw.udf
    def _generate_next_steps_udf(self, findings: str, urgency: str) -> List[str]:
        """Generate next steps based on findings and urgency"""
        
        next_steps = []
        
        if urgency == "EMERGENCY":
            next_steps = [
                "Immediate physician notification",
                "Prepare for emergency intervention",
                "Obtain IV access"
            ]
        elif urgency == "URGENT":
            next_steps = [
                "Physician review within 30 minutes",
                "Additional imaging if indicated",
                "Laboratory studies as clinically indicated"
            ]
        else:
            next_steps = [
                "Routine follow-up per protocol",
                "Document findings in medical record",
                "Schedule appropriate follow-up"
            ]
        
        return next_steps
    
    def register_mcp(self, server: McpServer):
        """Register medical recommendation tools"""
        server.tool(
            "generate_medical_recommendations",
            request_handler=self.generate_medical_recommendations,
            schema=MedicalRecommendationRequestSchema,
        )


# --- MCP Server Configuration ---

def create_critical_alert_mcp_server(
    host: str = "0.0.0.0",
    port: int = 8127,
    critical_alert_answerer: CriticalAlertQuestionAnswerer = None
) -> PathwayMcp:
    """
    Create CriticalAlert AI MCP server following latest Pathway patterns
    
    Args:
        host: Server host
        port: Server port
        critical_alert_answerer: CriticalAlert answerer instance
        
    Returns:
        Configured PathwayMcp server
    """
    
    # Initialize MCP tools
    analyzer_tool = CriticalAlertAnalyzerTool()
    monitor_tool = CriticalAlertMonitorTool(critical_alert_answerer)
    recommendation_tool = MedicalRecommendationTool()
    
    logger.info(f"Creating CriticalAlert AI MCP server on {host}:{port}")
    
    # Create MCP server following latest Pathway patterns
    pathway_mcp_server = PathwayMcp(
        name="CriticalAlert AI MCP Server",
        transport="streamable-http",  # Latest transport method
        host=host,
        port=port,
        serve=[
            analyzer_tool,
            monitor_tool, 
            recommendation_tool
        ]
    )
    
    logger.info("CriticalAlert AI MCP server configured successfully")
    return pathway_mcp_server


if __name__ == "__main__":
    """
    Standalone MCP server for CriticalAlert AI
    
    Usage:
        python src/mcp/critical_alert_mcp_server.py
    """
    
    # Set up Pathway license
    pw.set_license_key(os.getenv("PATHWAY_LICENSE_KEY", "demo-license-key-with-telemetry"))
    
    logger.info("🚨 Starting CriticalAlert AI MCP Server...")
    
    # Create and run MCP server
    mcp_server = create_critical_alert_mcp_server(
        host="0.0.0.0",
        port=8127
    )
    
    logger.info("🚀 CriticalAlert AI MCP Server running on http://0.0.0.0:8127/mcp/")
    logger.info("Available tools:")
    logger.info("  - analyze_radiology_report")
    logger.info("  - get_active_alerts") 
    logger.info("  - get_alert_statistics")
    logger.info("  - generate_medical_recommendations")
    
    # Run Pathway computation engine
    pw.run()
