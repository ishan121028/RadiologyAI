#!/usr/bin/env python3

"""
CriticalAlert AI - Real-time Emergency Radiology Alert System

Main application following exact Pathway patterns - similar to demo-question-answering/app.py
but specialized for radiology report processing and critical alert generation.
"""

import logging
import os

import pathway as pw
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, InstanceOf

# Import our custom components
from src.intelligence.critical_alert_answerer import CriticalAlertQuestionAnswerer
# from src.app import CriticalAlertApp

# To use advanced features with Pathway Scale, get your free license key from
# https://pathway.com/features and paste it below.
# To use Pathway Community, comment out the line below.
pw.set_license_key("demo-license-key-with-telemetry")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()

print(os.getenv("LANDINGAI_API_KEY"))
print(os.getenv("GEMINI_API_KEY"))
print(os.getenv("PATHWAY_LICENSE_KEY"))


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


DEBUG_UPDATE_STREAM = _env_flag("PW_DEBUG_UPDATE_STREAM", False)


class App(BaseModel):
    """
    CriticalAlert AI Application
    
    Follows the exact same pattern as demo-question-answering/app.py
    The YAML instantiates the critical_alert_answerer which contains the RadiologyDocumentStore
    """
    
    # This gets instantiated from YAML (just like question_answerer in demo-question-answering)
    critical_alert_answerer: InstanceOf[CriticalAlertQuestionAnswerer]
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 49000
    
    # Caching and persistence (same as other apps)
    with_cache: bool = True
    terminate_on_error: bool = False
    debug_update_stream: bool = DEBUG_UPDATE_STREAM
    
    def run(self) -> None:
        """
        Run the CriticalAlert AI application
        
        This is where the actual Pathway computation graph gets set up
        Similar to QASummaryRestServer.run() in existing examples
        """
        
        # Get the real-time critical alerts stream from the answerer
        # This internally uses the RadiologyDocumentStore that was instantiated from YAML
        critical_alerts = self.critical_alert_answerer.get_critical_alerts_stream()
        
        # Filter for immediate action alerts (RED level) - simplified filtering
        immediate_alerts = critical_alerts.filter(pw.this.alert_level == "RED")

        # Get processing statistics
        stats = self.critical_alert_answerer.get_processing_statistics()

        if self.debug_update_stream:
            logging.info("PW_DEBUG_UPDATE_STREAM enabled - printing update stream and exiting")
            pw.debug.compute_and_print_update_stream(
                critical_alerts,
                immediate_alerts,
                stats,
                include_id=True,
                short_pointers=True,
                terminate_on_error=self.terminate_on_error,
            )
            return

        # Set up real-time monitoring and outputs
        # Debug all critical alerts (simplified version)
        critical_alerts.debug("critical_alerts")
        
        # Debug immediate action alerts
        immediate_alerts.debug("immediate_alerts")
        
        # Debug processing statistics
        stats.debug("processing_stats")
        
        # Create a single webserver instance for all endpoints
        webserver = pw.io.http.PathwayWebserver(host=self.host, port=self.port)
        
        # Set up REST endpoint for querying critical alerts
        class QuerySchema(pw.Schema):
            query: str
        
        query_table, response_writer = pw.io.http.rest_connector(
            webserver=webserver,
            route="/api/query",
            schema=QuerySchema,
            autocommit_duration_ms=50,
            delete_completed_queries=True,
        )
        
        # Process queries using the actual critical alert answerer
        query_responses = query_table.select(
            query_id=pw.this.id,
            result=pw.apply(
                self.critical_alert_answerer.answer_single_query,
                pw.this.query
            )
        )
        
        response_writer(query_responses)
        
        # Add health check endpoint
        class HealthSchema(pw.Schema):
            check: str
        
        health_table, health_writer = pw.io.http.rest_connector(
            webserver=webserver,
            route="/health",
            schema=HealthSchema,
            methods=["GET", "POST"],
            autocommit_duration_ms=50,
            delete_completed_queries=True,
        )
        
        health_responses = health_table.select(
            query_id=pw.this.id,
            result={
                "status": "healthy",
                "service": "CriticalAlert AI",
                "streaming": "active",
                "endpoints": ["/api/query", "/api/search", "/health"]
            }
        )
        
        health_writer(health_responses)
        
        # Add RAG search endpoint for document retrieval
        class SearchSchema(pw.Schema):
            query: str
            limit: int
        
        search_table, search_writer = pw.io.http.rest_connector(
            webserver=webserver,
            route="/api/search",
            schema=SearchSchema,
            autocommit_duration_ms=50,
            delete_completed_queries=True,
        )
        
        # Process RAG searches using document store retrieval
        search_responses = search_table.select(
            query_id=pw.this.id,
            result=pw.apply(
                self.critical_alert_answerer.search_documents,
                pw.this.query,
                pw.this.limit
            )
        )
        
        search_writer(search_responses)
        
        logging.info(f"🚀 CriticalAlert AI started on http://{self.host}:{self.port}")
        logging.info("📡 Available REST endpoints:")
        logging.info("  POST /api/query - Query critical alerts with RAG")
        logging.info("  POST /api/search - RAG-based document search")
        logging.info("  GET  /health - Health check")
        logging.info("🔄 Monitoring for critical radiology alerts...")
        
        # Run Pathway computation (same as existing examples)
        pw.run(
            monitoring_level=pw.MonitoringLevel.ALL,
            terminate_on_error=self.terminate_on_error,
        )

    @classmethod
    def from_config(cls, config: dict) -> "App":
        """Instantiate App from YAML config while honoring debug overrides."""

        config = dict(config)
        debug_override = config.pop("debug_update_stream", None)
        instance = cls(**config)
        if debug_override is not None:
            instance.debug_update_stream = bool(debug_override)
        return instance

    model_config = ConfigDict(extra="forbid")


if __name__ == "__main__":
    # EXACT same pattern as demo-question-answering/app.py
    with open("app.yaml") as f:
        config = pw.load_yaml(f)
    app = App.from_config(config)
    app.run()
