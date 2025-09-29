"""
Radiology AI - Core Module
Real-time radiology document processing with AI
"""

from .parsers import (
    LandingAIRadiologyParser,
    RadiologyExtractionModel,
)

__all__ = [
    "LandingAIRadiologyParser",
    "RadiologyExtractionModel",
]

__version__ = "1.0.0"
__title__ = "Radiology AI"
__description__ = "Real-time radiology document processing with AI"