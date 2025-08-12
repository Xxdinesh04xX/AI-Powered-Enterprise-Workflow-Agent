"""
API dependencies for the AI-Powered Enterprise Workflow Agent.

This module provides dependency injection functions for FastAPI
including database sessions, authentication, and authorization.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.connection import db_manager
from src.database.models import User
from src.utils.logger import get_logger

logger = get_logger("api_dependencies")

# Security scheme
security = HTTPBearer(auto_error=False)

# API Keys (in production, these should be stored securely)
VALID_API_KEYS = {
    "dev-key-123": {"name": "Development Key", "permissions": ["read", "write"]},
    "admin-key-456": {"name": "Admin Key", "permissions": ["read", "write", "admin"]},
    "readonly-key-789": {"name": "Read-Only Key", "permissions": ["read"]}
}

def get_db_session() -> Session:
    """Get database session dependency."""
    try:
        with db_manager.get_session() as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify API key authentication."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return VALID_API_KEYS[x_api_key]

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
    db_session: Session = Depends(get_db_session)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user (optional)."""
    
    # Try API key authentication first
    if x_api_key:
        try:
            api_key_info = verify_api_key(x_api_key)
            return {
                "type": "api_key",
                "name": api_key_info["name"],
                "permissions": api_key_info["permissions"],
                "authenticated": True
            }
        except HTTPException:
            pass
    
    # Try JWT token authentication
    if credentials:
        try:
            # In a real implementation, you would verify the JWT token here
            # For now, we'll just return a mock user
            return {
                "type": "jwt",
                "user_id": 1,
                "name": "JWT User",
                "permissions": ["read", "write"],
                "authenticated": True
            }
        except Exception as e:
            logger.warning(f"JWT authentication failed: {e}")
    
    # Return anonymous user for public endpoints
    return {
        "type": "anonymous",
        "name": "Anonymous",
        "permissions": ["read"],
        "authenticated": False
    }

def require_authentication(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require authentication for protected endpoints."""
    if not current_user.get("authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user

def require_permission(permission: str):
    """Require specific permission for endpoint access."""
    def permission_checker(current_user: Dict[str, Any] = Depends(require_authentication)) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
) -> Dict[str, int]:
    """Get pagination parameters."""
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }

def get_filter_params(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_team_id: Optional[int] = Query(None, description="Filter by assigned team"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date (after)"),
    created_before: Optional[datetime] = Query(None, description="Filter by creation date (before)")
) -> Dict[str, Any]:
    """Get filter parameters for queries."""
    filters = {}
    
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    if priority:
        filters["priority"] = priority
    if assigned_team_id:
        filters["assigned_team_id"] = assigned_team_id
    if created_after:
        filters["created_after"] = created_after
    if created_before:
        filters["created_before"] = created_before
    
    return filters

def get_sort_params(
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
) -> Dict[str, str]:
    """Get sorting parameters."""
    return {
        "sort_by": sort_by,
        "sort_order": sort_order
    }

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int = 3600) -> bool:
        """Check if request is allowed within rate limit."""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window
        ]
        
        # Check if under limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(
    current_user: Dict[str, Any] = Depends(get_current_user),
    x_forwarded_for: Optional[str] = Header(None)
) -> None:
    """Check rate limits for requests."""
    
    # Determine rate limit based on authentication
    if current_user.get("authenticated", False):
        limit = 1000  # 1000 requests per hour for authenticated users
        key = f"user_{current_user.get('name', 'unknown')}"
    else:
        limit = 100   # 100 requests per hour for unauthenticated users
        # Use IP address for anonymous users
        ip = x_forwarded_for or "unknown"
        key = f"ip_{ip}"
    
    if not rate_limiter.is_allowed(key, limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "3600"}
        )

def validate_task_access(
    task_id: int,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db_session: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Validate user access to a specific task."""
    
    from src.database.models import Task
    
    task = db_session.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Admin users can access all tasks
    if "admin" in current_user.get("permissions", []):
        return {"task": task, "access_level": "admin"}
    
    # For now, all authenticated users can access all tasks
    # In a real implementation, you might check team membership, etc.
    return {"task": task, "access_level": "read_write"}

def validate_team_access(
    team_id: int,
    current_user: Dict[str, Any] = Depends(require_authentication),
    db_session: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Validate user access to a specific team."""
    
    from src.database.models import Team
    
    team = db_session.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    # Admin users can access all teams
    if "admin" in current_user.get("permissions", []):
        return {"team": team, "access_level": "admin"}
    
    # For now, all authenticated users can access all teams
    return {"team": team, "access_level": "read"}

def get_request_context(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_agent: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """Get request context information."""
    return {
        "user": current_user,
        "user_agent": user_agent,
        "ip_address": x_forwarded_for,
        "timestamp": datetime.utcnow()
    }
