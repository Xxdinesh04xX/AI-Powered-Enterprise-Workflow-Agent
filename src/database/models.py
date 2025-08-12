"""
Database models for the AI-Powered Enterprise Workflow Agent.

This module defines SQLAlchemy ORM models for tasks, classifications,
assignments, reports, and other entities in the workflow system.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
import uuid

from src.database.connection import Base

# Enums for database fields
class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskCategory(PyEnum):
    IT = "IT"
    HR = "HR"
    OPERATIONS = "Operations"

class UserRole(PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    USER = "user"

class Task(Base):
    """Task model representing workflow tasks."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Task content
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    original_request = Column(Text, nullable=False)  # Original natural language request
    
    # Classification
    category = Column(Enum(TaskCategory), nullable=True, index=True)
    priority = Column(Enum(TaskPriority), nullable=True, index=True)
    classification_confidence = Column(Float, nullable=True)
    
    # Status and workflow
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Assignment
    assigned_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assignment_confidence = Column(Float, nullable=True)
    
    # Metadata
    task_metadata = Column(JSON, nullable=True)  # Additional task metadata
    tags = Column(JSON, nullable=True)  # Task tags for filtering
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assigned_team = relationship("Team", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks")
    classifications = relationship("Classification", back_populates="task")
    assignments = relationship("Assignment", back_populates="task")
    workflow_executions = relationship("WorkflowExecution", back_populates="task")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_category_priority', 'category', 'priority'),
        Index('idx_task_status_created', 'status', 'created_at'),
    )

class Classification(Base):
    """Classification results for tasks."""
    
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Classification results
    predicted_category = Column(Enum(TaskCategory), nullable=False)
    predicted_priority = Column(Enum(TaskPriority), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)
    
    # Classification details
    category_scores = Column(JSON, nullable=True)  # Scores for all categories
    priority_scores = Column(JSON, nullable=True)  # Scores for all priorities
    features_used = Column(JSON, nullable=True)  # Features used for classification
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="classifications")

class Assignment(Base):
    """Assignment results for tasks."""
    
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Assignment results
    assigned_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)
    
    # Assignment strategy
    strategy_used = Column(String(100), nullable=False)  # skill_based, round_robin, etc.
    reasoning = Column(Text, nullable=True)  # Why this assignment was made
    
    # Assignment details
    team_scores = Column(JSON, nullable=True)  # Scores for all teams
    user_scores = Column(JSON, nullable=True)  # Scores for all users
    factors_considered = Column(JSON, nullable=True)  # Factors in assignment decision
    
    # Status
    is_active = Column(Boolean, default=True)  # Whether this assignment is current
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="assignments")
    assigned_team = relationship("Team")
    assigned_user = relationship("User")

class Team(Base):
    """Team model for task assignments."""
    
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(Enum(TaskCategory), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Team capabilities
    skills = Column(JSON, nullable=True)  # List of team skills/capabilities
    capacity = Column(Integer, default=10)  # Maximum concurrent tasks
    current_load = Column(Integer, default=0)  # Current number of assigned tasks
    
    # Team settings
    is_active = Column(Boolean, default=True)
    priority_weight = Column(Float, default=1.0)  # Weight for assignment priority
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="assigned_team")
    users = relationship("User", back_populates="team")

class User(Base):
    """User model for task assignments and system access."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.USER, index=True)
    
    # User assignment info
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    skills = Column(JSON, nullable=True)  # List of user skills
    capacity = Column(Integer, default=5)  # Maximum concurrent tasks
    current_load = Column(Integer, default=0)  # Current number of assigned tasks
    
    # User settings
    is_active = Column(Boolean, default=True)
    notification_preferences = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    team = relationship("Team", back_populates="users")
    tasks = relationship("Task", back_populates="assigned_user")

class Report(Base):
    """Report model for generated reports."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Report metadata
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(100), nullable=False, index=True)  # daily, weekly, monthly, custom
    
    # Report content
    content = Column(JSON, nullable=False)  # Report data in JSON format
    summary = Column(Text, nullable=True)  # Text summary of the report
    
    # Report generation
    generated_by = Column(String(100), nullable=False)  # Agent or user who generated
    generation_time = Column(Float, nullable=True)  # Time taken to generate (seconds)
    
    # Report parameters
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    filters_applied = Column(JSON, nullable=True)  # Filters used in report generation
    
    # File information
    file_path = Column(String(500), nullable=True)  # Path to generated file
    file_format = Column(String(20), nullable=True)  # pdf, html, json, etc.
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_report_type_created', 'report_type', 'created_at'),
    )

class WorkflowExecution(Base):
    """Workflow execution tracking."""
    
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Execution details
    execution_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String(100), nullable=False)  # Which agent executed this
    step_name = Column(String(100), nullable=False)  # Classification, Assignment, etc.
    
    # Execution results
    status = Column(String(50), nullable=False)  # success, failure, partial
    result = Column(JSON, nullable=True)  # Execution result data
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Performance metrics
    execution_time = Column(Float, nullable=True)  # Execution time in seconds
    tokens_used = Column(Integer, nullable=True)  # LLM tokens consumed
    cost = Column(Float, nullable=True)  # Estimated cost
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="workflow_executions")
    
    # Indexes
    __table_args__ = (
        Index('idx_execution_task_step', 'task_id', 'step_name'),
        Index('idx_execution_agent_status', 'agent_name', 'status'),
    )

# Additional utility functions for models
def create_task_from_request(
    original_request: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    task_metadata: Optional[Dict[str, Any]] = None
) -> Task:
    """Create a new task from a natural language request."""
    if not title:
        # Generate title from first 50 characters of request
        title = original_request[:50] + "..." if len(original_request) > 50 else original_request

    if not description:
        description = original_request

    return Task(
        title=title,
        description=description,
        original_request=original_request,
        task_metadata=task_metadata or {}
    )
