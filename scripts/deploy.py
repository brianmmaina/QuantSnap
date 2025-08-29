#!/usr/bin/env python3
"""
Deployment script for QuantSnap on Render
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'requirements.txt',
        'Dockerfile',
        'render.yaml',
        'src/frontend.py',
        'src/backend.py',
        'infrastructure/schema.sql'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files found")
    return True

def check_environment():
    """Check environment variables"""
    required_env_vars = [
        'GEMINI_API_KEY',
        'NEWS_API_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nThese will need to be set in Render dashboard")
    else:
        print("✅ All environment variables found")
    
    return True

def create_env_file():
    """Create .env file from template"""
    if not Path('.env').exists() and Path('env.template').exists():
        print("📝 Creating .env file from template...")
        with open('env.template', 'r') as f:
            template = f.read()
        
        with open('.env', 'w') as f:
            f.write(template)
        
        print("✅ .env file created (please fill in your API keys)")
    else:
        print("✅ .env file already exists")

def main():
    """Main deployment setup"""
    print("🚀 QuantSnap Deployment Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Create env file
    create_env_file()
    
    print("\n📋 Deployment Checklist:")
    print("1. ✅ Project structure organized")
    print("2. ✅ Dockerfile created")
    print("3. ✅ render.yaml configured")
    print("4. ✅ Requirements.txt updated")
    print("\n🎯 Next Steps:")
    print("1. Push code to GitHub")
    print("2. Connect repository to Render")
    print("3. Set environment variables in Render dashboard")
    print("4. Deploy services")
    
    print("\n🔗 Render Dashboard: https://dashboard.render.com")
    print("📚 Documentation: https://render.com/docs")

if __name__ == "__main__":
    main()
