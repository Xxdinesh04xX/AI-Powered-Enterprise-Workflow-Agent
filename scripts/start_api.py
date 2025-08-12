"""
API server startup script for the AI-Powered Enterprise Workflow Agent.

This script starts the FastAPI server for testing and development.
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Start the API server."""
    
    # Configuration
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "true").lower() == "true"
    
    print(f"Starting AI-Powered Enterprise Workflow Agent API...")
    print(f"Server: http://{host}:{port}")
    print(f"Documentation: http://{host}:{port}/docs")
    print(f"Debug mode: {debug}")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nShutting down API server...")
    except Exception as e:
        print(f"Failed to start API server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
