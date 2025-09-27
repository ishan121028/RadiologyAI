# 🚨 CriticalAlert AI - Complete Setup Guide

## 🚀 **Quick Start (5 Minutes)**

### **1. Clone and Navigate:**
```bash
cd /Users/iupadhyay/adobe/repos/pathway-mcp/CriticalAlertAI
```

### **2. Install Dependencies:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using uv (recommended for faster installation)
uv pip install -r requirements.txt
```

### **3. Set Environment Variables:**
```bash
# Required for LandingAI
export LANDINGAI_API_KEY="your_landingai_api_key_here"

# Required for OpenAI (LLM features)
export OPENAI_API_KEY="your_openai_api_key_here"

# Optional: Pathway license for advanced features
export PATHWAY_LICENSE_KEY="your_pathway_license_key"

# Optional: Save to .bashrc or .zshrc for persistence
echo 'export LANDINGAI_API_KEY="your_key"' >> ~/.bashrc
echo 'export OPENAI_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

### **4. Create Data Directories:**
```bash
mkdir -p data/incoming
mkdir -p data/processed  
mkdir -p data/alerts
mkdir -p data/test_reports
```

### **5. Test Installation:**
```bash
python examples/landingai_parser_example.py
```

## 📋 **Detailed Setup Instructions**

### **Environment Requirements:**
```bash
# Check Python version (3.8+ required)
python3 --version

# Check pip version
pip --version

# Create virtual environment (recommended)
python3 -m venv criticalalert_env
source criticalalert_env/bin/activate  # On Windows: criticalalert_env\Scripts\activate
```

### **Install Core Dependencies:**
```bash
# Core Pathway and AI libraries
pip install pathway[all]>=0.13.0
pip install agentic-doc>=0.2.4
pip install openai>=1.0.0
pip install pydantic>=2.0.0

# Document processing
pip install PyPDF2>=3.0.0
pip install python-dotenv>=1.0.0

# MCP Server support
pip install fastmcp>=0.1.0

# Web frameworks
pip install streamlit>=1.28.0
pip install fastapi>=0.104.0
pip install uvicorn>=0.24.0

# Or install everything at once
pip install -r requirements.txt
```

### **Get API Keys:**

#### **1. LandingAI API Key:**
- Go to [LandingAI](https://landing.ai/)
- Sign up for an account
- Navigate to API settings
- Copy your API key

#### **2. OpenAI API Key:**
- Go to [OpenAI](https://platform.openai.com/api-keys)
- Create an account or sign in
- Generate a new API key
- Copy the key

#### **3. Pathway License (Optional):**
- Go to [Pathway Features](https://pathway.com/features)
- Get your free license key
- For community use, you can skip this

## 🏃 **Running the System**

### **Option 1: Main Application (Real-time Processing)**
```bash
# Run the main CriticalAlert AI application
python app.py

# Or with custom configuration
python app.py examples/minimal_app.yaml

# Expected output:
# INFO Starting CriticalAlert AI on 0.0.0.0:8000
# INFO Monitoring for critical radiology alerts...
# INFO Starting Pathway computation engine...
```

### **Option 2: MCP Server (For AI Assistants)**
```bash
# Run the MCP server
python src/mcp/critical_alert_mcp_server.py

# Expected output:
# INFO 🚨 Starting CriticalAlert AI MCP Server...
# INFO 🚀 CriticalAlert AI MCP Server running on http://0.0.0.0:8127/mcp/
# INFO Available tools:
# INFO   - analyze_radiology_report
# INFO   - get_active_alerts
# INFO   - get_alert_statistics
# INFO   - generate_medical_recommendations
```

### **Option 3: Test Examples**
```bash
# Test LandingAI parser
python examples/landingai_parser_example.py

# Test MCP client
python src/mcp/mcp_client_example.py

# Run usage examples
python examples/usage_example.py

# Test runtime wiring
python examples/simple_runtime_example.py setup
python examples/simple_runtime_example.py run
```

## 📁 **Directory Structure Setup**

### **Required Directories:**
```bash
CriticalAlertAI/
├── data/
│   ├── incoming/          # Drop PDF reports here
│   ├── processed/         # Processed reports
│   ├── alerts/            # Critical alerts
│   └── test_reports/      # Test data
├── src/                   # Source code
├── examples/              # Usage examples
├── config/               # Configuration files
└── requirements.txt      # Dependencies
```

### **Create Structure:**
```bash
mkdir -p data/{incoming,processed,alerts,test_reports}
mkdir -p logs
mkdir -p cache
```

## 🧪 **Testing the Setup**

### **1. Test LandingAI Parser:**
```bash
python examples/landingai_parser_example.py

# Expected output:
# 🚨 CriticalAlert AI - Corrected LandingAI Parser Demo
# ✅ agentic_doc library is available
# ✅ LandingAI parser initialized successfully
# ✅ Created Pathway file source
# 🎉 LandingAI parser successfully updated!
```

### **2. Test MCP Server:**
```bash
# Terminal 1: Start MCP server
python src/mcp/critical_alert_mcp_server.py

# Terminal 2: Test client
python src/mcp/mcp_client_example.py

# Expected client output:
# 🏥 Testing Radiology Analysis Tool
# ✅ Analysis Results:
# 🚨 Alert Level: RED
# 🔍 Critical Conditions: ['pulmonary embolism']
```

### **3. Test Main Application:**
```bash
# Start main app
python app.py

# In another terminal, add a test file
echo "Test radiology report with pulmonary embolism" > data/incoming/test_report.txt

# Check logs for processing
```

## 📊 **Real-time Usage**

### **1. Process Radiology Reports:**
```bash
# Start the system
python app.py

# Drop PDF reports into data/incoming/
cp your_radiology_report.pdf data/incoming/

# Watch real-time alerts in console:
# critical_alerts: 
# +---+------------------------+-------------+
# |id |filename                |alert_level  |
# +---+------------------------+-------------+
# |1  |radiology_report.pdf    |RED          |
```

### **2. Use MCP Tools with AI Assistants:**
```bash
# Start MCP server
python src/mcp/critical_alert_mcp_server.py

# AI assistants can now call:
# - analyze_radiology_report
# - get_active_alerts  
# - get_alert_statistics
# - generate_medical_recommendations
```

## 🔧 **Configuration Options**

### **Environment Variables:**
```bash
# Core settings
export LANDINGAI_API_KEY="your_key"
export OPENAI_API_KEY="your_key"  
export PATHWAY_LICENSE_KEY="your_key"

# Server settings
export PATHWAY_PORT=8000
export PATHWAY_HOST="0.0.0.0"
export MCP_PORT=8127

# Processing settings
export MAX_PROCESSING_TIME=30
export ENABLE_REAL_TIME_ALERTS=true
export ALERT_ESCALATION_ENABLED=true

# Notification services (optional)
export TWILIO_ACCOUNT_SID="your_sid"
export TWILIO_AUTH_TOKEN="your_token"
export FIREBASE_SERVER_KEY="your_key"
```

### **Configuration Files:**
```bash
# Use custom app.yaml
python app.py config/custom_config.yaml

# Use minimal configuration
python app.py examples/minimal_app.yaml
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. "agentic_doc not found"**
```bash
pip install agentic-doc>=0.2.4
# or
pip install --upgrade agentic-doc
```

#### **2. "LANDINGAI_API_KEY not set"**
```bash
export LANDINGAI_API_KEY="your_actual_api_key"
# Check: echo $LANDINGAI_API_KEY
```

#### **3. "No module named 'pathway'"**
```bash
pip install pathway[all]
# or  
pip install --upgrade pathway
```

#### **4. "Permission denied" for directories**
```bash
chmod -R 755 data/
mkdir -p data/incoming data/processed data/alerts
```

#### **5. "MCP server connection refused"**
```bash
# Check if server is running
lsof -i :8127
# Restart server
python src/mcp/critical_alert_mcp_server.py
```

### **Debug Mode:**
```bash
# Run with verbose logging
python app.py --log-level DEBUG

# Check Pathway computation
export PATHWAY_MONITORING_LEVEL=ALL
python app.py
```

## 📈 **Performance Optimization**

### **1. Enable Caching:**
```bash
# Pathway will create cache automatically
export PATHWAY_CACHE_ENABLED=true
# Cache directory: PathwayCache/
```

### **2. Use UV for Fast Package Management:**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies faster
uv pip install -r requirements.txt
```

### **3. Resource Monitoring:**
```bash
# Monitor system resources
htop

# Monitor Pathway performance
# Check logs for processing times
tail -f logs/criticalalert.log
```

## 🎯 **Production Deployment**

### **1. Docker Setup (Optional):**
```bash
# Create Dockerfile (example)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8127
CMD ["python", "app.py"]
```

### **2. Systemd Service:**
```bash
# Create service file
sudo nano /etc/systemd/system/criticalalert.service

# Service content:
[Unit]
Description=CriticalAlert AI Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/CriticalAlertAI
Environment=LANDINGAI_API_KEY=your_key
Environment=OPENAI_API_KEY=your_key
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable criticalalert
sudo systemctl start criticalalert
```

## ✅ **Verification Checklist**

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] LANDINGAI_API_KEY set
- [ ] OPENAI_API_KEY set  
- [ ] Data directories created
- [ ] Test examples run successfully
- [ ] Main app starts without errors
- [ ] MCP server accessible on port 8127
- [ ] Real-time processing works with test files

## 🎉 **You're Ready!**

Your CriticalAlert AI system is now set up and ready for **real-time emergency radiology processing**! 

🏥 **Next Steps:**
1. Add real radiology PDFs to `data/incoming/`
2. Connect AI assistants to the MCP server
3. Monitor critical alerts in real-time
4. Scale for hospital deployment

Need help? Check the logs in `logs/` or run examples for debugging! 🚨
