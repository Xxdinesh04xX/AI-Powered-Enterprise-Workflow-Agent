"""
Database initialization script for the AI-Powered Enterprise Workflow Agent.

This script creates the database tables and sets up initial data
required for the workflow agent to function properly.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import init_database
from src.utils.logger import get_logger

logger = get_logger("init_db")

def main():
    """Initialize the database."""
    try:
        logger.info("Starting database initialization...")
        init_database()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
