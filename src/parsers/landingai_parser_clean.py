import pathway as pw
from typing import Any, List, Optional
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathway.xpacks.llm.document_store import DocumentStore

load_dotenv()
logger = logging.getLogger(__name__)

# Import the correct LandingAI agentic_doc library
try:
    from agentic_doc.parse import parse
    from agentic_doc.config import ParseConfig
    AGENTIC_DOC_AVAILABLE = True
except ImportError:
    AGENTIC_DOC_AVAILABLE = False
    parse = None

# Type aliases for Pathway components
try:
    UDFCache = pw.udfs.DefaultCache
    CacheStrategy = pw.udfs.CacheStrategy
    TextSplitter = pw.xpacks.llm.splitters.TokenCountSplitter
except AttributeError:
    logger.warning("Pathway xpacks not available, using fallback types")
    UDFCache = Any
    CacheStrategy = Any
    TextSplitter = Any

# --- Pydantic Models for Medical Extraction ---

class RadiologyExtractionModel(BaseModel):
    """Pydantic model for structured radiology report extraction using LandingAI"""
    
    # Simplified model with fewer fields to avoid complexity issues
    patient_id: Optional[str] = Field(default=None, description="Patient identification number or ID")
    study_type: Optional[str] = Field(default=None, description="Type of radiological study (e.g., CT, MRI, X-ray, Ultrasound)")
    findings: Optional[str] = Field(default=None, description="Detailed radiological findings and observations")
    impression: Optional[str] = Field(default=None, description="Radiologist's impression and conclusion")
    critical_findings: Optional[str] = Field(default=None, description="Critical or urgent findings that require immediate attention")


class LandingAIRadiologyParser(pw.UDF):
    """
    Pathway UDF for parsing radiology reports using LandingAI agentic-doc library.
    
    This parser extracts structured medical data from PDF radiology reports using
    LandingAI's document analysis API with custom Pydantic models.
    
    Args:
        api_key: LandingAI API key for document analysis
        cache_strategy: Caching strategy for UDF results (disabled to avoid Pydantic serialization issues)
        confidence_threshold: Minimum confidence for extractions
        chunk: Whether to chunk parsed document into smaller parts
        async_mode: Processing mode - "batch_async" or "fully_async"
    """
    
    def __init__(
        self,
        api_key: str,
        cache_strategy: Optional[CacheStrategy] = None,
        confidence_threshold: float = 0.7,
        chunk: bool = True,
        *,
        async_mode: str = "batch_async"
    ):
        """
        Initialize LandingAI parser following UDF pattern
        """

        self.api_key = api_key
        self.confidence_threshold = confidence_threshold
        self.chunk = chunk
        # Use None to avoid UDF serialization issues with class references
        self.extraction_model = None

        # Verify LandingAI library is available
        if not AGENTIC_DOC_AVAILABLE:
            logger.warning("LandingAI agentic-doc library not available. Install with: pip install agentic-doc")
        
        # Follow DoclingParser pattern exactly
        from pathway.xpacks.llm.parsers import _prepare_executor
        
        executor = _prepare_executor(async_mode=async_mode)
        super().__init__(cache_strategy=cache_strategy, executor=executor)
    
    def _parse_with_landingai_sync(self, contents: bytes) -> List[tuple[str, dict]]:
        """
        Synchronous wrapper for LandingAI parsing to avoid UDF async context issues
        """
        chunks: List[tuple[str, dict]] = []
        
        try:
            if not AGENTIC_DOC_AVAILABLE:
                raise ValueError("LandingAI agentic-doc library not available. Install with: pip install agentic-doc")
            
            if not self.api_key:
                raise ValueError("Valid LandingAI API key required. Set LANDINGAI_API_KEY environment variable.")
            
            # Create results directory if it doesn't exist
            results_dir = Path("data/extraction_results")
            results_dir.mkdir(exist_ok=True)
            
            # Use structured extraction with RadiologyExtractionModel
            # Define model locally to avoid UDF serialization issues
            logger.info("🔄 Using LandingAI parsing with structured medical extraction (sync mode)")
            
            # Define extraction model locally within the method to avoid Pathway UDF context issues
            class LocalRadiologyExtractionModel(BaseModel):
                patient_id: Optional[str] = Field(default=None, description="Patient identification number or ID")
                study_type: Optional[str] = Field(default=None, description="Type of radiological study (e.g., CT, MRI, X-ray, Ultrasound)")
                findings: Optional[str] = Field(default=None, description="Detailed radiological findings and observations")
                impression: Optional[str] = Field(default=None, description="Radiologist's impression and conclusion")
                critical_findings: Optional[str] = Field(default=None, description="Critical or urgent findings that require immediate attention")
            
            parsed_results = parse(
                contents,
                extraction_model=LocalRadiologyExtractionModel,
                include_marginalia=True,
                include_metadata_in_markdown=True,
                result_save_dir=str(results_dir),
                config=ParseConfig(api_key=self.api_key)
            )
            
            if parsed_results and len(parsed_results) > 0:
                parsed_doc = parsed_results[0]
                
                # Extract the text content
                text_content = parsed_doc.markdown if hasattr(parsed_doc, 'markdown') else ""
                
                # Extract structured data (if available)
                structured_data = {}
                extraction_success = False
                extraction_error = ""
                
                if hasattr(parsed_doc, 'extraction') and parsed_doc.extraction:
                    extraction_success = True
                    if hasattr(parsed_doc.extraction, 'model_dump'):
                        structured_data = parsed_doc.extraction.model_dump()
                    elif isinstance(parsed_doc.extraction, dict):
                        structured_data = parsed_doc.extraction
                    else:
                        # Handle Pydantic model instance
                        structured_data = {
                            "patient_id": getattr(parsed_doc.extraction, 'patient_id', ''),
                            "study_type": getattr(parsed_doc.extraction, 'study_type', ''),
                            "study_date": getattr(parsed_doc.extraction, 'study_date', ''),
                            "clinical_history": getattr(parsed_doc.extraction, 'clinical_history', ''),
                            "technique": getattr(parsed_doc.extraction, 'technique', ''),
                            "findings": getattr(parsed_doc.extraction, 'findings', ''),
                            "impression": getattr(parsed_doc.extraction, 'impression', ''),
                            "radiologist": getattr(parsed_doc.extraction, 'radiologist', ''),
                            "critical_findings": getattr(parsed_doc.extraction, 'critical_findings', ''),
                            "urgent_conditions": getattr(parsed_doc.extraction, 'urgent_conditions', ''),
                            "critical_conditions": getattr(parsed_doc.extraction, 'critical_conditions', ''),
                            "anatomical_abnormalities": getattr(parsed_doc.extraction, 'anatomical_abnormalities', ''),
                            "report_date": getattr(parsed_doc.extraction, 'report_date', ''),
                        }
                elif hasattr(parsed_doc, 'extraction_error') and parsed_doc.extraction_error:
                    extraction_error = parsed_doc.extraction_error
                    logger.warning(f"LandingAI structured parsing failed: {extraction_error}")
                
                # Combine metadata from parsed_doc and structured_data
                metadata = {
                    "source": "landingai",
                    "confidence": parsed_doc.confidence if hasattr(parsed_doc, 'confidence') else 0.0,
                    "extraction_success": extraction_success,
                    "extraction_error": extraction_error,
                    **structured_data, # Add structured data to metadata
                }
                
                # Ensure safe types for Pathway
                safe_text = str(text_content) if text_content else ""
                safe_metadata = {k: str(v) if v is not None else "" for k, v in metadata.items()}
                
                chunks.append((safe_text, safe_metadata))
                
                # Save extraction summary to JSON file
                if extraction_success and structured_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    summary_file = results_dir / f"extraction_summary_{timestamp}.json"
                    with open(summary_file, "w") as f:
                        json.dump(structured_data, f, indent=2)
                    logger.info(f"📁 Structured extraction summary saved to: {summary_file}")
            else:
                raise ValueError("LandingAI parsing returned no results.")
                
        except Exception as e:
            logger.error(f"Error during LandingAI parsing: {e}")
            # Fallback to raw markdown parsing if structured extraction fails
            logger.info("Attempting fallback to raw markdown parsing...")
            try:
                fallback_results_dir = results_dir / "fallback"
                fallback_results_dir.mkdir(exist_ok=True)
                parsed_results = parse(
                    contents,
                    include_marginalia=True,
                    include_metadata_in_markdown=True,
                    result_save_dir=str(fallback_results_dir),
                    config=ParseConfig(api_key=self.api_key)
                )
                if parsed_results and len(parsed_results) > 0:
                    parsed_doc = parsed_results[0]
                    text_content = parsed_doc.markdown if hasattr(parsed_doc, 'markdown') else ""
                    
                    metadata = {
                        "source": "landingai_fallback",
                        "confidence": parsed_doc.confidence if hasattr(parsed_doc, 'confidence') else 0.0,
                        "extraction_success": False,
                        "fallback_reason": str(e),
                        "content_length": len(text_content),
                        "patient_id": "", # Placeholder for fallback
                        "study_type": "", # Placeholder for fallback
                        "study_date": "", # Placeholder for fallback
                        "findings": text_content[:500] if text_content else "",  # First 500 chars as findings
                        "impression": "",
                        "critical_findings": "",
                        "extraction_error": str(e)
                    }
                    
                    # Ensure safe types for Pathway
                    safe_text = str(text_content) if text_content else ""
                    safe_metadata = {k: str(v) for k, v in metadata.items()}
                    
                    chunks.append((safe_text, safe_metadata))
                    logger.info(f"✅ Fallback parsing successful - {len(text_content)} characters")
                    logger.info(f"📁 Fallback results saved to: {fallback_results_dir}")
                else:
                    raise ValueError("Fallback parsing also failed")
                    
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
                # Return error chunk as last resort
                chunks.append(("", {
                    "parsing_method": "error",
                    "confidence": 0.0,
                    "extraction_success": False,
                    "error": str(e),
                    "fallback_error": str(fallback_error)
                }))
        
        return chunks

    async def parse(self, contents: bytes) -> List[tuple[str, dict]]:
        """
        Parse radiology reports using LandingAI agentic-doc library.
        
        Args:
            contents: PDF content as bytes
            
        Returns:
            List of tuples containing (text, metadata) for each chunk
        """
        # Call the synchronous wrapper to avoid UDF async context issues
        return self._parse_with_landingai_sync(contents)

    async def __wrapped__(self, contents: bytes, **kwargs) -> list[tuple[str, dict]]:
        return await self.parse(contents)


# Usage examples and integration patterns
class RadiologyDocumentStore(DocumentStore):
    """
    Document store for radiology reports with LandingAI parsing
    
    Inherits from Pathway's DocumentStore to get real-time indexing and vector search.
    Adds medical-specific parsing and critical alert detection.
    """
    
    def __init__(
        self,
        docs: pw.Table,
        retriever_factory,
        splitter: Optional[TextSplitter] = None,
        parser=None,
        landingai_api_key: Optional[str] = None,
        cache_strategy: Optional[CacheStrategy] = None,
        **kwargs
    ):
        """
        Initialize radiology document store
        
        Args:
            docs: Pathway table with document data
            retriever_factory: Factory for creating document retrievers
            splitter: Text splitter for chunking documents
            parser: Document parser (will use LandingAI if not provided)
            landingai_api_key: API key for LandingAI parsing
            cache_strategy: Caching strategy for UDFs
        """
        
        self.landingai_api_key = landingai_api_key or os.getenv("LANDINGAI_API_KEY")
        
        # Use LandingAI parser if no parser provided
        if parser is None:
            if not self.landingai_api_key:
                raise ValueError(
                    "LandingAI API key is missing. Export LANDINGAI_API_KEY before running."
                )
            parser = LandingAIRadiologyParser(
                api_key=self.landingai_api_key,
                cache_strategy=cache_strategy,
                async_mode="batch_async",
                capacity=2
            )
        
        # Initialize parent DocumentStore
        super().__init__(
            docs=docs,
            retriever_factory=retriever_factory,
            splitter=splitter,
            parser=parser,
            **kwargs
        )
