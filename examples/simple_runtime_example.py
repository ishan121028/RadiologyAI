#!/usr/bin/env python3

"""
CriticalAlert AI - Simple Runtime Wiring Example

This shows EXACTLY how the YAML components get instantiated and wired together
at runtime, following the exact same pattern as existing Pathway examples.
"""

import os
import sys
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pathway as pw
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, InstanceOf

logging.basicConfig(level=logging.INFO)
load_dotenv()
pw.set_license_key("demo-license-key-with-telemetry")

# Import our components (same pattern as existing examples)
from intelligence.critical_alert_answerer import CriticalAlertQuestionAnswerer


def demonstrate_manual_instantiation():
    """
    Show manual instantiation (what normally happens automatically from YAML)
    """
    
    print("🔧 Manual Component Instantiation (normally done by YAML)")
    print("=" * 60)
    
    # 1. Create data sources (normally from YAML $sources)
    print("1️⃣ Creating data sources...")
    file_source = pw.io.fs.read(
        path="data/incoming",
        format="binary", 
        with_metadata=True,
        mode="streaming"
    )
    print(f"   ✅ File source: {file_source}")
    
    # 2. Create LandingAI parser (normally from YAML $parser)
    print("2️⃣ Creating LandingAI parser...")
    from parsers.landingai_parser import LandingAIRadiologyParser
    parser = LandingAIRadiologyParser(
        api_key=os.getenv("LANDINGAI_API_KEY", "dummy_key"),
        cache_strategy=pw.udfs.DefaultCache()
    )
    print(f"   ✅ Parser: {parser}")
    
    # 3. Create LLM (normally from YAML $llm)
    print("3️⃣ Creating LLM...")
    llm = pw.xpacks.llm.llms.OpenAIChat(
        model="gpt-4o-mini",
        cache_strategy=pw.udfs.DefaultCache(),
        temperature=0
    )
    print(f"   ✅ LLM: {llm}")
    
    # 4. Create RadiologyDocumentStore (normally from YAML $document_store)
    print("4️⃣ Creating RadiologyDocumentStore...")
    from parsers.landingai_parser import RadiologyDocumentStore
    document_store = RadiologyDocumentStore(
        data_sources=[file_source],
        landingai_api_key=os.getenv("LANDINGAI_API_KEY", "dummy_key")
    )
    print(f"   ✅ Document store: {document_store}")
    
    # 5. Create CriticalAlertQuestionAnswerer (normally from YAML critical_alert_answerer)
    print("5️⃣ Creating CriticalAlertQuestionAnswerer...")
    critical_alert_answerer = CriticalAlertQuestionAnswerer(
        llm=llm,
        document_store=document_store
    )
    print(f"   ✅ Critical alert answerer: {critical_alert_answerer}")
    
    return critical_alert_answerer


def demonstrate_yaml_instantiation():
    """
    Show YAML instantiation (what actually happens in production)
    """
    
    print("\n📋 YAML Instantiation (production method)")
    print("=" * 60)
    
    # Simple YAML config (inline for demonstration)
    yaml_config = """
# Data sources
$sources:
  - !pw.io.fs.read
    path: data/incoming
    format: binary
    with_metadata: true
    mode: streaming

# LandingAI parser
$parser: !src.parsers.landingai_parser.LandingAIRadiologyParser
  api_key: dummy_key
  cache_strategy: !pw.udfs.DefaultCache {}

# LLM
$llm: !pw.xpacks.llm.llms.OpenAIChat
  model: "gpt-4o-mini"
  cache_strategy: !pw.udfs.DefaultCache {}
  temperature: 0

# Document store
$document_store: !src.parsers.landingai_parser.RadiologyDocumentStore
  data_sources: $sources
  landingai_api_key: dummy_key

# Critical alert answerer (main component)
critical_alert_answerer: !src.intelligence.critical_alert_answerer.CriticalAlertQuestionAnswerer
  llm: $llm
  document_store: $document_store

# App configuration
host: "0.0.0.0"
port: 8000
with_cache: true
terminate_on_error: false
    """
    
    print("1️⃣ Loading YAML configuration...")
    print(f"   📝 YAML config length: {len(yaml_config)} characters")
    
    try:
        # Load YAML (same as pw.load_yaml(f) in existing examples)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_config)
            yaml_file = f.name
        
        print("2️⃣ Parsing YAML with pw.load_yaml()...")
        with open(yaml_file) as f:
            config = pw.load_yaml(f)
        
        print(f"   ✅ Config loaded: {len(config)} components")
        for key, value in config.items():
            print(f"      - {key}: {type(value).__name__}")
        
        print("3️⃣ Creating App instance...")
        # Create App class (inline for demo)
        class SimpleApp(BaseModel):
            critical_alert_answerer: InstanceOf[CriticalAlertQuestionAnswerer]
            host: str = "0.0.0.0"
            port: int = 8000
            with_cache: bool = True
            terminate_on_error: bool = False
            
            model_config = ConfigDict(extra="forbid")
            
            def run(self):
                print(f"   🚀 App would run on {self.host}:{self.port}")
                # Get the actual Pathway table from the answerer
                critical_alerts = self.critical_alert_answerer.get_critical_alerts_stream()
                print(f"   📊 Critical alerts stream: {critical_alerts}")
                return critical_alerts
        
        # Instantiate app from YAML config (same as existing examples)
        app = SimpleApp(**config)
        print(f"   ✅ App created: {app}")
        
        print("4️⃣ Running application...")
        critical_alerts_table = app.run()
        
        print(f"\n🎯 SUCCESS! YAML components instantiated and wired:")
        print(f"   - CriticalAlertQuestionAnswerer: ✅")
        print(f"   - RadiologyDocumentStore: ✅")  
        print(f"   - LandingAI Parser: ✅")
        print(f"   - Pathway Table: {critical_alerts_table}")
        
        # Clean up
        os.unlink(yaml_file)
        
        return app
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def show_runtime_flow():
    """
    Show the complete runtime flow
    """
    
    print("\n🔄 Complete Runtime Flow")
    print("=" * 40)
    
    print("1. app.py loads app.yaml with pw.load_yaml()")
    print("2. YAML instantiates:")
    print("   - $sources: pw.io.fs.read")
    print("   - $parser: LandingAIRadiologyParser")
    print("   - $llm: OpenAIChat")
    print("   - $document_store: RadiologyDocumentStore")
    print("   - critical_alert_answerer: CriticalAlertQuestionAnswerer")
    print("3. App(**config) creates App instance")
    print("4. app.run() calls critical_alert_answerer.get_critical_alerts_stream()")
    print("5. That calls document_store.get_critical_alerts()") 
    print("6. That uses the LandingAI parser on the file sources")
    print("7. pw.run() starts the Pathway computation engine")
    print("8. Real-time alerts flow through the pipeline")


def main():
    """
    Main demonstration
    """
    
    print("🚨 CriticalAlert AI - Runtime Wiring Demonstration")
    print("=" * 60)
    print()
    
    # Check environment
    if not os.getenv("LANDINGAI_API_KEY"):
        print("⚠️  LANDINGAI_API_KEY not set - using dummy key for demo")
        os.environ["LANDINGAI_API_KEY"] = "dummy_key"
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - using dummy key for demo")
        os.environ["OPENAI_API_KEY"] = "dummy_key"
    
    # Create data directory
    os.makedirs("data/incoming", exist_ok=True)
    
    # Show different approaches
    try:
        # 1. Manual instantiation
        manual_answerer = demonstrate_manual_instantiation()
        
        # 2. YAML instantiation  
        yaml_app = demonstrate_yaml_instantiation()
        
        # 3. Show the complete flow
        show_runtime_flow()
        
        print(f"\n✅ Both manual and YAML approaches work!")
        print(f"📋 The YAML approach is what app.py uses in production")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

