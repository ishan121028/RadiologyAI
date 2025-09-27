#!/usr/bin/env python3

"""
CriticalAlert AI - Usage Examples

This demonstrates how to use the LandingAI parser with Pathway
for real-time radiology report processing.
"""

import pathway as pw
import logging
from pathlib import Path
import os

# Import our custom parser
from src.parsers.landingai_parser import (
    LandingAIRadiologyParser, 
    RadiologyDocumentStore,
    create_landingai_radiology_parser
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def basic_usage_example():
    """
    Basic usage example - similar to how DoclingParser is used
    """
    
    print("=== Basic Usage Example ===")
    
    # Create data source - monitor incoming radiology reports
    radiology_reports = pw.io.fs.read(
        path="data/incoming",
        format="binary", 
        with_metadata=True,
        mode="streaming"  # Real-time monitoring
    )
    
    # Create LandingAI parser (similar to DoclingParser)
    parser = LandingAIRadiologyParser(
        api_key=os.getenv("LANDINGAI_API_KEY", "demo-key"),
        cache_strategy=pw.udfs.DefaultCache(),
        confidence_threshold=0.7
    )
    
    # Parse documents - just like using DoclingParser
    parsed_reports = radiology_reports.select(
        # Original fields
        *radiology_reports,
        
        # Parsed content using our parser
        parsed_content=parser(pw.this.data, pw.this._metadata)
    )
    
    # Extract key medical information
    medical_data = parsed_reports.select(
        filename=pw.this._metadata["path"],
        patient_id=pw.this.parsed_content["patient_id"],
        study_type=pw.this.parsed_content["study_type"],
        findings=pw.this.parsed_content["findings"],
        impression=pw.this.parsed_content["impression"],
        critical_findings=pw.this.parsed_content["critical_findings"],
        parsing_success=pw.this.parsed_content["parsing_metadata"]["success"]
    ).filter(
        pw.this.parsing_success == True
    )
    
    # Debug output
    medical_data.debug("parsed_radiology_reports")
    
    print("Basic usage pipeline created. Run with pw.run() to process files.")


def advanced_pipeline_example():
    """
    Advanced usage with complete medical pipeline
    """
    
    print("=== Advanced Pipeline Example ===")
    
    # Multiple data sources
    incoming_reports = pw.io.fs.read(
        path="data/incoming",
        format="binary",
        with_metadata=True,
        mode="streaming"
    )
    
    batch_reports = pw.io.fs.read(
        path="data/batch",
        format="binary", 
        with_metadata=True
    )
    
    # Create parser with custom configuration
    parser = create_landingai_radiology_parser(
        api_key=os.getenv("LANDINGAI_API_KEY", "demo-key"),
        cache_strategy=pw.udfs.DefaultCache(),
        confidence_threshold=0.8,
        async_mode="fully_async"
    )
    
    # Create RadiologyDocumentStore (similar to DocumentStore)
    doc_store = RadiologyDocumentStore(
        data_sources=[incoming_reports, batch_reports],
        landingai_api_key=os.getenv("LANDINGAI_API_KEY", "demo-key"),
        cache_strategy=pw.udfs.DefaultCache()
    )
    
    # Get critical alerts
    critical_alerts = doc_store.get_critical_alerts()
    
    # Add alert classification
    classified_alerts = critical_alerts.select(
        *critical_alerts,
        alert_level=classify_alert_level(pw.this.critical_findings),
        requires_immediate_action=requires_immediate_action(pw.this.critical_findings),
        alert_id=generate_alert_id()
    )
    
    # Filter for immediate action alerts
    immediate_alerts = classified_alerts.filter(
        pw.this.requires_immediate_action == True
    )
    
    # Get processing statistics
    stats = doc_store.get_processing_stats()
    
    # Debug outputs
    immediate_alerts.debug("immediate_action_alerts")
    stats.debug("processing_statistics")
    
    print("Advanced pipeline created with critical alert detection.")


def yaml_configuration_example():
    """
    Example using YAML configuration (like existing Pathway apps)
    """
    
    print("=== YAML Configuration Example ===")
    
    # This shows how to use the parser in a YAML config file
    yaml_config = """
# Similar to app.yaml files in existing examples
$sources:
  - !pw.io.fs.read
    path: data/incoming
    format: binary
    with_metadata: true
    mode: streaming

$landingai_parser: !src.parsers.landingai_parser.LandingAIRadiologyParser
  api_key: $LANDINGAI_API_KEY
  cache_strategy: !pw.udfs.DefaultCache {}
  confidence_threshold: 0.7

$radiology_document_store: !src.parsers.landingai_parser.RadiologyDocumentStore
  data_sources: $sources
  landingai_api_key: $LANDINGAI_API_KEY
  cache_strategy: !pw.udfs.DefaultCache {}
"""
    
    print("YAML Configuration:")
    print(yaml_config)
    
    # Load and use configuration
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_config)
            temp_config_path = f.name
        
        # Load configuration (in real usage)
        # with open(temp_config_path) as f:
        #     config = pw.load_yaml(f)
        #     doc_store = config['radiology_document_store']
        
        print(f"Configuration saved to: {temp_config_path}")
        
    except Exception as e:
        print(f"Configuration example: {e}")


def real_time_monitoring_example():
    """
    Real-time monitoring example with alert generation
    """
    
    print("=== Real-time Monitoring Example ===")
    
    # Create streaming data source
    radiology_stream = pw.io.fs.read(
        path="data/incoming",
        format="binary",
        with_metadata=True, 
        mode="streaming"
    )
    
    # Create parser
    parser = LandingAIRadiologyParser(
        api_key=os.getenv("LANDINGAI_API_KEY", "demo-key"),
        cache_strategy=pw.udfs.DefaultCache()
    )
    
    # Real-time processing pipeline
    processed_stream = parser.create_medical_pipeline(radiology_stream)
    
    # Generate real-time alerts
    alert_stream = processed_stream.select(
        *processed_stream,
        alert_level=classify_alert_level(pw.this.critical_findings),
        alert_timestamp=pw.now(),
        needs_escalation=pw.apply(
            lambda findings: len(findings) > 0 and any(
                critical in " ".join(findings).lower() 
                for critical in ["pulmonary embolism", "aortic dissection", "hemorrhage"]
            ),
            pw.this.critical_findings
        )
    )
    
    # Real-time statistics
    stats_stream = alert_stream.groupby().reduce(
        total_alerts=pw.reducers.count(),
        critical_alerts=pw.reducers.sum(
            pw.if_else(pw.this.alert_level == "RED", 1, 0)
        ),
        avg_processing_time=pw.reducers.avg(pw.this.processing_time),
        latest_alert=pw.reducers.latest(pw.this.alert_timestamp)
    )
    
    # Output streams
    alert_stream.debug("real_time_alerts")
    stats_stream.debug("real_time_statistics")
    
    print("Real-time monitoring pipeline created.")


def integration_with_mcp_example():
    """
    Example of integrating with MCP server
    """
    
    print("=== MCP Integration Example ===")
    
    # This shows how the parser integrates with MCP servers
    integration_example = """
from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp

class RadiologyAnalyzerTool(McpServable):
    def __init__(self):
        self.parser = LandingAIRadiologyParser(
            api_key=os.getenv("LANDINGAI_API_KEY")
        )
    
    def analyze_radiology_report(self, report_table: pw.Table) -> pw.Table:
        # Use our parser in MCP tool
        return self.parser.create_medical_pipeline(report_table)
    
    def register_mcp(self, server: McpServer):
        server.tool(
            "analyze_radiology_report",
            request_handler=self.analyze_radiology_report,
            schema=RadiologyReportSchema
        )

# MCP Server with radiology tools
radiology_mcp_server = PathwayMcp(
    name="CriticalAlert AI MCP Server", 
    transport="streamable-http",
    host="0.0.0.0",
    port=8127,
    serve=[RadiologyAnalyzerTool()]
)
"""
    
    print("MCP Integration Code:")
    print(integration_example)


# UDFs for examples
@pw.udf
def classify_alert_level(critical_findings: list) -> str:
    """Classify alert level based on findings"""
    
    if not critical_findings:
        return "GREEN"
    
    findings_text = " ".join(critical_findings).lower()
    
    red_conditions = ["pulmonary embolism", "aortic dissection", "hemorrhage"]
    orange_conditions = ["pneumonia", "fracture", "mass"]
    
    for condition in red_conditions:
        if condition in findings_text:
            return "RED"
    
    for condition in orange_conditions:
        if condition in findings_text:
            return "ORANGE"
    
    return "YELLOW"


@pw.udf  
def requires_immediate_action(critical_findings: list) -> bool:
    """Check if immediate action is required"""
    
    immediate_conditions = [
        "pulmonary embolism", "aortic dissection", "hemorrhage",
        "tension pneumothorax", "cardiac tamponade"
    ]
    
    findings_text = " ".join(critical_findings).lower()
    
    return any(condition in findings_text for condition in immediate_conditions)


@pw.udf
def generate_alert_id() -> str:
    """Generate unique alert ID"""
    
    import uuid
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"ALERT_{timestamp}_{unique_id}"


def main():
    """
    Run all examples
    """
    
    print("CriticalAlert AI - LandingAI Parser Usage Examples")
    print("=" * 60)
    
    # Run examples
    basic_usage_example()
    print()
    
    advanced_pipeline_example()
    print()
    
    yaml_configuration_example()
    print()
    
    real_time_monitoring_example()
    print()
    
    integration_with_mcp_example()
    print()
    
    print("=" * 60)
    print("All examples completed!")
    print()
    print("To run actual processing:")
    print("1. Set LANDINGAI_API_KEY environment variable")
    print("2. Create data/incoming directory with PDF files")
    print("3. Run: pw.run() to start processing")
    print()
    print("Key differences from DoclingParser:")
    print("✅ Specialized for radiology reports")
    print("✅ Built-in critical finding detection")
    print("✅ Real-time alert classification")
    print("✅ Medical entity extraction")
    print("✅ Integration with emergency workflows")


if __name__ == "__main__":
    main()
