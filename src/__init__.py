"""
CriticalAlert AI - Core Module
Real-time emergency radiology alert system
"""

# Core parsers
from .parsers import (
    LandingAIRadiologyParser,
    RadiologyExtractionModel,
)

__all__ = [
    "LandingAIRadiologyParser",
    "RadiologyExtractionModel",
]

# Package metadata
__version__ = "1.0.0"
__title__ = "CriticalAlert AI"
__description__ = "Real-time emergency radiology alert system"
__author__ = "CriticalAlert AI Team"
__license__ = "MIT"

