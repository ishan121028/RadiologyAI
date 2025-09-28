"""
CriticalAlert AI - Core Module
Real-time emergency radiology alert system
"""

# Core parsers
from .parsers import (
    LandingAIRadiologyParser,
    RadiologyDocumentStore,
    RadiologyExtractionModel
)

# Intelligence components  
try:
    from .intelligence import CriticalAlertQuestionAnswerer
except ImportError:
    # Handle case where pathway xpacks is not available
    CriticalAlertQuestionAnswerer = None

# Data sources
try:
    from .data_sources import (
        PathwayFileConnector,
        PathwayDocumentProcessor
    )
except ImportError:
    # Handle case where pathway is not fully available
    PathwayFileConnector = None
    PathwayDocumentProcessor = None

# MCP Server components
try:
    from .mcp import (
        CriticalAlertAnalyzerTool,
        CriticalAlertMonitorTool, 
        MedicalRecommendationTool
    )
except ImportError:
    # Handle case where MCP dependencies are not available
    CriticalAlertAnalyzerTool = None
    CriticalAlertMonitorTool = None
    MedicalRecommendationTool = None

__all__ = [
    # Core parsers
    "LandingAIRadiologyParser",
    "RadiologyDocumentStore",
    "RadiologyExtractionModel",
    
    # Intelligence
    "CriticalAlertQuestionAnswerer",
    
    # Data sources  
    "PathwayFileConnector",
    "PathwayDocumentProcessor",
    
    # MCP tools
    "CriticalAlertAnalyzerTool",
    "CriticalAlertMonitorTool",
    "MedicalRecommendationTool"
]

# Package metadata
__version__ = "1.0.0"
__title__ = "CriticalAlert AI"
__description__ = "Real-time emergency radiology alert system"
__author__ = "CriticalAlert AI Team"
__license__ = "MIT"

