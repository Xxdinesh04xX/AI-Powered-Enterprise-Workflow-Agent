"""
API models for the AI-Powered Enterprise Workflow Agent.

This module defines Pydantic models for API request/response validation
and serialization.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class TaskStatusAPI(str, Enum):
    """Task status enum for API."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskCategoryAPI(str, Enum):
    """Task category enum for API."""
    IT = "IT"
    HR = "HR"
    OPERATIONS = "Operations"

class TaskPriorityAPI(str, Enum):
    """Task priority enum for API."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    title: str = Field(..., description="Task title", max_length=200)
    description: str = Field(..., description="Task description", max_length=2000)
    original_request: str = Field(..., description="Original natural language request", max_length=5000)
    category: Optional[TaskCategoryAPI] = Field(None, description="Task category")
    priority: Optional[TaskPriorityAPI] = Field(None, description="Task priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")

class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, description="Task title", max_length=200)
    description: Optional[str] = Field(None, description="Task description", max_length=2000)
    status: Optional[TaskStatusAPI] = Field(None, description="Task status")
    category: Optional[TaskCategoryAPI] = Field(None, description="Task category")
    priority: Optional[TaskPriorityAPI] = Field(None, description="Task priority")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")

class TaskResponse(BaseModel):
    """Response model for task data."""
    id: int = Field(..., description="Task ID")
    uuid: str = Field(..., description="Task UUID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    original_request: str = Field(..., description="Original request")
    status: TaskStatusAPI = Field(..., description="Task status")
    category: Optional[TaskCategoryAPI] = Field(None, description="Task category")
    priority: Optional[TaskPriorityAPI] = Field(None, description="Task priority")
    assigned_team_id: Optional[int] = Field(None, description="Assigned team ID")
    assigned_user_id: Optional[int] = Field(None, description="Assigned user ID")
    classification_confidence: Optional[float] = Field(None, description="Classification confidence")
    assignment_confidence: Optional[float] = Field(None, description="Assignment confidence")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Task metadata")

class WorkflowProcessRequest(BaseModel):
    """Request model for processing a workflow."""
    task_id: int = Field(..., description="Task ID to process")
    strategy: Optional[str] = Field("hybrid", description="Processing strategy")
    force_reprocess: bool = Field(False, description="Force reprocessing even if already processed")

class WorkflowProcessResponse(BaseModel):
    """Response model for workflow processing."""
    success: bool = Field(..., description="Processing success status")
    task_id: int = Field(..., description="Processed task ID")
    execution_time: float = Field(..., description="Execution time in seconds")
    steps: Dict[str, Any] = Field(..., description="Processing steps results")
    final_state: Dict[str, Any] = Field(..., description="Final task state")
    timestamp: datetime = Field(..., description="Processing timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")

class ReportGenerateRequest(BaseModel):
    """Request model for generating reports."""
    report_type: str = Field("daily", description="Type of report to generate")
    output_formats: List[str] = Field(["html", "json"], description="Output formats")
    start_date: Optional[datetime] = Field(None, description="Report start date")
    end_date: Optional[datetime] = Field(None, description="Report end date")
    categories: Optional[List[str]] = Field(None, description="Categories to include")
    include_analytics: bool = Field(True, description="Include analytics data")
    use_ai_insights: bool = Field(True, description="Use AI-generated insights")

class ReportGenerateResponse(BaseModel):
    """Response model for report generation."""
    report_id: int = Field(..., description="Generated report ID")
    report_type: str = Field(..., description="Report type")
    generated_files: Dict[str, str] = Field(..., description="Generated file paths")
    generation_timestamp: datetime = Field(..., description="Generation timestamp")
    period: Dict[str, str] = Field(..., description="Report period")

class ClassificationRequest(BaseModel):
    """Request model for task classification."""
    text: str = Field(..., description="Text to classify", max_length=5000)
    title: Optional[str] = Field(None, description="Task title", max_length=200)
    strategy: str = Field("hybrid", description="Classification strategy")

class ClassificationResponse(BaseModel):
    """Response model for classification results."""
    category: TaskCategoryAPI = Field(..., description="Predicted category")
    priority: TaskPriorityAPI = Field(..., description="Predicted priority")
    confidence: float = Field(..., description="Classification confidence")
    strategy_used: str = Field(..., description="Strategy used")
    reasoning: str = Field(..., description="Classification reasoning")
    category_scores: Dict[str, float] = Field(..., description="Category confidence scores")
    priority_scores: Dict[str, float] = Field(..., description="Priority confidence scores")

class AssignmentRequest(BaseModel):
    """Request model for task assignment."""
    task_id: int = Field(..., description="Task ID to assign")
    strategy: str = Field("hybrid", description="Assignment strategy")
    force_reassign: bool = Field(False, description="Force reassignment")

class AssignmentResponse(BaseModel):
    """Response model for assignment results."""
    assigned_team_id: Optional[int] = Field(None, description="Assigned team ID")
    assigned_user_id: Optional[int] = Field(None, description="Assigned user ID")
    confidence: float = Field(..., description="Assignment confidence")
    strategy_used: str = Field(..., description="Strategy used")
    reasoning: str = Field(..., description="Assignment reasoning")
    team_scores: Dict[str, float] = Field(..., description="Team scores")
    factors_considered: List[str] = Field(..., description="Factors considered")

class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    components: Dict[str, Any] = Field(..., description="Component health status")
    version: str = Field(..., description="System version")

class StatisticsResponse(BaseModel):
    """Response model for system statistics."""
    total_tasks: int = Field(..., description="Total tasks in system")
    tasks_by_status: Dict[str, int] = Field(..., description="Tasks grouped by status")
    tasks_by_category: Dict[str, int] = Field(..., description="Tasks grouped by category")
    tasks_by_priority: Dict[str, int] = Field(..., description="Tasks grouped by priority")
    agent_statistics: Dict[str, Any] = Field(..., description="Agent performance statistics")
    system_uptime: float = Field(..., description="System uptime in seconds")
    last_updated: datetime = Field(..., description="Last statistics update")

class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error timestamp")

class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    items: List[Union[TaskResponse, Dict[str, Any]]] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")

class TaskListResponse(PaginatedResponse):
    """Response model for task list."""
    items: List[TaskResponse] = Field(..., description="List of tasks")

class TeamResponse(BaseModel):
    """Response model for team data."""
    id: int = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    category: TaskCategoryAPI = Field(..., description="Team category")
    description: Optional[str] = Field(None, description="Team description")
    skills: List[str] = Field(..., description="Team skills")
    capacity: int = Field(..., description="Team capacity")
    current_load: int = Field(..., description="Current workload")
    availability: int = Field(..., description="Available capacity")
    priority_weight: float = Field(..., description="Priority weight")
    is_active: bool = Field(..., description="Team active status")

class UserResponse(BaseModel):
    """Response model for user data."""
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    team_id: Optional[int] = Field(None, description="Team ID")
    skills: List[str] = Field(..., description="User skills")
    is_active: bool = Field(..., description="User active status")

class WebhookRequest(BaseModel):
    """Request model for webhook notifications."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    active: bool = Field(True, description="Webhook active status")

class WebhookResponse(BaseModel):
    """Response model for webhook data."""
    id: int = Field(..., description="Webhook ID")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed events")
    active: bool = Field(..., description="Webhook active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_triggered: Optional[datetime] = Field(None, description="Last trigger timestamp")
