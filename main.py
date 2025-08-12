"""
Main entry point for the AI-Powered Enterprise Workflow Agent.

This script provides a command-line interface to start different components
of the workflow agent system including the API server, dashboard, and
database initialization.
"""

import click
import uvicorn
import subprocess
import sys
from pathlib import Path

from src.core.config import config
from src.utils.logger import get_logger

logger = get_logger("main")

@click.group()
@click.version_option(version="1.0")
def cli():
    """AI-Powered Enterprise Workflow Agent - Command Line Interface"""
    pass

@cli.command()
@click.option("--host", default=None, help="Host to bind the server to")
@click.option("--port", default=None, type=int, help="Port to bind the server to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def start_api(host, port, reload):
    """Start the FastAPI backend server."""
    host = host or config.api.host
    port = port or config.api.port
    reload = reload or config.api.reload
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=config.api.workers if not reload else 1
    )

@cli.command()
@click.option("--host", default=None, help="Host to bind the dashboard to")
@click.option("--port", default=None, type=int, help="Port to bind the dashboard to")
def start_dashboard(host, port):
    """Start the Streamlit dashboard."""
    host = host or config.streamlit.host
    port = port or config.streamlit.port
    
    logger.info(f"Starting Streamlit dashboard on {host}:{port}")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/dashboard.py",
        "--server.address", host,
        "--server.port", str(port)
    ]
    
    subprocess.run(cmd)

@cli.command()
def init_db():
    """Initialize the database with required tables."""
    logger.info("Initializing database...")
    
    try:
        from src.database.models import init_database
        init_database()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

@cli.command()
def create_sample_data():
    """Create sample data for testing and development."""
    logger.info("Creating sample data...")
    
    try:
        from scripts.create_sample_data import create_sample_data
        create_sample_data()
        logger.info("Sample data created successfully!")
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        sys.exit(1)

@cli.command()
def run_tests():
    """Run the test suite."""
    logger.info("Running tests...")
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed!")
        sys.exit(1)

@cli.command()
def start_all():
    """Start both API server and dashboard (development mode)."""
    import threading
    import time
    
    logger.info("Starting all services...")
    
    # Start API server in a separate thread
    api_thread = threading.Thread(
        target=lambda: uvicorn.run(
            "src.api.main:app",
            host=config.api.host,
            port=config.api.port,
            reload=False
        )
    )
    api_thread.daemon = True
    api_thread.start()
    
    # Wait a moment for API to start
    time.sleep(3)
    
    # Start dashboard
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/dashboard.py",
        "--server.address", config.streamlit.host,
        "--server.port", str(config.streamlit.port)
    ]
    
    subprocess.run(cmd)

@cli.command()
def check_config():
    """Check and validate configuration."""
    logger.info("Checking configuration...")
    
    # Check required directories
    required_dirs = ["data", "logs", "reports", "templates"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            logger.warning(f"Creating missing directory: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory exists: {dir_name}")
    
    # Check API keys
    if not config.llm.openai_api_key and not config.llm.groq_api_key:
        logger.warning("No LLM API keys configured. Please set OPENAI_API_KEY or GROQ_API_KEY")
    else:
        logger.info("LLM API keys configured")
    
    logger.info("Configuration check completed!")

if __name__ == "__main__":
    cli()
