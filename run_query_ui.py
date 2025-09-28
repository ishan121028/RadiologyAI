#!/usr/bin/env python3

"""
CriticalAlert AI - Query UI Launcher
Simple launcher for the document query interface
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the query interface"""
    
    print("🔍 Starting CriticalAlert AI Query Interface...")
    print("📍 Make sure the main CriticalAlert AI service is running on port 49001")
    print("🌐 The query interface will open in your browser")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 60)
    
    # Path to the query interface
    query_interface_path = Path("src/dashboard/query_interface.py")
    
    if not query_interface_path.exists():
        print("❌ Error: Query interface not found!")
        print(f"Expected path: {query_interface_path.absolute()}")
        return 1
    
    try:
        # Run streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(query_interface_path),
            "--server.port", "8502",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Query interface stopped")
        return 0
    except Exception as e:
        print(f"❌ Error starting query interface: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
