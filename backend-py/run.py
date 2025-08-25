#!/usr/bin/env python3
"""
Budget PWA Backend Development Server
Run this script for development purposes.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def main():
    # Set development environment
    os.environ.setdefault("ENVIRONMENT", "development")
    
    # Load .env file if it exists
    env_file = app_dir / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    
    # Get configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🚀 Starting Budget PWA Backend on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/api/health")
    print("🛑 Press Ctrl+C to stop")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(app_dir / "app")],
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()