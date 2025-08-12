"""
Main FastAPI application for the AI-Powered Enterprise Workflow Agent.

This module provides the REST API server with comprehensive endpoints
for task management, workflow processing, reporting, and system monitoring.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import Request

from src.api.models import *
from src.api.dependencies import get_db_session, get_current_user, verify_api_key
from src.api.routers import tasks, workflows, reports, teams, users, system
from src.database.connection import init_database
from src.utils.logger import get_logger

logger = get_logger("api_main")

# Application metadata
APP_VERSION = "1.0.0"
APP_TITLE = "AI-Powered Enterprise Workflow Agent API"
APP_DESCRIPTION = """
## AI-Powered Enterprise Workflow Agent API

A comprehensive REST API for automating enterprise workflows using AI agents.

### Features

* **Task Management**: Create, update, and track workflow tasks
* **AI Classification**: Automatically classify tasks by category and priority
* **Smart Assignment**: Intelligently assign tasks to appropriate teams
* **Workflow Processing**: End-to-end workflow automation
* **Analytics & Reporting**: Generate comprehensive reports with insights
* **Team Management**: Manage teams, users, and capabilities
* **System Monitoring**: Health checks and performance metrics

### Authentication

This API supports multiple authentication methods:
- API Key authentication for service-to-service communication
- JWT tokens for user authentication
- Basic authentication for development

### Rate Limiting

API endpoints are rate-limited to ensure fair usage:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated requests

### Webhooks

The API supports webhook notifications for real-time updates:
- Task status changes
- Workflow completions
- System alerts
"""

# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
templates = Jinja2Templates(directory="src/web/templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for tracking
startup_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting AI-Powered Enterprise Workflow Agent API...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
        
        # Additional startup tasks can be added here
        logger.info(f"API server started successfully on version {APP_VERSION}")
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down AI-Powered Enterprise Workflow Agent API...")

# Include routers
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])

# Root endpoint - Beautiful Web Interface
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the beautiful web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

# API Root endpoint
@app.get("/api", response_model=Dict[str, Any])
async def api_root():
    """API root endpoint with information."""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json"
    }

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connectivity
        from src.database.connection import db_manager
        db_healthy = True
        try:
            with db_manager.get_session() as session:
                session.execute("SELECT 1")
        except Exception as e:
            db_healthy = False
            logger.error(f"Database health check failed: {e}")
        
        # Check system components
        components = {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "details": "Database connection successful" if db_healthy else "Database connection failed"
            },
            "api": {
                "status": "healthy",
                "details": "API server running normally"
            },
            "uptime": {
                "status": "healthy",
                "details": f"System uptime: {time.time() - startup_time:.2f} seconds"
            }
        }
        
        overall_status = "healthy" if all(c["status"] == "healthy" for c in components.values()) else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            components=components,
            version=APP_VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# API Info endpoint
@app.get("/api/v1/info", response_model=Dict[str, Any])
async def api_info():
    """Get API information and capabilities."""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "description": "AI-Powered Enterprise Workflow Agent API",
        "capabilities": [
            "Task Management",
            "AI Classification",
            "Smart Assignment", 
            "Workflow Processing",
            "Analytics & Reporting",
            "Team Management",
            "System Monitoring"
        ],
        "endpoints": {
            "tasks": "/api/v1/tasks",
            "workflows": "/api/v1/workflows", 
            "reports": "/api/v1/reports",
            "teams": "/api/v1/teams",
            "users": "/api/v1/users",
            "system": "/api/v1/system"
        },
        "authentication": [
            "API Key",
            "JWT Token",
            "Basic Auth"
        ],
        "supported_formats": [
            "JSON",
            "HTML",
            "PDF"
        ],
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

# Statistics endpoint
@app.get("/api/v1/statistics", response_model=StatisticsResponse)
async def get_statistics(db_session=Depends(get_db_session)):
    """Get system statistics."""
    try:
        from src.database.operations import AnalyticsOperations
        from src.database.models import Task, TaskStatus, TaskCategory, TaskPriority
        
        # Get basic task statistics
        total_tasks = db_session.query(Task).count()
        
        # Tasks by status
        tasks_by_status = {}
        for status in TaskStatus:
            count = db_session.query(Task).filter(Task.status == status).count()
            tasks_by_status[status.value] = count
        
        # Tasks by category
        tasks_by_category = {}
        for category in TaskCategory:
            count = db_session.query(Task).filter(Task.category == category).count()
            tasks_by_category[category.value] = count
        
        # Tasks by priority
        tasks_by_priority = {}
        for priority in TaskPriority:
            count = db_session.query(Task).filter(Task.priority == priority).count()
            tasks_by_priority[priority.value] = count
        
        # Agent statistics (simplified)
        agent_statistics = {
            "classification_agent": {"status": "active", "success_rate": 0.95},
            "assignment_agent": {"status": "active", "success_rate": 0.92},
            "reporter_agent": {"status": "active", "success_rate": 0.98}
        }
        
        return StatisticsResponse(
            total_tasks=total_tasks,
            tasks_by_status=tasks_by_status,
            tasks_by_category=tasks_by_category,
            tasks_by_priority=tasks_by_priority,
            agent_statistics=agent_statistics,
            system_uptime=time.time() - startup_time,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        routes=app.routes,
    )
    
    # Add custom security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [
        {"ApiKeyAuth": []},
        {"BearerAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            timestamp=datetime.utcnow()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"exception": str(exc)},
            timestamp=datetime.utcnow()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
