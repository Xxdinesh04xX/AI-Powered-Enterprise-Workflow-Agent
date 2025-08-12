"""
Database connection management for the AI-Powered Enterprise Workflow Agent.

This module handles database connection setup, session management,
and database initialization.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import os

from src.core.config import config
from src.utils.logger import get_logger

logger = get_logger("database")

# Create the SQLAlchemy base class
Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the database engine."""
        database_url = config.database.url
        
        # Configure engine based on database type
        if database_url.startswith("sqlite"):
            # SQLite specific configuration
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=config.database.echo
            )
            
            # Enable foreign key constraints for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL or other database configuration
            self.engine = create_engine(
                database_url,
                pool_size=config.database.pool_size,
                max_overflow=config.database.max_overflow,
                echo=config.database.echo
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database engine initialized with URL: {database_url}")
    
    def create_tables(self):
        """Create all database tables."""
        try:
            # Import all models to ensure they're registered
            from src.database.models import (
                Task, Classification, Assignment, Report, 
                Team, User, WorkflowExecution
            )
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session for synchronous operations."""
        return self.SessionLocal()

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Generator[Session, None, None]:
    """Dependency function for FastAPI to get database sessions."""
    with db_manager.get_session() as session:
        yield session

def init_database():
    """Initialize the database with tables and initial data."""
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Create tables
        db_manager.create_tables()
        
        # Create initial data if needed
        _create_initial_data()
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def _create_initial_data():
    """Create initial data for the database."""
    try:
        with db_manager.get_session() as session:
            from src.database.models import Team, User
            
            # Check if initial data already exists
            if session.query(Team).count() > 0:
                logger.info("Initial data already exists, skipping creation")
                return
            
            # Create default teams
            teams_data = [
                # IT Teams
                {"name": "DevOps Team", "category": "IT", "description": "Infrastructure and deployment automation"},
                {"name": "Infrastructure Team", "category": "IT", "description": "Server and network management"},
                {"name": "Security Team", "category": "IT", "description": "Cybersecurity and compliance"},
                {"name": "Application Support", "category": "IT", "description": "Application maintenance and support"},

                # HR Teams
                {"name": "Recruitment Team", "category": "HR", "description": "Talent acquisition and hiring"},
                {"name": "Employee Relations", "category": "HR", "description": "Employee engagement and relations"},
                {"name": "Payroll Team", "category": "HR", "description": "Payroll processing and benefits"},
                {"name": "Training & Development", "category": "HR", "description": "Employee training and development"},

                # Operations Teams
                {"name": "Project Management", "category": "OPERATIONS", "description": "Project planning and execution"},
                {"name": "Quality Assurance", "category": "OPERATIONS", "description": "Quality control and testing"},
                {"name": "Business Analysis", "category": "OPERATIONS", "description": "Business process analysis"},
                {"name": "Process Improvement", "category": "OPERATIONS", "description": "Operational efficiency optimization"},
            ]
            
            for team_data in teams_data:
                # Convert category string to enum
                from src.database.models import TaskCategory
                category_str = team_data["category"]
                if category_str == "IT":
                    team_data["category"] = TaskCategory.IT
                elif category_str == "HR":
                    team_data["category"] = TaskCategory.HR
                elif category_str == "OPERATIONS":
                    team_data["category"] = TaskCategory.OPERATIONS

                team = Team(**team_data)
                session.add(team)
            
            # Create default users
            users_data = [
                {"name": "System Admin", "email": "admin@company.com", "role": "admin"},
                {"name": "IT Manager", "email": "it.manager@company.com", "role": "manager"},
                {"name": "HR Manager", "email": "hr.manager@company.com", "role": "manager"},
                {"name": "Operations Manager", "email": "ops.manager@company.com", "role": "manager"},
            ]
            
            for user_data in users_data:
                user = User(**user_data)
                session.add(user)
            
            session.commit()
            logger.info("Initial data created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        raise
