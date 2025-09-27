#!/usr/bin/env python3

"""
CriticalAlert AI - Simple Usage Example

Shows how to use app.yaml configuration exactly like other Pathway examples:
- demo-question-answering/app.py
- adaptive-rag/app.py
- private-rag/app.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pathway as pw
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Pathway license (optional)
pw.set_license_key("demo-license-key-with-telemetry")

def run_with_yaml_config():
    """
    Run CriticalAlert AI using YAML configuration
    
    This demonstrates the exact same usage pattern as existing Pathway examples
    """
    
    print("🚨 CriticalAlert AI - YAML Configuration Example")
    print("=" * 60)
    
    # Check required environment variables
    required_vars = ["LANDINGAI_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        return
    
    # Use minimal configuration
    config_file = Path(__file__).parent / "minimal_app.yaml"
    
    print(f"📋 Using configuration: {config_file}")
    print(f"📂 Monitoring directory: data/incoming")
    print(f"🔑 LandingAI API Key: {os.getenv('LANDINGAI_API_KEY')[:10]}...")
    print()
    
    try:
        # Load YAML configuration (same as other Pathway examples)
        with open(config_file) as f:
            config = pw.load_yaml(f)
        
        print("✅ Configuration loaded successfully")
        print()
        
        # Show what components were loaded
        print("🔧 Loaded components:")
        for key, value in config.items():
            if hasattr(value, '__class__'):
                print(f"   - {key}: {value.__class__.__name__}")
            else:
                print(f"   - {key}: {type(value).__name__}")
        print()
        
        # Create app instance (same pattern as other examples)
        from app import App
        app = App(**config)
        
        print("🚀 Starting CriticalAlert AI...")
        print("   📡 Real-time monitoring enabled")
        print("   🏥 Medical intelligence active")
        print("   🚨 Critical alert detection ready")
        print()
        print("💡 Add radiology report PDFs to 'data/incoming/' to see alerts")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        # Run the application
        app.run()
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_file}")
        print("   Make sure you're running from the correct directory")
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()


def create_test_data():
    """Create test data directory and sample files"""
    
    print("📂 Setting up test data directory...")
    
    # Create directories
    data_dir = Path("data")
    incoming_dir = data_dir / "incoming"
    processed_dir = data_dir / "processed" 
    alerts_dir = data_dir / "alerts"
    
    for directory in [incoming_dir, processed_dir, alerts_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}")
    
    print("\n💡 Directory structure ready!")
    print("   📥 Drop radiology PDFs in: data/incoming/")
    print("   📤 Processed files go to: data/processed/")
    print("   🚨 Critical alerts saved in: data/alerts/")


def show_yaml_usage():
    """Show YAML configuration usage examples"""
    
    print("📋 YAML Configuration Examples")
    print("=" * 40)
    
    print("\n1️⃣  Basic Usage (like DoclingParser):")
    print("""
$parser: !src.parsers.landingai_parser.LandingAIRadiologyParser
  api_key: $LANDINGAI_API_KEY
  cache_strategy: !pw.udfs.DefaultCache {}
    """)
    
    print("2️⃣  Document Store (like DocumentStore):")
    print("""
$document_store: !src.parsers.landingai_parser.RadiologyDocumentStore
  data_sources: $sources
  landingai_api_key: $LANDINGAI_API_KEY
  cache_strategy: !pw.udfs.DefaultCache {}
    """)
    
    print("3️⃣  Critical Alert Answerer (like RAGQuestionAnswerer):")
    print("""
critical_alert_answerer: !src.intelligence.critical_alert_answerer.CriticalAlertQuestionAnswerer
  llm: $llm
  document_store: $document_store
    """)
    
    print("4️⃣  Run exactly like other Pathway examples:")
    print("""
# Same as demo-question-answering, adaptive-rag, etc.
python app.py                    # Use default app.yaml
python app.py minimal_app.yaml   # Use custom config
    """)


def main():
    """Main example runner"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            create_test_data()
        elif command == "yaml":
            show_yaml_usage()
        elif command == "run":
            run_with_yaml_config()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_example.py [setup|yaml|run]")
    else:
        print("🚨 CriticalAlert AI - Usage Examples")
        print("=" * 40)
        print()
        print("Available commands:")
        print("  python run_example.py setup    # Create test directories")
        print("  python run_example.py yaml     # Show YAML usage")
        print("  python run_example.py run      # Run the application")
        print()
        print("Environment variables needed:")
        print("  export LANDINGAI_API_KEY='your_key'")
        print("  export OPENAI_API_KEY='your_openai_key'")


if __name__ == "__main__":
    main()
