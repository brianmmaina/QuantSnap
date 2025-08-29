#!/usr/bin/env python3
"""
Start script for AI Daily Draft
Runs both the FastAPI backend and Streamlit frontend
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_api():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    try:
        # Start API in background
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.backend:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        print("✅ FastAPI backend started on http://localhost:8000")
        return api_process
    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        return None

def start_streamlit():
    """Start the Streamlit frontend"""
    print("🎨 Starting Streamlit frontend...")
    try:
        # Start Streamlit
        streamlit_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "src/frontend.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        print("✅ Streamlit frontend started on http://localhost:8501")
        return streamlit_process
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return None

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "streamlit", "fastapi", "uvicorn", "psycopg2-binary", 
        "sqlalchemy", "pandas", "yfinance"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🎯 AI Daily Draft - Starting Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment variables
    if not os.getenv('DATABASE_URL'):
        print("⚠️  DATABASE_URL not set. Using default: postgresql://localhost/ai_daily_draft")
        print("   Set DATABASE_URL environment variable for production use.")
    
    # Start API
    api_process = start_api()
    if not api_process:
        sys.exit(1)
    
    # Wait a moment for API to start
    time.sleep(3)
    
    # Start Streamlit
    streamlit_process = start_streamlit()
    if not streamlit_process:
        api_process.terminate()
        sys.exit(1)
    
    print("\n🎉 Application started successfully!")
    print("📊 Frontend: http://localhost:8501")
    print("🔧 API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both services...")
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ API process stopped unexpectedly")
                break
            if streamlit_process.poll() is not None:
                print("❌ Streamlit process stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
    finally:
        # Cleanup
        if api_process:
            api_process.terminate()
            api_process.wait()
        if streamlit_process:
            streamlit_process.terminate()
            streamlit_process.wait()
        print("✅ Application stopped")

if __name__ == "__main__":
    main()
