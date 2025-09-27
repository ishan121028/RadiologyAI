"""
CriticalAlert AI - Parsers Module
Radiology report parsers for critical finding detection
"""

# Import components conditionally based on available dependencies
try:
    from .landingai_parser import (
        LandingAIRadiologyParser,
        RadiologyDocumentStore,
        RadiologyExtractionModel
    )
    _PARSERS_AVAILABLE = True
except ImportError as e:
    # Create placeholder classes when dependencies are missing
    LandingAIRadiologyParser = None
    RadiologyDocumentStore = None
    RadiologyExtractionModel = None
    _PARSERS_AVAILABLE = False
    print(f"⚠️ Warning: Parser components not available - {e}")

__all__ = [
    "LandingAIRadiologyParser",
    "RadiologyDocumentStore", 
    "RadiologyExtractionModel"
]

# Version info
__version__ = "1.0.0"
__author__ = "CriticalAlert AI Team"
