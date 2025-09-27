#!/usr/bin/env python3

"""
CriticalAlert AI - Real-time Emergency Radiology Alert System

Main application following Pathway patterns - similar to demo-question-answering/app.py
but specialized for radiology report processing and critical alert generation.
"""

import logging
from pathlib import Path
from typing import Optional, List

import pathway as pw
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, InstanceOf

# Import our custom components
from src.intelligence.critical_alert_answerer import CriticalAlertQuestionAnswerer
from src.parsers.landingai_parser import LandingAIRadiologyParser, RadiologyDocumentStore
# from src.mcp.critical_alert_mcp_server import CriticalAlertMCPServer as CriticalAlertRestServer

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CriticalAlertApp(BaseModel):
    """
    Main CriticalAlert AI application
    
    Similar to existing Pathway app templates but specialized for
    real-time radiology report processing and critical alert generation.
    """
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Data sources
    sources: List[InstanceOf[pw.Table]]
    
    # LandingAI parser configuration
    landingai_parser: InstanceOf[LandingAIRadiologyParser]
    
    # Document store for radiology reports
    radiology_document_store: InstanceOf[RadiologyDocumentStore]
    
    # Optional components
    llm: Optional[InstanceOf[pw.UDF]] = None
    retriever_factory: Optional[InstanceOf[pw.indexing.AbstractRetrieverFactory]] = None
    
    # Processing configuration
    max_processing_time: int = 30  # seconds
    enable_real_time_alerts: bool = True
    alert_escalation_enabled: bool = True
    
    # Caching and persistence
    with_cache: bool = True
    terminate_on_error: bool = False
    cache_backend: Optional[pw.persistence.Backend] = None
    
    def run(self) -> None:
        """
        Run the CriticalAlert AI application
        
        This creates the complete Pathway pipeline for:
        1. Real-time file monitoring
        2. Document parsing with LandingAI
        3. Critical finding detection
        4. Alert generation and escalation
        """
        
        logger.info("Starting CriticalAlert AI - Real-time Emergency Radiology Alert System")
        
        # Create the main processing pipeline
        critical_alerts_pipeline = self._create_processing_pipeline()
        
        # Create alert escalation pipeline
        escalated_alerts = self._create_alert_escalation_pipeline(critical_alerts_pipeline)
        
        # Create real-time statistics pipeline
        processing_stats = self._create_statistics_pipeline(critical_alerts_pipeline)
        
        # Set up output streams for notification services
        self._setup_output_streams(critical_alerts_pipeline, escalated_alerts, processing_stats)
        
        # Configure caching if enabled
        cache_backend = self.cache_backend or pw.persistence.Backend.filesystem("data/cache")
        
        # Run the Pathway computation
        logger.info("Starting Pathway computation engine...")
        pw.run(
            monitoring_level=pw.MonitoringLevel.ALL,
            cache_backend=cache_backend if self.with_cache else None,
            terminate_on_error=self.terminate_on_error
        )
    
    def _create_processing_pipeline(self) -> pw.Table:
        """
        Create the main document processing pipeline
        
        Returns:
            Table with critical alerts
        """
        
        logger.info("Creating document processing pipeline")
        
        # Combine all data sources
        combined_docs = self._combine_data_sources()
        
        # Parse documents with LandingAI
        parsed_docs = self.landingai_parser.create_medical_pipeline(combined_docs)
        
        # Detect critical findings and generate alerts
        critical_alerts = parsed_docs.select(
            # Document information
            filename=pw.this._metadata["path"],
            patient_id=pw.this.patient_id,
            study_type=pw.this.study_type,
            
            # Medical content
            findings=pw.this.findings,
            impression=pw.this.impression,
            critical_findings=pw.this.critical_findings,
            
            # Alert classification
            alert_level=self._classify_alert_level(pw.this.critical_findings),
            requires_immediate_action=self._requires_immediate_action(pw.this.critical_findings),
            
            # Metadata
            processing_timestamp=pw.now(),
            parsing_confidence=pw.this.parsing_confidence,
            processing_time=pw.this.processing_time
        ).filter(
            # Only include documents with critical findings
            pw.apply(lambda findings: len(findings) > 0, pw.this.critical_findings)
        )
        
        # Add alert ID and additional metadata
        alerts_with_metadata = critical_alerts.select(
            *critical_alerts,
            alert_id=self._generate_alert_id(),
            findings_summary=self._create_findings_summary(
                pw.this.critical_findings, 
                pw.this.alert_level
            ),
            recommended_actions=self._get_treatment_recommendations(pw.this.critical_findings),
            estimated_treatment_time=self._estimate_treatment_urgency(pw.this.alert_level)
        )
        
        return alerts_with_metadata
    
    def _create_alert_escalation_pipeline(self, alerts: pw.Table) -> pw.Table:
        """
        Create alert escalation pipeline for unacknowledged alerts
        
        Args:
            alerts: Critical alerts table
            
        Returns:
            Table with escalation information
        """
        
        if not self.alert_escalation_enabled:
            return alerts
        
        logger.info("Creating alert escalation pipeline")
        
        escalated_alerts = alerts.select(
            *alerts,
            escalation_time=self._calculate_escalation_time(
                pw.this.alert_level,
                pw.this.processing_timestamp
            ),
            escalation_target=self._determine_escalation_target(pw.this.alert_level),
            needs_escalation=self._check_escalation_needed(
                pw.this.alert_level,
                pw.this.processing_timestamp
            )
        )
        
        return escalated_alerts
    
    def _create_statistics_pipeline(self, alerts: pw.Table) -> pw.Table:
        """
        Create real-time processing statistics
        
        Args:
            alerts: Critical alerts table
            
        Returns:
            Table with processing statistics
        """
        
        logger.info("Creating real-time statistics pipeline")
        
        stats = alerts.groupby().reduce(
            total_alerts_generated=pw.reducers.count(),
            red_alerts=pw.reducers.sum(
                pw.if_else(pw.this.alert_level == "RED", 1, 0)
            ),
            orange_alerts=pw.reducers.sum(
                pw.if_else(pw.this.alert_level == "ORANGE", 1, 0)
            ),
            yellow_alerts=pw.reducers.sum(
                pw.if_else(pw.this.alert_level == "YELLOW", 1, 0)
            ),
            avg_processing_time=pw.reducers.avg(pw.this.processing_time),
            avg_parsing_confidence=pw.reducers.avg(pw.this.parsing_confidence),
            latest_alert_time=pw.reducers.latest(pw.this.processing_timestamp),
            immediate_action_alerts=pw.reducers.sum(
                pw.if_else(pw.this.requires_immediate_action, 1, 0)
            )
        )
        
        return stats
    
    def _setup_output_streams(self, alerts: pw.Table, escalated_alerts: pw.Table, stats: pw.Table) -> None:
        """
        Set up output streams for notification services
        
        Args:
            alerts: Critical alerts stream
            escalated_alerts: Escalated alerts stream  
            stats: Processing statistics stream
        """
        
        logger.info("Setting up output streams for notifications")
        
        # Output critical alerts for notification service
        alerts.debug("critical_alerts_for_notification")
        
        # Output escalated alerts
        escalated_alerts.debug("escalated_alerts_for_notification")
        
        # Output processing statistics
        stats.debug("real_time_processing_statistics")
        
        # Create specific streams for different alert levels
        red_alerts = alerts.filter(pw.this.alert_level == "RED")
        red_alerts.debug("red_alerts_immediate_notification")
        
        orange_alerts = alerts.filter(pw.this.alert_level == "ORANGE")
        orange_alerts.debug("orange_alerts_urgent_notification")
        
    def _combine_data_sources(self) -> pw.Table:
        """Combine multiple data sources into single table"""
        
        if len(self.sources) == 1:
            return self.sources[0]
        
        combined = self.sources[0]
        for source in self.sources[1:]:
            combined = combined.concat(source)
        
        return combined
    
    # UDF methods for processing pipeline
    @staticmethod
    @pw.udf
    def _classify_alert_level(critical_findings: List[str]) -> str:
        """Classify alert level based on critical findings"""
        
        if not critical_findings:
            return "GREEN"
        
        # Red alert conditions (life-threatening)
        red_conditions = [
            "pulmonary embolism", "aortic dissection", "hemorrhage", "intracranial bleed",
            "tension pneumothorax", "bowel obstruction", "aortic aneurysm rupture",
            "acute stroke", "myocardial infarction", "cardiac tamponade"
        ]
        
        # Orange alert conditions (urgent)
        orange_conditions = [
            "pneumonia", "fracture", "mass", "pneumothorax", "appendicitis",
            "kidney stones", "gallbladder inflammation", "abscess", "blood clot"
        ]
        
        findings_text = " ".join(critical_findings).lower()
        
        for condition in red_conditions:
            if condition in findings_text:
                return "RED"
        
        for condition in orange_conditions:
            if condition in findings_text:
                return "ORANGE"
        
        return "YELLOW"
    
    @staticmethod
    @pw.udf
    def _requires_immediate_action(critical_findings: List[str]) -> bool:
        """Determine if findings require immediate action"""
        
        immediate_action_conditions = [
            "pulmonary embolism", "aortic dissection", "hemorrhage", 
            "tension pneumothorax", "cardiac tamponade", "acute stroke"
        ]
        
        findings_text = " ".join(critical_findings).lower()
        
        return any(condition in findings_text for condition in immediate_action_conditions)
    
    @staticmethod
    @pw.udf  
    def _generate_alert_id() -> str:
        """Generate unique alert ID"""
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        return f"ALERT_{timestamp}_{unique_id}"
    
    @staticmethod
    @pw.udf
    def _create_findings_summary(critical_findings: List[str], alert_level: str) -> str:
        """Create concise summary for emergency physicians"""
        
        if not critical_findings:
            return "No critical findings"
        
        findings_str = ", ".join(critical_findings)
        
        if alert_level == "RED":
            return f"🚨 CRITICAL: {findings_str.upper()} - Immediate intervention required"
        elif alert_level == "ORANGE":
            return f"⚠️ URGENT: {findings_str} - Prompt evaluation needed"
        else:
            return f"📋 FOLLOW-UP: {findings_str} - Schedule appropriate follow-up"
    
    @staticmethod
    @pw.udf
    def _get_treatment_recommendations(critical_findings: List[str]) -> List[str]:
        """Get evidence-based treatment recommendations"""
        
        recommendations = []
        
        for finding in critical_findings:
            finding_lower = finding.lower()
            
            if "pulmonary embolism" in finding_lower:
                recommendations.extend([
                    "Initiate anticoagulation immediately",
                    "Consider thrombolytic therapy if massive PE"
                ])
            elif "aortic dissection" in finding_lower:
                recommendations.extend([
                    "Control BP (SBP <120)",
                    "Urgent cardiothoracic surgery consult"
                ])
            elif "hemorrhage" in finding_lower:
                recommendations.extend([
                    "Type and crossmatch blood products",
                    "Consider reversal agents"
                ])
            elif "fracture" in finding_lower:
                recommendations.extend([
                    "Immobilize affected area",
                    "Orthopedic consultation"
                ])
        
        return list(set(recommendations)) if recommendations else ["Standard care protocol"]
    
    @staticmethod
    @pw.udf
    def _estimate_treatment_urgency(alert_level: str) -> int:
        """Estimate treatment urgency in minutes"""
        
        urgency_map = {
            "RED": 15,      # 15 minutes
            "ORANGE": 60,   # 1 hour
            "YELLOW": 240,  # 4 hours
            "GREEN": 1440   # 24 hours
        }
        
        return urgency_map.get(alert_level, 1440)
    
    @staticmethod
    @pw.udf
    def _calculate_escalation_time(alert_level: str, timestamp: str) -> str:
        """Calculate when alert should be escalated"""
        
        try:
            from datetime import datetime, timedelta
            
            alert_time = datetime.fromisoformat(timestamp)
            
            escalation_minutes = {
                "RED": 5,
                "ORANGE": 15,
                "YELLOW": 60
            }
            
            minutes = escalation_minutes.get(alert_level, 60)
            escalation_time = alert_time + timedelta(minutes=minutes)
            
            return escalation_time.isoformat()
            
        except Exception:
            return timestamp
    
    @staticmethod
    @pw.udf
    def _determine_escalation_target(alert_level: str) -> str:
        """Determine escalation target based on alert level"""
        
        targets = {
            "RED": "attending_physician",
            "ORANGE": "senior_resident", 
            "YELLOW": "resident"
        }
        
        return targets.get(alert_level, "resident")
    
    @staticmethod
    @pw.udf
    def _check_escalation_needed(alert_level: str, timestamp: str) -> bool:
        """Check if alert needs escalation"""
        
        try:
            from datetime import datetime
            
            if alert_level not in ["RED", "ORANGE"]:
                return False
            
            alert_time = datetime.fromisoformat(timestamp)
            current_time = datetime.now()
            
            time_elapsed = (current_time - alert_time).total_seconds() / 60
            
            thresholds = {"RED": 5, "ORANGE": 15}
            threshold = thresholds.get(alert_level, 60)
            
            return time_elapsed >= threshold
            
        except Exception:
            return False
    
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)


def create_app_from_config(config_file: str) -> CriticalAlertApp:
    """
    Create CriticalAlert app from YAML configuration
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        Configured CriticalAlertApp instance
    """
    
    with open(config_file) as f:
        config = pw.load_yaml(f)
    
    return CriticalAlertApp(**config)


if __name__ == "__main__":
    """
    Main entry point for CriticalAlert AI
    
    Usage:
        python app.py                           # Use default config
        python app.py config/custom.yaml       # Use custom config
    """
    
    import sys
    
    # Determine config file
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config/critical_alert_config.yaml"
    
    # Create and run the application
    try:
        app = create_app_from_config(config_file)
        app.run()
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)
