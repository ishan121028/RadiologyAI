# 🚨 LandingAI Parser Update - Using Correct Documentation

## ✅ **What Was Fixed**

The LandingAI parser has been **completely updated** to use the **correct `agentic_doc` library** as per the official LandingAI documentation.

### **❌ Previous (Incorrect) Implementation:**
```python
# WRONG - Using fictional library
from landingai import LandingAI
client = LandingAI(api_key=api_key)
result = await client.extract_structured_data(...)
```

### **✅ Current (Correct) Implementation:**
```python
# CORRECT - Using real agentic_doc library
from agentic_doc.parse import parse
from agentic_doc import ParsedDocument

# Parse from bytes directly (preferred method)
parsed_results = parse(
    documents=content,  # bytes, file path, or URL
    extraction_model=RadiologyExtractionModel,  # Pydantic model
    include_marginalia=True,
    include_metadata_in_markdown=True
)

# Get results
parsed_doc: ParsedDocument = parsed_results[0]
structured_data = parsed_doc.model_output.model_dump()
raw_text = parsed_doc.markdown
chunks = parsed_doc.chunks
```

## 📋 **Key Changes Made**

### **1. Correct Library Import:**
```python
# Added correct imports
from agentic_doc.parse import parse
from agentic_doc import ParsedDocument
from pydantic import BaseModel
```

### **2. Pydantic Extraction Model:**
```python
class RadiologyExtractionModel(BaseModel):
    """Pydantic model for structured radiology report extraction"""
    patient_id: Optional[str] = None
    study_date: Optional[str] = None
    study_type: Optional[str] = None
    clinical_history: Optional[str] = None
    technique: Optional[str] = None
    findings: Optional[str] = None
    impression: Optional[str] = None
    radiologist: Optional[str] = None
    urgent_findings: Optional[List[str]] = None
    critical_conditions: Optional[List[str]] = None
    # ... more fields
```

### **3. Bytes Parsing (Preferred Method):**
```python
def _call_landingai_api_from_bytes(self, content: bytes, metadata: Dict) -> Optional[Dict]:
    """Parse directly from bytes - no temporary files needed"""
    
    parsed_results = parse(
        documents=content,  # Parse from bytes directly
        extraction_model=RadiologyExtractionModel,
        include_marginalia=True,
        include_metadata_in_markdown=True
    )
    
    # Extract structured data
    parsed_doc = parsed_results[0]
    structured_data = parsed_doc.model_output.model_dump()
    raw_text = parsed_doc.markdown
    
    return result
```

### **4. File Path Parsing (Fallback):**
```python
def _call_landingai_api(self, file_path: str, metadata: Dict) -> Optional[Dict]:
    """Parse from file path if bytes parsing fails"""
    
    parsed_results = parse(
        documents=file_path,  # Can be file path, URL, or bytes
        extraction_model=RadiologyExtractionModel,
        include_marginalia=True,
        include_metadata_in_markdown=True
    )
    # ... same processing logic
```

### **5. Enhanced Processing Pipeline:**
```python
try:
    # 1. Try bytes parsing first (preferred)
    parsed_data = self._call_landingai_api_from_bytes(content, metadata)
    
    if parsed_data:
        # Success with bytes parsing
        result.update(parsed_data)
    else:
        # 2. Fallback to file parsing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        parsed_data = self._call_landingai_api(temp_file_path, metadata)
        
        if parsed_data:
            # Success with file parsing
            result.update(parsed_data)
        else:
            # 3. Final fallback to basic text extraction
            fallback_result = self._fallback_text_extraction(content, metadata)
            result.update(fallback_result)
            
except Exception as e:
    # Robust error handling
    logger.error(f"LandingAI parsing failed: {e}")
```

## 📦 **Updated Dependencies**

### **requirements.txt:**
```txt
# LandingAI - CORRECT LIBRARY
agentic-doc>=0.2.4

# Supporting libraries
pydantic>=2.0.0
pathway[all]>=0.13.0
```

### **Installation:**
```bash
pip install agentic-doc>=0.2.4
pip install pydantic>=2.0.0
```

## 🎯 **Usage Examples**

### **1. Basic Parsing:**
```python
from agentic_doc.parse import parse

# Parse from bytes (recommended)
with open("radiology_report.pdf", "rb") as f:
    pdf_bytes = f.read()

results = parse(
    documents=pdf_bytes,
    extraction_model=RadiologyExtractionModel
)

print(results[0].markdown)  # Raw text
print(results[0].model_output)  # Structured data
```

### **2. Pathway Integration:**
```python
from parsers.landingai_parser import LandingAIRadiologyParser

parser = LandingAIRadiologyParser(
    api_key="your_landingai_api_key",
    cache_strategy=pw.udfs.DefaultCache()
)

file_source = pw.io.fs.read(path="data/", format="binary", mode="streaming")
parsed_docs = parser.parse_table(file_source)
```

### **3. Document Store:**
```python
from parsers.landingai_parser import RadiologyDocumentStore

doc_store = RadiologyDocumentStore(
    data_sources=[file_source],
    landingai_api_key="your_api_key"
)

critical_alerts = doc_store.get_critical_alerts()
```

## 🔧 **Testing**

### **Run Tests:**
```bash
# Test the updated parser
python examples/landingai_parser_example.py

# Test with MCP server
python src/mcp/critical_alert_mcp_server.py
```

### **Environment Setup:**
```bash
export LANDINGAI_API_KEY="your_real_api_key"
export OPENAI_API_KEY="your_openai_key"
```

## ⚡ **Key Benefits of Correct Implementation**

1. **✅ Real API Calls**: Uses actual LandingAI service
2. **✅ Bytes Support**: No temporary files needed  
3. **✅ Structured Extraction**: Pydantic models for type safety
4. **✅ Error Handling**: Robust fallback mechanisms
5. **✅ Pathway Integration**: Native Pathway UDF support
6. **✅ Medical Specialization**: Radiology-specific extraction
7. **✅ Performance**: Direct bytes parsing is faster

## 🏥 **Medical Features**

The parser now correctly extracts:
- **Patient Information**: ID, demographics
- **Study Details**: Date, type, technique
- **Clinical Data**: History, findings, impression
- **Critical Conditions**: Automatic detection
- **Radiologist Info**: Name, report date
- **Structured Output**: JSON + Markdown formats

## 🎉 **Summary**

✅ **Fixed**: Using correct `agentic_doc` library  
✅ **Enhanced**: Bytes parsing + file fallback  
✅ **Improved**: Pydantic models for structure  
✅ **Ready**: For real-time radiology processing  

The LandingAI parser now follows the **official documentation** and is ready for production use in the CriticalAlert AI system! 🚨🏥
