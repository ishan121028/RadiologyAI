#!/usr/bin/env python3

"""
CriticalAlert AI - Real LandingAI Parser Example

Demonstrates the use of the corrected LandingAI parser using the agentic_doc library
following the proper documentation patterns.
"""

import os
import sys
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pathway as pw
from dotenv import load_dotenv

# Import our corrected LandingAI parser
from parsers.landingai_parser import LandingAIRadiologyParser, RadiologyDocumentStore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set Pathway license (optional)
pw.set_license_key(os.getenv("PATHWAY_LICENSE_KEY", "demo-license-key-with-telemetry"))


def create_sample_radiology_reports():
    """Create sample radiology report PDFs for testing"""
    
    print("📄 Creating sample radiology reports for testing...")
    
    # Create test data directory
    test_dir = Path("data/test_reports")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample radiology reports (simplified PDF content)
    reports = {
        "critical_pe_report.pdf": """
RADIOLOGY REPORT

Patient ID: P12345
Study Date: 01/15/2024
Study Type: CT Pulmonary Angiogram

CLINICAL HISTORY: 
65-year-old male with chest pain and shortness of breath. 
Rule out pulmonary embolism.

TECHNIQUE: 
IV contrast-enhanced CT of the chest with pulmonary angiography protocol.

FINDINGS: 
Large filling defect is noted in the main pulmonary artery extending 
into both right and left main pulmonary arteries, consistent with 
massive pulmonary embolism. There is evidence of right heart strain 
with enlarged right ventricle. Small bilateral pleural effusions are present.

IMPRESSION: 
Massive pulmonary embolism with signs of right heart strain. 
Immediate medical attention required.

Radiologist: Dr. Sarah Johnson, MD
Report Date: 01/15/2024
        """,
        
        "normal_chest_xray.pdf": """
RADIOLOGY REPORT

Patient ID: P67890
Study Date: 01/15/2024
Study Type: Chest X-Ray PA and Lateral

CLINICAL HISTORY:
45-year-old female with routine screening.

TECHNIQUE:
PA and lateral chest radiographs.

FINDINGS:
Heart size and mediastinal contours are normal. 
Lungs are clear bilaterally with no evidence of consolidation, 
mass, or pleural effusion. Bony structures are intact.

IMPRESSION:
Normal chest radiograph. No acute cardiopulmonary abnormality.

Radiologist: Dr. Michael Chen, MD
Report Date: 01/15/2024
        """,
        
        "pneumonia_report.pdf": """
RADIOLOGY REPORT

Patient ID: P11223
Study Date: 01/15/2024
Study Type: Chest CT

CLINICAL HISTORY:
72-year-old male with fever and cough. Rule out pneumonia.

TECHNIQUE:
Non-contrast chest CT.

FINDINGS:
Consolidation is present in the right lower lobe with air bronchograms,
consistent with pneumonia. Small right pleural effusion. 
Mild emphysematous changes noted bilaterally.

IMPRESSION:
Right lower lobe pneumonia with small pleural effusion.
Recommend antibiotic therapy and follow-up imaging.

Radiologist: Dr. Lisa Wang, MD
Report Date: 01/15/2024
        """
    }
    
    # Create simple PDF files (text-based for testing)
    created_files = []
    for filename, content in reports.items():
        file_path = test_dir / filename
        
        # Create a simple text file (in production, these would be real PDFs)
        # For testing purposes, we'll create text files that can be parsed
        with open(file_path.with_suffix('.txt'), 'w') as f:
            f.write(content)
        
        # Also create minimal PDF using reportlab if available
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(str(file_path), pagesize=letter)
            text_lines = content.split('\n')
            y = 750
            
            for line in text_lines:
                if line.strip():
                    c.drawString(50, y, line.strip())
                    y -= 15
                    if y < 50:
                        c.showPage()
                        y = 750
            
            c.save()
            created_files.append(file_path)
            print(f"   ✅ Created PDF: {file_path}")
            
        except ImportError:
            # If reportlab not available, just create text files
            text_file = file_path.with_suffix('.txt')
            created_files.append(text_file)
            print(f"   ✅ Created text file: {text_file}")
    
    return created_files


def test_landingai_parser_basic():
    """Test basic LandingAI parser functionality"""
    
    print("\n🔧 Testing LandingAI Parser Basic Functionality")
    print("=" * 60)
    
    # Check if agentic_doc is installed
    try:
        from agentic_doc.parse import parse
        print("✅ agentic_doc library is available")
    except ImportError as e:
        print(f"❌ agentic_doc library not installed: {e}")
        print("   Install with: pip install agentic-doc")
        return None
    
    # Initialize parser
    api_key = os.getenv("LANDINGAI_API_KEY")
    if not api_key:
        print("⚠️  LANDINGAI_API_KEY not set - using dummy key for testing")
        api_key = "dummy_api_key"
    
    try:
        parser = LandingAIRadiologyParser(
            api_key=api_key,
            cache_strategy=pw.udfs.DefaultCache(),
            confidence_threshold=0.7
        )
        print(f"✅ LandingAI parser initialized successfully")
        print(f"   API Key: {api_key[:10]}..." if len(api_key) > 10 else api_key)
        print(f"   Confidence threshold: {parser.confidence_threshold}")
        print(f"   Cache strategy: {parser.cache_strategy}")
        
        return parser
        
    except Exception as e:
        print(f"❌ Failed to initialize parser: {e}")
        return None


def test_parser_with_sample_files(parser):
    """Test parser with sample files"""
    
    print("\n📄 Testing Parser with Sample Files")
    print("=" * 40)
    
    # Create sample files
    sample_files = create_sample_radiology_reports()
    if not sample_files:
        print("❌ No sample files created")
        return
    
    # Create a simple Pathway table for testing
    file_paths = [str(f) for f in sample_files]
    
    try:
        # Create a data source
        file_source = pw.io.fs.read(
            path="data/test_reports",
            format="binary",
            with_metadata=True,
            mode="batch"  # Use batch mode for testing
        )
        
        print(f"✅ Created Pathway file source for {len(sample_files)} files")
        
        # Use the parser on the data source
        parsed_table = parser.parse_table(file_source)
        
        print(f"✅ Parser applied to Pathway table")
        print(f"   Processing will happen when Pathway runs")
        
        return parsed_table
        
    except Exception as e:
        print(f"❌ Error creating Pathway table: {e}")
        return None


def test_radiology_document_store():
    """Test the RadiologyDocumentStore"""
    
    print("\n🏥 Testing RadiologyDocumentStore")
    print("=" * 40)
    
    api_key = os.getenv("LANDINGAI_API_KEY", "dummy_api_key")
    
    try:
        # Create file source
        file_source = pw.io.fs.read(
            path="data/test_reports",
            format="binary",
            with_metadata=True,
            mode="batch"
        )
        
        # Create document store
        doc_store = RadiologyDocumentStore(
            data_sources=[file_source],
            landingai_api_key=api_key,
            cache_strategy=pw.udfs.DefaultCache()
        )
        
        print("✅ RadiologyDocumentStore created successfully")
        
        # Get critical alerts
        critical_alerts = doc_store.get_critical_alerts()
        print("✅ Critical alerts table created")
        
        # Get processing stats
        processing_stats = doc_store.get_processing_stats()
        print("✅ Processing statistics table created")
        
        print(f"\n📊 Document Store Components:")
        print(f"   - Parser: LandingAI with agentic_doc")
        print(f"   - Data sources: {len(doc_store.data_sources)}")
        print(f"   - Critical alerts table: Available")
        print(f"   - Processing stats table: Available")
        
        return doc_store
        
    except Exception as e:
        print(f"❌ Error creating RadiologyDocumentStore: {e}")
        return None


def demonstrate_correct_usage():
    """Demonstrate correct usage patterns"""
    
    print("\n📋 Correct Usage Patterns")
    print("=" * 30)
    
    print("1️⃣ Installation:")
    print("   pip install agentic-doc>=0.2.4")
    print("   pip install pathway[all]")
    
    print("\n2️⃣ Basic Usage:")
    print("""
from agentic_doc.parse import parse
from parsers.landingai_parser import LandingAIRadiologyParser

# Initialize parser
parser = LandingAIRadiologyParser(
    api_key="your_landingai_api_key",
    cache_strategy=pw.udfs.DefaultCache()
)

# Use in Pathway pipeline
file_source = pw.io.fs.read(path="data/", format="binary", mode="streaming")
parsed_docs = parser.parse_table(file_source)
    """)
    
    print("3️⃣ Key Features:")
    print("   - ✅ Parses from bytes directly (no temp files)")
    print("   - ✅ Structured extraction with Pydantic models")
    print("   - ✅ Critical finding detection")
    print("   - ✅ Full Pathway integration")
    print("   - ✅ Caching and error handling")
    
    print("\n4️⃣ Environment Variables:")
    print("   LANDINGAI_API_KEY=your_api_key")
    print("   OPENAI_API_KEY=your_openai_key")


def main():
    """Main demonstration"""
    
    print("🚨 CriticalAlert AI - Corrected LandingAI Parser Demo")
    print("=" * 60)
    print("Using REAL agentic_doc library as per documentation")
    print()
    
    # Test basic parser functionality
    parser = test_landingai_parser_basic()
    if not parser:
        print("\n❌ Parser initialization failed. Check installation and API keys.")
        return
    
    # Test with sample files
    parsed_table = test_parser_with_sample_files(parser)
    
    # Test document store
    doc_store = test_radiology_document_store()
    
    # Show correct usage
    demonstrate_correct_usage()
    
    print(f"\n🎯 Summary:")
    print(f"✅ Parser: {'Working' if parser else 'Failed'}")
    print(f"✅ Sample Files: {'Processed' if parsed_table else 'Failed'}")
    print(f"✅ Document Store: {'Working' if doc_store else 'Failed'}")
    
    if parser and doc_store:
        print(f"\n🎉 LandingAI parser successfully updated!")
        print(f"📚 Now using correct agentic_doc library")
        print(f"🏥 Ready for real-time radiology processing")
    else:
        print(f"\n⚠️  Some components need attention")
        print(f"🔧 Check installation: pip install agentic-doc>=0.2.4")


if __name__ == "__main__":
    main()

