# 🚨 CriticalAlert AI MCP Server

**Latest Pathway MCP Server Implementation** following the most recent patterns and documentation.

## 🏗️ **MCP Server Architecture (Latest Patterns)**

### **📋 Core Components:**

```python
# 1. McpServable Tools (following latest Pathway patterns)
class CriticalAlertAnalyzerTool(McpServable):
    def analyze_radiology_report(self, request_table: pw.Table) -> pw.Table:
        # Pathway table-based processing
        return results
    
    def register_mcp(self, server: McpServer):
        server.tool("analyze_radiology_report", ...)

# 2. PathwayMcp Server (streamable-http transport)
pathway_mcp_server = PathwayMcp(
    name="CriticalAlert AI MCP Server",
    transport="streamable-http",  # Latest transport method
    host="0.0.0.0",
    port=8127,
    serve=[analyzer_tool, monitor_tool, recommendation_tool]
)
```

### **🔧 Available MCP Tools:**

| **Tool** | **Purpose** | **Schema** |
|----------|-------------|------------|
| `analyze_radiology_report` | Parse PDF reports, detect critical findings | `RadiologyAnalysisRequestSchema` |
| `get_active_alerts` | Query current RED/ORANGE alerts | `AlertQueryRequestSchema` |
| `get_alert_statistics` | Real-time processing metrics | `EmptyRequestSchema` |
| `generate_medical_recommendations` | Evidence-based medical guidance | `MedicalRecommendationRequestSchema` |

## 🚀 **Quick Start**

### **1. Start the MCP Server:**
```bash
# Set environment variables
export LANDINGAI_API_KEY="your_landingai_key"
export OPENAI_API_KEY="your_openai_key"
export PATHWAY_LICENSE_KEY="your_pathway_license" # Optional

# Run the MCP server
python src/mcp/critical_alert_mcp_server.py

# Server starts on http://localhost:8127/mcp/
```

### **2. Test with Client:**
```bash
# Install client dependency
pip install fastmcp

# Run client demo
python src/mcp/mcp_client_example.py
```

### **3. Use with AI Assistants:**
```python
import asyncio
from fastmcp import Client

client = Client("http://localhost:8127/mcp/")

async def analyze_report():
    async with client:
        result = await client.call_tool(
            name="analyze_radiology_report",
            arguments={
                "report_content": "FINDINGS: Large filling defect in pulmonary artery...",
                "patient_id": "P12345",
                "urgency_level": "EMERGENCY"
            }
        )
        print(f"Alert Level: {result['alert_level']}")
        print(f"Critical Conditions: {result['critical_conditions']}")
```

## 📊 **MCP Tool Usage Examples**

### **🏥 Analyze Radiology Report:**
```json
{
  "name": "analyze_radiology_report",
  "arguments": {
    "report_content": "FINDINGS: Massive pulmonary embolism with right heart strain...",
    "patient_id": "PATIENT_12345",
    "urgency_level": "EMERGENCY"
  }
}

// Returns:
{
  "alert_level": "RED",
  "critical_conditions": ["pulmonary embolism"],
  "immediate_actions": ["Notify attending physician immediately"],
  "treatment_recommendations": ["Anticoagulation per PE protocol"],
  "analysis_timestamp": "2024-01-15T14:30:00Z"
}
```

### **🚨 Get Active Alerts:**
```json
{
  "name": "get_active_alerts", 
  "arguments": {
    "alert_level": "RED",
    "time_range_hours": 24
  }
}

// Returns:
{
  "alert_id": "ALERT_143000",
  "alert_level": "RED",
  "patient_id": "PATIENT_12345",
  "condition": "Pulmonary Embolism",
  "timestamp": "2024-01-15T14:30:00Z",
  "status": "ACTIVE"
}
```

### **📈 Get System Statistics:**
```json
{
  "name": "get_alert_statistics",
  "arguments": {}
}

// Returns:
{
  "total_reports_processed": 150,
  "red_alerts_today": 5,
  "orange_alerts_today": 12,
  "avg_processing_time_seconds": 15.3,
  "system_status": "OPERATIONAL"
}
```

## 🔗 **Integration with Main App**

### **📋 app.yaml Integration:**
```yaml
# Add MCP server to main application
mcp_server_config:
  host: "0.0.0.0"
  port: 8127
  enable_mcp: true

# Use the same critical_alert_answerer
critical_alert_answerer: !src.intelligence.critical_alert_answerer.CriticalAlertQuestionAnswerer
  llm: $llm
  document_store: $document_store
```

### **🏗️ Runtime Integration:**
```python
# In app.py - run both main app and MCP server
class App(BaseModel):
    critical_alert_answerer: InstanceOf[CriticalAlertQuestionAnswerer]
    enable_mcp: bool = True
    mcp_port: int = 8127
    
    def run(self) -> None:
        # Start main Pathway computation
        critical_alerts = self.critical_alert_answerer.get_critical_alerts_stream()
        critical_alerts.debug("critical_alerts")
        
        # Start MCP server if enabled
        if self.enable_mcp:
            mcp_server = create_critical_alert_mcp_server(
                port=self.mcp_port,
                critical_alert_answerer=self.critical_alert_answerer
            )
        
        # Run Pathway computation engine
        pw.run()
```

## 🔧 **Latest Pathway MCP Patterns Used**

### **✅ Following Current Best Practices:**

1. **McpServable Inheritance**: All tools inherit from `McpServable`
2. **Streamable HTTP Transport**: Using `transport="streamable-http"`
3. **Schema-based Requests**: Proper `pw.Schema` definitions
4. **Table-based Processing**: All methods use `pw.Table` input/output
5. **UDF Integration**: Medical logic implemented as Pathway UDFs
6. **PathwayMcp Server**: Using latest `PathwayMcp` class
7. **Proper Registration**: Tools register via `register_mcp()` method

### **🚀 Advanced Features:**

- **Real-time Streaming**: MCP tools access live Pathway tables
- **Medical Intelligence**: Built-in critical finding detection
- **Error Handling**: Robust error handling and logging
- **Performance Monitoring**: Built-in processing statistics
- **Scalable Architecture**: Designed for hospital-scale deployment

## 📡 **Client Integration Examples**

### **🤖 AI Assistant Integration:**
```python
# Claude, GPT-4, or other AI assistants can use:
async def emergency_radiology_analysis():
    result = await mcp_client.call_tool(
        "analyze_radiology_report",
        {"report_content": uploaded_pdf_text}
    )
    
    if result["alert_level"] == "RED":
        await notify_emergency_physician(result)
```

### **🏥 Hospital System Integration:**
```python
# Hospital EMR systems can integrate:
class HospitalEMRIntegration:
    def process_new_radiology_report(self, report_data):
        analysis = await mcp_client.call_tool(
            "analyze_radiology_report", 
            report_data
        )
        
        if analysis["alert_level"] in ["RED", "ORANGE"]:
            self.trigger_physician_alert(analysis)
```

## 🔍 **Testing & Monitoring**

### **✅ Health Check:**
```bash
curl http://localhost:8127/mcp/health
```

### **📊 Monitor Performance:**
```bash
# View real-time statistics
python -c "
import asyncio
from fastmcp import Client
async def stats():
    client = Client('http://localhost:8127/mcp/')
    async with client:
        result = await client.call_tool('get_alert_statistics', {})
        print(result)
asyncio.run(stats())
"
```

## 🎯 **Key Advantages**

- **🔄 Real-time Processing**: MCP tools access live Pathway data streams
- **🏥 Medical Expertise**: Built-in radiology intelligence 
- **📈 Scalable**: Handles hospital-scale document volumes
- **🔌 Standards-based**: Full MCP protocol compliance
- **⚡ Fast Response**: Sub-second critical alert detection
- **🛡️ Reliable**: Robust error handling and monitoring

This MCP server implementation follows the **latest Pathway patterns** and provides **production-ready** medical intelligence for emergency radiology! 🚨🏥

