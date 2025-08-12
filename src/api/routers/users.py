"""
Users API router for the AI-Powered Enterprise Workflow Agent.
"""

from fastapi import APIRouter, Depends, HTTPException
from src.api.models import *
from src.api.dependencies import require_authentication, check_rate_limit

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(require_authentication),
    _rate_limit: None = Depends(check_rate_limit)
):
    """List all users."""
    # Implementation would go here
    return []
