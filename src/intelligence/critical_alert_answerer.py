import pathway as pw
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, InstanceOf
import logging
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm import embedders, splitters

logger = logging.getLogger(__name__)

# Import RadiologyDocumentStore directly to avoid forward reference issues  
from src.parsers.landingai_parser import RadiologyDocumentStore


class CriticalAlertQuestionAnswerer(BaseRAGQuestionAnswerer):
    """
    Question answerer for critical radiology alerts using Pathway's built-in RAG
    
    Extends BaseRAGQuestionAnswerer with medical-specific functionality
    """
    
    def __init__(self, llm, indexer, document_store=None, **kwargs):
        """
        Initialize CriticalAlert RAG with medical-specific settings
        
        Args:
            llm: LLM instance for question answering
            indexer: VectorStoreServer or DocumentStore for retrieval
            document_store: RadiologyDocumentStore (optional, for compatibility)
            **kwargs: Additional arguments for BaseRAGQuestionAnswerer
        """
        
        # Medical-specific prompt template
        medical_prompt = kwargs.get('prompt_template', 
            "Based on these radiology findings: {context}\n\n"
            "Patient Query: {query}\n\n"
            "Provide immediate medical recommendations and alert level (RED/ORANGE/YELLOW/GREEN). "
            "Focus on:\n"
            "1. Immediate actions required\n"
            "2. Treatment recommendations\n"
            "3. Escalation requirements\n"
            "4. Timeline for intervention\n\n"
            "Response:"
        )
        
        # Extract custom parameters from kwargs to avoid conflicts
        search_topk = kwargs.pop('search_topk', 6)
        red_alert_threshold = kwargs.pop('red_alert_threshold', 0.9)
        orange_alert_threshold = kwargs.pop('orange_alert_threshold', 0.7)
        yellow_alert_threshold = kwargs.pop('yellow_alert_threshold', 0.4)
        
        # Initialize parent BaseRAGQuestionAnswerer
        super().__init__(
            llm=llm,
            indexer=indexer,
            prompt_template=medical_prompt,
            search_topk=search_topk,
            **kwargs
        )
        
        # Store document store for compatibility - use indexer if document_store not provided
        self.document_store = document_store if document_store is not None else indexer
        
        # Alert thresholds
        self.red_alert_threshold = red_alert_threshold
        self.orange_alert_threshold = orange_alert_threshold
        self.yellow_alert_threshold = yellow_alert_threshold
    
    # Using BaseRAGQuestionAnswerer's built-in answer_query method
    
    def get_critical_alerts_stream(self) -> pw.Table:
        """
        Get real-time stream of critical alerts
        
        Returns:
            Stream of critical alerts with medical recommendations
            This is the main method called by app.py to get the Pathway table
        """
        
        # Get critical alerts from the document store (instantiated from YAML)
        critical_alerts = self.document_store.get_critical_alerts()
        
        # Add medical intelligence to alerts using UDFs
        enhanced_alerts = critical_alerts.select(
            *critical_alerts,
            # Generate medical summary
            medical_summary=pw.apply_with_type(
                lambda findings, impression: f"Findings: {findings[:100]}... | Impression: {impression[:100]}...",
                str,
                pw.this.findings,
                pw.this.impression
            ),
            # Calculate risk score
            risk_score=pw.apply_with_type(
                lambda findings, impression: 0.5,  # Simplified risk calculation
                float,
                pw.this.findings,
                pw.this.impression
            ),
            # Generate recommendations
            recommendations=pw.apply_with_type(
                lambda alert_level: ["Standard monitoring protocol"] if alert_level == "GREEN" else ["Immediate medical attention required"],
                list,
                pw.this.alert_level
            )
        )
        
        return enhanced_alerts
    
    def get_processing_statistics(self) -> pw.Table:
        """
        Get processing statistics for the critical alert system
        
        Returns:
            Statistics table with medical intelligence metrics
        """
        
        return self.document_store.get_processing_stats()
    
    # Using BaseRAGQuestionAnswerer's built-in methods instead of custom implementations
    # All UDF methods removed - using BaseRAGQuestionAnswerer's built-in functionality