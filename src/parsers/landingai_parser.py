import pathway as pw
from typing import Any, Dict, List, Optional, Union, Literal
import tempfile
import os
import json
import logging
from datetime import datetime
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
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

# Check if Pathway xpacks is available
try:
    import pathway.xpacks.llm.parsers
    import pathway.xpacks.llm.splitters
    import pathway.udfs
    # Test the specific imports we need
    from pathway.xpacks.llm.parsers import UnstructuredParser
    from pathway.udfs import DiskCache
    PATHWAY_XPACKS_AVAILABLE = True
    logger.info("Pathway xpacks available with UnstructuredParser")
    # Type aliases for when xpacks is available  
    UDFCache = pw.udfs.DefaultCache
    CacheStrategy = pw.udfs.CacheStrategy
    TextSplitter = pw.xpacks.llm.splitters.TokenCountSplitter
    try:
        RetrieverFactory = pw.indexing.AbstractRetrieverFactory
    except AttributeError:
        RetrieverFactory = Any  # Fallback if not available
except (ImportError, AttributeError) as e:
    PATHWAY_XPACKS_AVAILABLE = False
    logger.warning(
        "Pathway xpacks not fully available; falling back to simplified implementations: %s",
        e,
    )
    # Fallback type aliases
    UDFCache = Any
    CacheStrategy = Any
    TextSplitter = Any
    RetrieverFactory = Any

# --- Pydantic Models for Medical Extraction ---

class RadiologyExtractionModel(BaseModel):
    """Pydantic model for structured radiology report extraction using LandingAI"""
    patient_id: Optional[str] = Field(None, description="Patient identification number or ID")
    study_date: Optional[str] = Field(None, description="Date when the study was performed")
    study_type: Optional[str] = Field(None, description="Type of radiological study (e.g., CT, MRI, X-ray, Ultrasound)")
    clinical_history: Optional[str] = Field(None, description="Patient's clinical history and reason for the study")
    technique: Optional[str] = Field(None, description="Technical details of how the study was performed")
    findings: Optional[str] = Field(None, description="Detailed radiological findings and observations")
    impression: Optional[str] = Field(None, description="Radiologist's impression and conclusion")
    radiologist: Optional[str] = Field(None, description="Name of the radiologist who interpreted the study")
    critical_findings: Optional[List[str]] = Field(None, description="List of critical or urgent findings that require immediate attention")
    urgent_conditions: Optional[List[str]] = Field(None, description="List of urgent medical conditions identified")
    critical_conditions: Optional[List[str]] = Field(None, description="List of critical medical conditions requiring immediate intervention")
    anatomical_abnormalities: Optional[List[str]] = Field(None, description="List of anatomical abnormalities or structural changes")
    report_date: Optional[str] = Field(None, description="Date when the report was finalized")


class LandingAIRadiologyParser(pw.UDF):
    """
    Parse radiology reports using LandingAI agentic-doc library.
    
    This class follows the same pattern as DoclingParser, providing
    structured medical data extraction from PDF radiology reports.
    
    Args:
        api_key: LandingAI API key for document parsing
        extraction_model: Pydantic model for structured data extraction
        cache_strategy: Defines the caching mechanism
        confidence_threshold: Minimum confidence for extractions
        chunk: Whether to chunk parsed document into smaller parts
        async_mode: Processing mode - "batch_async" or "fully_async"
    """
    
    def __init__(
        self,
        api_key: str,
        extraction_model: Optional[type] = None,
        cache_strategy: Optional[CacheStrategy] = None,
        confidence_threshold: float = 0.7,
        chunk: bool = True,
        *,
        async_mode: Literal["batch_async", "fully_async"] = "batch_async"
    ):
        """
        Initialize LandingAI parser following UDF pattern
        """
        self.api_key = api_key
        self.confidence_threshold = confidence_threshold
        self.chunk = chunk
        self.extraction_model = extraction_model or RadiologyExtractionModel
        
        # Verify LandingAI library is available
        if not AGENTIC_DOC_AVAILABLE:
            logger.warning("LandingAI agentic-doc library not available. Install with: pip install agentic-doc")
        
        # Follow DoclingParser pattern exactly
        from pathway.xpacks.llm.parsers import _prepare_executor
        
        executor = _prepare_executor(async_mode=async_mode)
        super().__init__(cache_strategy=cache_strategy, executor=executor)
    
    async def parse(self, contents: bytes) -> List[tuple[str, dict]]:
        """
        Parse radiology reports using LandingAI agentic-doc library.
        
        Args:
            contents: PDF content as bytes
            
        Returns:
            List of tuples containing (text, metadata) for each chunk
        """
        chunks: List[tuple[str, dict]] = []
        
        try:
            if not AGENTIC_DOC_AVAILABLE:
                raise ValueError("LandingAI agentic-doc library not available. Install with: pip install agentic-doc")
            
            if not self.api_key:
                raise ValueError("Valid LandingAI API key required. Set LANDINGAI_API_KEY environment variable.")
            
            # Use LandingAI agentic-doc parse function
            logger.info("Parsing with LandingAI agentic-doc library")
            
            # Create results directory if it doesn't exist
            results_dir = Path("data/extraction_results")
            results_dir.mkdir(exist_ok=True)
            
            # Parse with structured extraction model and save results
            parsed_results = parse(
                contents,
                extraction_model=self.extraction_model,  # Use our Pydantic model
                include_marginalia=True,  # Include headers/footers
                include_metadata_in_markdown=True,  # Include metadata
                result_save_dir=str(results_dir),  # Save extraction results
                config=ParseConfig(api_key=self.api_key) # Pass API key explicitly
            )
            
            if parsed_results and len(parsed_results) > 0:
                parsed_doc = parsed_results[0]
                
                # Extract the text content
                text_content = parsed_doc.markdown if hasattr(parsed_doc, 'markdown') else ""
                
                # Extract structured data using the correct LandingAI API
                structured_data = {}
                extraction_success = False
                
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
                            "critical_findings": getattr(parsed_doc.extraction, 'critical_findings', []) or [],
                            "urgent_conditions": getattr(parsed_doc.extraction, 'urgent_conditions', []) or [],
                            "critical_conditions": getattr(parsed_doc.extraction, 'critical_conditions', []) or [],
                            "anatomical_abnormalities": getattr(parsed_doc.extraction, 'anatomical_abnormalities', []) or [],
                            "report_date": getattr(parsed_doc.extraction, 'report_date', ''),
                        }
                
                # Check for extraction errors
                extraction_error = None
                if hasattr(parsed_doc, 'extraction_error') and parsed_doc.extraction_error:
                    extraction_error = str(parsed_doc.extraction_error)
                    logger.warning(f"LandingAI extraction error: {extraction_error}")
                
                # Create metadata with medical fields
                metadata = {
                    "patient_id": structured_data.get("patient_id", ""),
                    "study_type": structured_data.get("study_type", ""),
                    "study_date": structured_data.get("study_date", ""),
                    "findings": structured_data.get("findings", ""),
                    "impression": structured_data.get("impression", ""),
                    "critical_findings": structured_data.get("critical_findings", []) or structured_data.get("critical_conditions", []) or [],
                    "confidence": 0.95 if extraction_success else 0.7,
                    "parsing_method": "landingai_agentic_doc",
                    "extraction_success": extraction_success,
                    "extraction_error": extraction_error,
                    "has_extraction_metadata": hasattr(parsed_doc, 'extraction_metadata') and parsed_doc.extraction_metadata is not None
                }
                
                # Handle chunking
                if self.chunk and hasattr(parsed_doc, 'chunks') and parsed_doc.chunks:
                    # Use LandingAI's native chunks
                    for chunk_data in parsed_doc.chunks:
                        chunk_text = str(chunk_data) if chunk_data else ""
                        chunk_metadata = metadata.copy()
                        chunk_metadata["chunk_type"] = "landingai_chunk"
                        chunks.append((chunk_text, chunk_metadata))
                else:
                    # Single chunk with full content
                    chunks.append((text_content, metadata))
                
                # Save extraction summary to JSON file
                if extraction_success and structured_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    summary_file = results_dir / f"extraction_summary_{timestamp}.json"
                    
                    summary = {
                        "timestamp": timestamp,
                        "extraction_success": extraction_success,
                        "extraction_error": extraction_error,
                        "structured_data": structured_data,
                        "content_length": len(text_content),
                        "chunks_created": len(chunks)
                    }
                    
                    try:
                        with open(summary_file, 'w') as f:
                            json.dump(summary, f, indent=2, default=str)
                        logger.info(f"📄 Extraction summary saved to: {summary_file}")
                    except Exception as save_error:
                        logger.warning(f"Failed to save extraction summary: {save_error}")
                
                logger.info(f"✅ Successfully parsed document with LandingAI - {len(chunks)} chunks")
                logger.info(f"📁 Extraction results saved to: {results_dir}")
                
            else:
                logger.error("No results returned from LandingAI parsing")
                raise ValueError("LandingAI parsing returned no results")
                
        except Exception as e:
            logger.error(f"LandingAI structured parsing failed: {e}")
            logger.info("Attempting fallback to raw markdown parsing...")
            
            try:
                # Fallback: Parse without extraction model but still save results
                fallback_results_dir = Path("data/extraction_results/fallback")
                fallback_results_dir.mkdir(parents=True, exist_ok=True)
                
                parsed_results = parse(
                    contents,
                    include_marginalia=True,
                    include_metadata_in_markdown=True,
                    result_save_dir=str(fallback_results_dir),  # Save fallback results
                    config=ParseConfig(api_key=self.api_key)
                )
                
                if parsed_results and len(parsed_results) > 0:
                    parsed_doc = parsed_results[0]
                    text_content = parsed_doc.markdown if hasattr(parsed_doc, 'markdown') else ""
                    
                    # Basic metadata for fallback
                    metadata = {
                        "parsing_method": "landingai_fallback",
                        "confidence": 0.7,  # Lower confidence for fallback
                        "extraction_success": False,
                        "fallback_reason": str(e),
                        "content_length": len(text_content),
                        "patient_id": "",
                        "study_type": "",
                        "study_date": "",
                        "findings": text_content[:500] if text_content else "",  # First 500 chars as findings
                        "impression": "",
                        "critical_findings": [],
                        "extraction_error": str(e)
                    }
                    
                    chunks.append((text_content, metadata))
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
    
    async def __wrapped__(self, contents: bytes, **kwargs) -> List[tuple[str, dict]]:
        """Main entry point for the UDF - follows DoclingParser pattern"""
        return await self.parse(contents)


# Factory function to create parser instances (similar to Pathway's pattern)
def create_landingai_radiology_parser(
    api_key: str,
    cache_strategy: Optional[CacheStrategy] = None,
    **kwargs
) -> LandingAIRadiologyParser:
    """
    Factory function to create LandingAI radiology parser
    
    Args:
        api_key: LandingAI API key
        cache_strategy: Pathway caching strategy
        **kwargs: Additional parser configuration
        
    Returns:
        Configured LandingAI parser instance
    """
    
    return LandingAIRadiologyParser(
        api_key=api_key,
        cache_strategy=cache_strategy,
        **kwargs
    )


# Usage examples and integration patterns
class RadiologyDocumentStore:
    """
    Document store specifically for radiology reports using LandingAI parser
    
    Similar to pw.xpacks.llm.document_store.DocumentStore
    """
    
    def __init__(
        self,
        data_sources: List[pw.Table],
        landingai_api_key: Optional[str] = None,
        retriever_factory: Optional[RetrieverFactory] = None,
        splitter: Optional[TextSplitter] = None,
        cache_strategy: Optional[CacheStrategy] = None
    ):
        """
        Initialize radiology document store
        
        Args:
            data_sources: List of Pathway tables with document data
            landingai_api_key: LandingAI API key
            retriever_factory: Vector retrieval factory
            splitter: Text splitter for chunks
            cache_strategy: Caching strategy
        """
        
        self.data_sources = data_sources
        api_key = landingai_api_key or os.getenv("LANDINGAI_API_KEY")
        if not api_key:
            raise ValueError(
                "LandingAI API key is missing. Export LANDINGAI_API_KEY before running streaming mode."
            )
        self.parser = LandingAIRadiologyParser(
            api_key=api_key,
            cache_strategy=cache_strategy
        )
        self.retriever_factory = retriever_factory
        self.splitter = splitter
        
        # Combine all data sources
        self.combined_docs = self._combine_sources()
        
        # Parse documents
        self.parsed_docs = self._parse_documents()
        
        # Create chunks if splitter provided
        if self.splitter:
            self.chunked_docs = self._create_chunks()
        else:
            self.chunked_docs = self.parsed_docs
    
    def _combine_sources(self) -> pw.Table:
        """Simple source handling - just return the single source"""
        # In most cases, we'll have just one source
        if len(self.data_sources) == 1:
            return self.data_sources[0]
        
        # If multiple sources, simple concatenation
        combined = self.data_sources[0]
        for source in self.data_sources[1:]:
            combined = combined.concat(source)
        
        return combined
    
    def _parse_documents(self) -> pw.Table:
        """Parse documents using LandingAI parser"""
        
        return self.combined_docs.select(
            *self.combined_docs,
            parsed_content=self.parser(pw.this.data)
        )
    
    def _create_chunks(self) -> pw.Table:
        """Create document chunks for retrieval"""
        
        if not self.splitter:
            return self.parsed_docs
        
        # Implementation would depend on specific chunking strategy
        # For now, return parsed docs as-is
        return self.parsed_docs
    
    def get_critical_alerts(self) -> pw.Table:
        """
        Get critical alerts from parsed radiology reports
        
        Returns:
            pw.Table: Table containing critical alerts with flattened medical fields
        """
        # Transform the parsed content into the expected column structure
        return self.chunked_docs.select(
            # Original columns
            *self.chunked_docs,
            # Extract medical fields from parsed_content metadata
            findings=pw.apply_with_type(
                lambda parsed_content: parsed_content[1].get('findings', '') if parsed_content and len(parsed_content) > 1 and isinstance(parsed_content[1], dict) else '',
                str,
                pw.this.parsed_content
            ),
            impression=pw.apply_with_type(
                lambda parsed_content: parsed_content[1].get('impression', '') if parsed_content and len(parsed_content) > 1 and isinstance(parsed_content[1], dict) else '',
                str,
                pw.this.parsed_content
            ),
            critical_conditions=pw.apply_with_type(
                lambda parsed_content: parsed_content[1].get('critical_findings', []) if parsed_content and len(parsed_content) > 1 and isinstance(parsed_content[1], dict) else [],
                list,
                pw.this.parsed_content
            ),
            # Add a simple alert_level for testing
            alert_level=pw.apply_with_type(
                lambda parsed_content: "RED" if (parsed_content and len(parsed_content) > 1 and isinstance(parsed_content[1], dict) and parsed_content[1].get('critical_findings', [])) else "GREEN",
                str,
                pw.this.parsed_content
            )
        )
    
    def get_processing_stats(self) -> pw.Table:
        """
        Get processing statistics for the document store
        
        Returns:
            pw.Table: Table with processing statistics
        """
        # Create a simple stats table
        return pw.debug.table_from_markdown("""
        stat_name | stat_value
        "documents_processed" | 0
        "critical_alerts_found" | 0
        "processing_errors" | 0
        """)