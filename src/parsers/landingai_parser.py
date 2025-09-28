import pathway as pw
from typing import List, Optional, Literal, Dict, Any
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from agentic_doc.parse import parse
from agentic_doc.config import ParseConfig

logger = logging.getLogger(__name__)


class RadiologyExtractionModel(BaseModel):
    """Pydantic model for structured radiology report extraction using LandingAI"""
    
    patient_id: Optional[str] = Field(default=None, description="Patient identification number or ID")
    study_type: Optional[str] = Field(default=None, description="Type of radiological study (e.g., CT, MRI, X-ray, Ultrasound)")
    study_date: Optional[str] = Field(default=None, description="Date when the study was performed")
    report_date: Optional[str] = Field(default=None, description="Date when the report was generated")
    radiologist: Optional[str] = Field(default=None, description="Name of the radiologist who interpreted the study")
    clinical_history: Optional[str] = Field(default=None, description="Patient's clinical history and reason for study")
    technique: Optional[str] = Field(default=None, description="Technical parameters and methodology used")
    findings: Optional[str] = Field(default=None, description="Detailed radiological findings and observations")
    impression: Optional[str] = Field(default=None, description="Radiologist's impression and conclusion")
    critical_findings: Optional[str] = Field(default=None, description="Critical or urgent findings that require immediate attention")
    urgent_conditions: Optional[str] = Field(default=None, description="Urgent medical conditions identified")
    critical_conditions: Optional[str] = Field(default=None, description="Life-threatening or critical conditions")
    anatomical_abnormalities: Optional[str] = Field(default=None, description="Anatomical abnormalities or structural issues")


class LandingAIRadiologyParser(pw.UDF):
    """Parse radiology reports using LandingAI agentic-doc library."""
    
    def __init__(self, api_key: str, capacity: int, results_dir: str, cache_strategy: pw.udfs.CacheStrategy = None, *, async_mode: str = "fully_async", **kwargs):
        self.api_key = api_key
        self.async_mode = async_mode
        self.results_dir = results_dir
        self.capacity = capacity
        from pathway.xpacks.llm._utils import _prepare_executor 

        executor = _prepare_executor(async_mode)
        super().__init__(cache_strategy=cache_strategy, executor=executor)
    
    async def parse(self, contents: bytes) -> List[tuple[str, dict]]:
        """Parse radiology reports using LandingAI."""
        
        # Create results directory
        results_dir = Path(self.results_dir)
        results_dir.mkdir(exist_ok=True)
        # Define extraction schema in JSON Schema format
        extraction_schema = {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient identification number or ID"
                },
                "study_type": {
                    "type": "string", 
                    "description": "Type of radiological study (CT, MRI, X-ray, Ultrasound, etc.)"
                },
                "findings": {
                    "type": "string",
                    "description": "Key radiological findings and observations from the study"
                },
                "impression": {
                    "type": "string",
                    "description": "Radiologist's impression, conclusion, and clinical interpretation"
                },
                "critical_findings": {
                    "type": "string",
                    "description": "Any critical, urgent, or life-threatening findings requiring immediate attention"
                }
            },
            "additionalProperties": False,
            "required": ["study_type", "findings", "impression"]
        }
        
        # Parse document with LandingAI using proper JSON Schema
        parsed_results = parse(
            contents,
            include_marginalia=True,
            include_metadata_in_markdown=True,
            result_save_dir=str(results_dir),
            extraction_schema=extraction_schema,
            config=ParseConfig(api_key=self.api_key)
        )
        
        if not parsed_results:
            return [("", {"source": "landingai", "error": "No parsing results"})]

        parsed_doc = parsed_results[0]
        text_content = getattr(parsed_doc, 'markdown', "")

        # Extract structured data from extraction_metadata if available
        extraction_data = {}
        if hasattr(parsed_doc, 'extraction_metadata') and parsed_doc.extraction_metadata:
            for field, data in parsed_doc.extraction_metadata.items():
                if isinstance(data, dict) and 'value' in data and data['value']:
                    extraction_data[field] = data['value']

        # Create clean metadata with extracted fields
        metadata = {
            "source": "landingai",
            "confidence": str(getattr(parsed_doc, 'confidence', 0.0)),
            **{k: str(v) for k, v in extraction_data.items() if v is not None}
        }
        
        # Ensure string types for Pathway
        safe_text = str(text_content) if text_content else ""
        safe_metadata = {k: str(v) if v is not None else "" for k, v in metadata.items()}
        
        return [(safe_text, safe_metadata)]
    
    async def __wrapped__(self, contents: bytes, **kwargs) -> list[tuple[str, dict]]:
        return await self.parse(contents)