import pathway as pw
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, InstanceOf
import logging
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from src.store.RadiologyDocumentStore import RadiologyDocumentStore

logger = logging.getLogger(__name__)

class RadiologyQuestionAnswerer(BaseRAGQuestionAnswerer):
    """
    Radiology-focused question answerer built on BaseRAGQuestionAnswerer.

    - Provides a medical prompt tuned for emergency alerting
    - Holds a reference to the underlying DocumentStore (indexer) for patient utilities
    """

    def __init__(self, llm, indexer, **kwargs):
        # Medical prompt (can be overridden via kwargs)
        medical_prompt = kwargs.pop(
            "prompt_template",
            (
        "Based on these radiology findings: {context}\n\n"
        "Patient Query: {query}\n\n"
        "Provide immediate medical recommendations and alert level (RED/ORANGE/YELLOW/GREEN). "
                "Focus on: 1) Immediate actions, 2) Treatment, 3) Escalation, 4) Timeline.\n\n"
        "Response:"
            ),
        )
        search_topk = kwargs.pop("search_topk", 6)

        super().__init__(
            llm=llm,
            indexer=indexer,
            prompt_template=medical_prompt,
            search_topk=search_topk,
            **kwargs,
        )

        self.indexer: RadiologyDocumentStore | object = indexer


    class PatientSearchSchema(pw.Schema):
        patient_id: str = pw.column_definition(dtype=str, default_value="")

    class PatientQuerySchema(pw.Schema):
        patient_name: str = pw.column_definition(dtype=str, default_value="")

    @pw.table_transformer
    def search_patient_by_id(self, request_table: pw.Table[PatientSearchSchema]) -> pw.Table:
        """
        Search for patient by ID - delegates to DocumentStore implementation.
        """
        return self.indexer.search_patient_by_id(request_table)

    @pw.table_transformer
    def query_patient_extraction(self, request_table: pw.Table[PatientQuerySchema]) -> pw.Table:
        """
        Query patient extraction results - delegates to DocumentStore implementation.
        """
        return self.indexer.query_patient_extraction(request_table)

