import pathway as pw
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, InstanceOf
import logging
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm import embedders, splitters

logger = logging.getLogger(__name__)

# Correct import path for the DocumentStore
from src.store.RadiologyDocumentStore import RadiologyDocumentStore


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

        # Keep a typed handle to the document store when available
        self.indexer: RadiologyDocumentStore | object = indexer


    # Patient tools are now only available directly through MCP from DocumentStore
    # No delegation needed - this avoids double delegation issues

