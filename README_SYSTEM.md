# CriticalAlert AI - Complete System

A comprehensive real-time medical document processing and alert system with RAG capabilities, MCP server, WebSocket notifications, and interactive dashboard.

## 🏥 System Components

### 1. **Main RAG Application** (`app.py`)
- **Port**: 49001
- **Purpose**: Core Pathway-based RAG system for medical document processing
- **Features**: 
  - LandingAI structured extraction from radiology reports
  - Real-time document indexing and vector search
  - Claude-powered medical query answering
- **Endpoints**:
  - `POST /v1/pw_ai_answer` - Medical query answering
  - `POST /v1/retrieve` - Document retrieval
  - `POST /v1/statistics` - Processing statistics

### 2. **MCP Server** (`mcp_server_simple.py`)
- **Port**: 8123
- **Purpose**: Model Context Protocol server exposing medical document capabilities
- **Features**:
  - Exposes document store via MCP for AI assistants
  - Real-time access to parsed medical documents
  - Structured medical data retrieval
- **URL**: `http://localhost:8123/mcp/`

### 3. **WebSocket Alert System** (`alert_system.py`)
- **Port**: 8765
- **Purpose**: Real-time critical findings notification system
- **Features**:
  - Monitors extraction results for critical findings
  - WebSocket-based real-time alerts
  - Alert severity levels: RED, ORANGE, YELLOW, GREEN
  - Automatic file system monitoring
- **URL**: `ws://localhost:8765`

### 4. **Streamlit Dashboard** (`dashboard.py`)
- **Port**: 8501
- **Purpose**: Interactive web dashboard for system monitoring
- **Features**:
  - Real-time processing statistics
  - Critical alerts visualization
  - Recent documents table
  - Analytics charts and metrics
  - Auto-refresh capabilities
- **URL**: `http://localhost:8501`

## 🚀 Quick Start

### Prerequisites
1. **Environment Variables** (in `.env` file):
   ```bash
   LANDINGAI_API_KEY=your_landingai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

2. **Python Dependencies**: Already installed in virtual environment
   - pathway
   - streamlit
   - websockets
   - plotly
   - pandas
   - watchdog

### Start the Complete System
```bash
# Start all components automatically
python start_system.py
```

This will start all components in the correct order and provide monitoring.

### Start Components Individually

If you prefer to start components separately:

```bash
# Terminal 1: Main RAG Application
python app.py

# Terminal 2: MCP Server
python mcp_server_simple.py

# Terminal 3: Alert System
python alert_system.py

# Terminal 4: Dashboard
streamlit run dashboard.py --server.port=8501
```

## 📊 System Usage

### 1. **Processing Documents**
- Add PDF radiology reports to `data/incoming/`
- System automatically processes and extracts medical data
- Results saved to `data/extraction_results/`

### 2. **Monitoring via Dashboard**
- Open `http://localhost:8501`
- View real-time processing statistics
- Monitor critical alerts
- Analyze document processing trends

### 3. **Receiving Alerts**
- Critical findings trigger WebSocket alerts
- Connect alert client: `python alert_client.py`
- Alerts categorized by severity (RED/ORANGE/YELLOW/GREEN)

### 4. **Using MCP Server**
- AI assistants can connect to `http://localhost:8123/mcp/`
- Access real-time medical document data
- Perform semantic searches on medical content

### 5. **RAG Queries**
```bash
# Query the medical knowledge base
curl -X POST http://localhost:49001/v1/pw_ai_answer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the findings in the latest elbow X-ray?"}'
```

## 🚨 Alert System

### Alert Levels
- **🔴 RED**: Critical/Emergency - Immediate action required
  - Keywords: emergency, urgent, critical, hemorrhage, infarct, etc.
- **🟠 ORANGE**: Warning - Prompt attention needed  
  - Keywords: abnormal, lesion, mass, fracture, etc.
- **🟡 YELLOW**: Caution - Monitor closely
  - Keywords: mild, slight, minimal, possible, etc.
- **🟢 GREEN**: Normal - No action required
  - Keywords: normal, unremarkable, within normal limits, etc.

### WebSocket Alert Format
```json
{
  "type": "alert",
  "data": {
    "alert_id": "patient123_1234567890",
    "patient_id": "123",
    "study_type": "X-ray",
    "alert_level": "RED",
    "findings": "Critical findings...",
    "impression": "Immediate attention required",
    "critical_findings": "Emergency condition detected",
    "timestamp": "2025-09-28T12:00:00",
    "message": "🚨 CRITICAL ALERT: Patient 123 - X-ray shows critical findings requiring immediate attention!"
  }
}
```

## 🔧 Configuration

### Main Application (`app.yaml`)
- LLM model: Claude 3.5 Sonnet
- Embeddings: SentenceTransformer (all-MiniLM-L12-v2)
- Document processing: LandingAI structured extraction
- Vector search: Brute force KNN with cosine similarity

### System Ports
- **49001**: Main RAG application
- **8123**: MCP server
- **8501**: Streamlit dashboard  
- **8765**: WebSocket alert system

## 📁 Directory Structure
```
CriticalAlertAI/
├── app.py                    # Main RAG application
├── app.yaml                  # Main app configuration
├── mcp_server_simple.py      # MCP server
├── mcp_app.yaml             # MCP configuration
├── alert_system.py          # WebSocket alert system
├── alert_client.py          # Alert client example
├── dashboard.py             # Streamlit dashboard
├── start_system.py          # System startup coordinator
├── src/parsers/
│   └── landingai_parser.py  # LandingAI integration
├── data/
│   ├── incoming/            # PDF documents to process
│   └── extraction_results/  # Processed results
└── .env                     # Environment variables
```

## 🔍 Monitoring & Debugging

### Logs
- All components log to console with timestamps
- Check individual component logs for debugging
- System manager provides centralized monitoring

### Health Checks
- Dashboard shows system status
- Statistics endpoint: `POST /v1/statistics`
- File system monitoring for document processing

### Troubleshooting
1. **Components not starting**: Check environment variables and file permissions
2. **No alerts**: Verify `data/incoming/` has PDF files and extraction is working
3. **Dashboard offline**: Check if main app is running on port 49001
4. **MCP connection issues**: Verify port 8123 is available

## 🎯 Use Cases

1. **Hospital Radiology Department**: Real-time monitoring of radiology reports with immediate alerts for critical findings
2. **AI Assistant Integration**: MCP server allows AI assistants to access medical knowledge base
3. **Research & Analytics**: Dashboard provides insights into document processing patterns
4. **Emergency Response**: WebSocket alerts enable immediate notification systems
5. **Quality Assurance**: Monitor extraction success rates and processing statistics

## 🔒 Security Notes

- System designed for internal hospital networks
- API keys stored in environment variables
- No authentication implemented (add as needed for production)
- WebSocket connections are unencrypted (use WSS in production)

## 📈 Performance

- **Document Processing**: ~10-20 seconds per PDF (depends on LandingAI API)
- **Query Response**: Sub-second for cached queries
- **Real-time Alerts**: Immediate notification upon document processing
- **Dashboard Updates**: Configurable refresh intervals (5-60 seconds)

---

**🏥 CriticalAlert AI - Enhancing Medical Decision Making with Real-Time Intelligence**
