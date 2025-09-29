# Radiology AI

Real-time radiology document processing with AI-powered analysis and RAG (Retrieval-Augmented Generation) capabilities.

## Overview

This system processes radiology reports in real-time, extracts structured medical data, and provides intelligent query answering with critical finding detection. Built on Pathway's streaming data processing framework with LandingAI for document parsing.

## Key Features

- **Real-time Processing**: Streams incoming radiology reports as they arrive
- **AI-Powered Parsing**: Uses LandingAI for structured medical data extraction
- **RAG Query System**: Advanced question answering over medical documents
- **Medical Intelligence**: Specialized radiology report understanding
- **REST API**: Complete HTTP endpoints for integration
- **MCP Server**: Model Context Protocol for external tool access
- **High Performance**: Pathway-powered streaming architecture

## Quick Start

### Prerequisites

- Python 3.9+
- LandingAI API key
- Anthropic API key 

You can customize the LLM model in app.yaml please check out pathway.xpacks.llm.llms for more details.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ishan121028/RadiologyAI.git
cd RadiologyAI

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate 

# 3. Install dependencies
pip install requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Configuration

Create a `.env` file with:

```bash
PATHWAY_LICENSE_KEY="pathway-license-key"
LANDINGAI_API_KEY="your-landing-ai-api-key"
VISION_AGENT_API_KEY="your-landing-ai-api-key"
ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Running the Application

```bash
# 1. Create data directories
mkdir -p data/incoming data/processed

# 2. Start the application
python app.py

# 3. Add PDF radiology reports to data/incoming/
# 4. Access the API at http://localhost:49001
# 5. Access the mcp server at http://localhost:8123/mcp
```

## 📁 Project Structure

```
├── app.py                              # Main application entry point
├── app.yaml                           # Application configuration
├── src/
│   ├── __init__.py                    # Package initialization
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── landingai_parser.py        # LandingAI document parser
│   ├── intelligence/
│   │   ├── __init__.py
│   │   └── critical_alert_answerer.py # RAG question answerer
│   ├── store/
│   │   └── RadiologyDocumentStore.py  # Document store with MCP tools
│   └── server/
│       └── RadiologyServer.py         # REST API server
├── data/
│   ├── incoming/                      # Drop PDF files here
│   └── processed/                     # Processed documents
└── Cache/                             # Pathway cache directory
```

## 🔌 API Endpoints

### Standard RAG Endpoints

- **POST** `/v1/retrieve` - Semantic document search
- **POST** `/v1/statistics` - System statistics
- **POST** `/v1/pw_list_documents` - List all documents
- **POST** `/v1/pw_ai_answer` - AI question answering
- **POST** `/v2/answer` - Enhanced question answering

### Patient-Specific Endpoints

- **POST** `/v1/search_patient_by_id` - Search by patient ID
- **POST** `/v1/query_patient_extraction` - Query patient extraction data

### Example API Calls

```bash
# Search for documents
curl -X POST "http://localhost:49001/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"query": "brain tumor", "k": 5}'

# Get system statistics
curl -X POST "http://localhost:49001/v1/statistics" \
  -H "Content-Type: application/json" \
  -d '{}'

# Search specific patient
curl -X POST "http://localhost:49001/v1/search_patient_by_id" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "12345"}'

# Ask AI question
curl -X POST "http://localhost:49001/v2/answer" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the critical findings in recent MRI scans?"}'
```

## 🔧 Configuration

The application uses `app.yaml` for configuration following Pathway's standard patterns:

```yaml
# Data sources
$sources:
  - !pw.io.fs.read
    path: data/incoming
    format: binary
    with_metadata: true
    mode: streaming

# LandingAI parser
$parser: !src.parsers.landingai_parser.LandingAIRadiologyParser
  api_key: $LANDINGAI_API_KEY
  cache_strategy: !pw.udfs.DefaultCache {}

# Document processing
$document_store: !src.store.RadiologyDocumentStore.RadiologyDocumentStore
  data_sources: $sources
  parser: $parser

# Question answerer
question_answerer: !src.intelligence.critical_alert_answerer.RadiologyQuestionAnswerer
  llm: $llm
  indexer: $document_store

# Server settings
host: "0.0.0.0"
port: 49001
```

## 🩺 Medical Data Processing

### Supported Document Types

- **CT Scans**: Computed Tomography reports
- **MRI Reports**: Magnetic Resonance Imaging
- **X-Ray Reports**: Radiographic findings
- **Ultrasound**: Sonographic reports
- **Nuclear Medicine**: SPECT, PET scans

### Extracted Medical Fields

- Patient ID and demographics
- Study type and modality
- Clinical findings
- Impressions and diagnoses
- Critical findings requiring immediate attention
- Radiologist recommendations

### Critical Finding Detection

The system automatically identifies and prioritizes:

- **RED**: Life-threatening conditions (PE, hemorrhage, pneumothorax)
- **ORANGE**: Urgent findings requiring prompt attention
- **YELLOW**: Significant findings needing follow-up
- **GREEN**: Routine findings

## 🔌 MCP (Model Context Protocol) Integration

The system exposes tools via MCP for external access:

```python
# Available MCP tools
- retrieve_query: Document retrieval
- statistics_query: System statistics  
- inputs_query: Document listing
- search_patient_by_id: Patient search
- query_patient_extraction: Patient data extraction
```

Access MCP server at: `http://localhost:49001/mcp/`

## 🛠️ Development

### Adding New Parsers

```python
# Create new parser in src/parsers/
class CustomParser(pw.UDF):
    def __call__(self, contents: bytes, **kwargs) -> dict:
        # Your parsing logic
        return parsed_data
```

### Extending Medical Intelligence

```python
# Add medical analysis in src/intelligence/
class CustomMedicalAnalyzer:
    def analyze_findings(self, text: str) -> dict:
        # Your medical analysis logic
        return analysis_results
```

### Custom MCP Tools

```python
# Add MCP tools in src/store/RadiologyDocumentStore.py
@pw.table_transformer
def my_custom_tool(self, request_table: pw.Table) -> pw.Table:
    # Your custom tool logic
    return results
```

## 📊 Monitoring and Debugging

### Enable Debug Mode

```bash
# Set environment variables for debugging
export PW_DEBUG_UPDATE_STREAM=1
export PATHWAY_LOGGING_LEVEL=DEBUG
export PW_MONITORING_LEVEL=DEBUG

python app.py
```

### Performance Monitoring

The system provides real-time metrics:

- Document processing rate
- Parse success/failure rates
- Query response times
- Critical alert frequencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions or some bug in my code, please raise a ticket in Github Issues I would love to chat with you.

## Deployment

### Production Deployment

```bash
# 1. Set production environment variables
export ENVIRONMENT=production
export HOST=0.0.0.0
export PORT=80

# 2. Use production-grade WSGI server
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:80

# 3. Set up reverse proxy (nginx recommended)
# 4. Configure SSL certificates
# 5. Set up monitoring and logging
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 49001

CMD ["python", "app.py"]
```

---

**Built with ❤️ using [Pathway](https://pathway.com) and [LandingAI](https://landing.ai)**