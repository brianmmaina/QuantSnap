#!/usr/bin/env python3
"""
Frontend startup script for Render deployment
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the frontend
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # Set up Streamlit arguments
    sys.argv = [
        "streamlit", "run", 
        str(src_path / "frontend.py"),
        "--server.port", os.getenv("PORT", "8501"),
        "--server.address", "0.0.0.0"
    ]
    
    # Run Streamlit
    sys.exit(stcli.main())
