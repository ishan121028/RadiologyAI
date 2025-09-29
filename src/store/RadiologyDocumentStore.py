import pathway as pw
from typing import Any, List, Optional, Dict
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.splitters import TokenCountSplitter
from pathway.udfs import CacheStrategy

logger = logging.getLogger(__name__)

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
        splitter: Optional[TokenCountSplitter] = None,
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
            parser: Document parser (will create LandingAI parser if not provided)
            landingai_api_key: API key for LandingAI parsing
            cache_strategy: Caching strategy for parsing operations
        """
        
        self.landingai_api_key = landingai_api_key or os.getenv("LANDINGAI_API_KEY")
        
        
        super().__init__(
            docs=docs,
            retriever_factory=retriever_factory,
            splitter=splitter,
            parser=parser,
            **kwargs
        )
    
    class PatientQuerySchema(pw.Schema):
        """Schema for patient extraction query"""
        patient_name: str = pw.column_definition(dtype=str, default_value="")
    
    class PatientQueryResultSchema(pw.Schema):
        """Result schema for patient extraction query - matches DocumentStore pattern"""
        result: pw.Json
    
    class PatientSearchSchema(pw.Schema):
        """Schema for patient search by ID"""
        patient_id: str = pw.column_definition(dtype=str, default_value="")
        
    class PatientSearchResultSchema(pw.Schema):
        """Result schema for patient search - matches DocumentStore pattern"""
        result: pw.Json
    
    @pw.table_transformer
    def query_patient_extraction(self, request_table: pw.Table[PatientQuerySchema]) -> pw.Table[PatientQueryResultSchema]:
        """
        MCP Tool: Simple extraction query using parsed_docs directly (no complex aggregations).
        """
        all_docs = self.parsed_docs.reduce(
            metadatas=pw.reducers.tuple(pw.this.metadata),
            texts=pw.reducers.tuple(pw.this.text),
            doc_count=pw.reducers.count(),
        )
        
        @pw.udf
        def format_filtered_extraction_result(patient_query: str, metadatas: list, texts: list, doc_count: int) -> pw.Json:
            all_results = []
            filtered_results = []
            
            for i, (metadata, text) in enumerate(zip(metadatas or [], texts or [])):
                if metadata:
                    try:
                        metadata_dict = metadata.as_dict() if hasattr(metadata, 'as_dict') else {}
                        doc_result = {
                            "document_index": i + 1,
                            "patient_id": metadata_dict.get("patient_id", "unknown"),
                            "study_type": metadata_dict.get("study_type", "unknown"),
                            "findings_preview": str(metadata_dict.get("findings", ""))[:150] + "..." if metadata_dict.get("findings") else "No findings",
                            "impression_preview": str(metadata_dict.get("impression", ""))[:150] + "..." if metadata_dict.get("impression") else "No impression",
                            "critical_findings": metadata_dict.get("critical_findings", "none"),
                            "confidence": metadata_dict.get("confidence", "0.0"),
                            "text_length": len(str(text)) if text else 0
                        }
                        all_results.append(doc_result)
                        
                        # Filter by patient query if provided and not generic
                        if patient_query and patient_query.lower() not in ["test patient", "radiology patient", "", "all"]:
                            patient_id = str(metadata_dict.get("patient_id", "")).strip()
                            if patient_id == patient_query or patient_query.lower() in patient_id.lower():
                                filtered_results.append(doc_result)
                        else:
                            filtered_results.append(doc_result)
                            
                    except:
                        # Skip problematic documents
                        continue
            
            results_to_show = filtered_results if (patient_query and patient_query.lower() not in ["test patient", "radiology patient", "", "all"]) else all_results
            
            response = {
                "query": patient_query,
                "total_documents": doc_count,
                "filtered": len(filtered_results) < len(all_results),
                "extraction_results": results_to_show,
                "summary": {
                    "total_documents_processed": len(all_results),
                    "documents_shown": len(results_to_show),
                    "documents_with_patient_ids": len([r for r in results_to_show if r["patient_id"] != "unknown"]),
                    "documents_with_findings": len([r for r in results_to_show if r["findings_preview"] != "No findings"]),
                    "documents_with_critical_findings": len([r for r in results_to_show if r["critical_findings"] not in ["none", "", "no critical findings"]])
                },
                "status": "success",
                "note": "Live extraction data from parsed documents" + (" (filtered)" if len(filtered_results) < len(all_results) else " (all documents)")
            }
            return pw.Json(response)
        
        result = request_table.join_left(all_docs, id=request_table.id).select(
            result=format_filtered_extraction_result(
                request_table.patient_name,
                all_docs.metadatas,
                all_docs.texts,
                all_docs.doc_count
            )
        )
        
        return result
    
    @pw.table_transformer
    def search_patient_by_id(self, request_table: pw.Table[PatientSearchSchema]) -> pw.Table[PatientSearchResultSchema]:
        """
        MCP Tool: Search for specific patient ID in parsed documents.
        """
        logger.info("🔍 search_patient_by_id: Filtering by specific patient ID")
        
        all_docs = self.parsed_docs.reduce(
            metadatas=pw.reducers.tuple(pw.this.metadata),
            texts=pw.reducers.tuple(pw.this.text),
            total_docs=pw.reducers.count(),
        )
        
        @pw.udf
        def search_by_patient_id(requested_patient_id: str, metadatas: list, texts: list, total_docs: int) -> pw.Json:

            matching_docs = []
            for i, (metadata, text) in enumerate(zip(metadatas or [], texts or [])):
                if metadata:
                    try:
                        metadata_dict = metadata.as_dict() if hasattr(metadata, 'as_dict') else {}
                        doc_patient_id = str(metadata_dict.get("patient_id", "")).strip()
                        
                        # Check if this document matches the requested patient ID
                        if doc_patient_id == requested_patient_id or (doc_patient_id and doc_patient_id != "unknown"):
                            matching_docs.append({
                                "document_index": i + 1,
                                "patient_id": doc_patient_id,
                                "study_type": metadata_dict.get("study_type", "unknown"),
                                "findings": str(metadata_dict.get("findings", ""))[:200] + "..." if len(str(metadata_dict.get("findings", ""))) > 200 else str(metadata_dict.get("findings", "")),
                                "impression": str(metadata_dict.get("impression", ""))[:200] + "..." if len(str(metadata_dict.get("impression", ""))) > 200 else str(metadata_dict.get("impression", "")),
                                "critical_findings": metadata_dict.get("critical_findings", "none"),
                                "confidence": metadata_dict.get("confidence", "0.0"),
                                "text_length": len(str(text)) if text else 0,
                                "exact_match": doc_patient_id == requested_patient_id
                            })
                    except:
                        continue
            
            if matching_docs:
                exact_matches = [doc for doc in matching_docs if doc["exact_match"]]
                if exact_matches:
                    response = {
                        "patient_id": requested_patient_id,
                        "found": True,
                        "exact_matches": len(exact_matches),
                        "documents": exact_matches,
                        "total_documents_in_system": total_docs,
                        "status": "success"
                    }
                else:
                    response = {
                        "patient_id": requested_patient_id,
                        "found": False,
                        "similar_patients": matching_docs,
                        "total_documents_in_system": total_docs,
                        "status": "no_exact_match",
                        "message": f"No exact match for patient ID '{requested_patient_id}', but found {len(matching_docs)} other patients"
                    }
            else:
                response = {
                    "patient_id": requested_patient_id,
                    "found": False,
                    "total_documents_in_system": total_docs,
                    "status": "not_found",
                    "message": f"No documents found for patient ID '{requested_patient_id}'"
                }
            
            return pw.Json(response)
        
        result = request_table.join_left(all_docs, id=request_table.id).select(
            result=search_by_patient_id(
                request_table.patient_id,
                all_docs.metadatas,
                all_docs.texts,
                all_docs.total_docs
            )
        )
        
        logger.info("✅ search_patient_by_id: Returning filtered results by patient ID")
        return result
    
    def register_mcp(self, server):
        """
        Register MCP tools including both DocumentStore defaults and custom patient tools.
        
        This overrides the parent DocumentStore.register_mcp to add our custom patient tools
        alongside the standard retrieve_query, statistics_query, and inputs_query tools.
        """
        super().register_mcp(server)
        
        server.tool(
            name="query_patient_extraction",
            request_handler=self.query_patient_extraction,
            schema=self.PatientQuerySchema,
        )
        
        server.tool(
            name="search_patient_by_id", 
            request_handler=self.search_patient_by_id,
            schema=self.PatientSearchSchema,
        )
