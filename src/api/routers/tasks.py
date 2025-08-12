"""
Tasks API router for the AI-Powered Enterprise Workflow Agent.

This module provides REST API endpoints for task management
including CRUD operations, classification, and assignment.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.models import *
from src.api.dependencies import (
    get_db_session, require_authentication, require_permission,
    get_pagination_params, get_filter_params, get_sort_params,
    check_rate_limit, validate_task_access, get_request_context
)
from src.database.models import Task, TaskStatus, TaskCategory, TaskPriority
from src.database.operations import TaskOperations
from src.core.classification import classification_system
from src.core.assignment import assignment_engine
from src.utils.logger import get_logger

logger = get_logger("api_tasks")

router = APIRouter()

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    pagination: dict = Depends(get_pagination_params),
    filters: dict = Depends(get_filter_params),
    sort: dict = Depends(get_sort_params),
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_authentication),
    _rate_limit: None = Depends(check_rate_limit)
):
    """List tasks with pagination, filtering, and sorting."""
    
    try:
        # Build query
        query = db_session.query(Task)
        
        # Apply filters
        if filters.get("status"):
            query = query.filter(Task.status == TaskStatus(filters["status"]))
        if filters.get("category"):
            query = query.filter(Task.category == TaskCategory(filters["category"]))
        if filters.get("priority"):
            query = query.filter(Task.priority == TaskPriority(filters["priority"]))
        if filters.get("assigned_team_id"):
            query = query.filter(Task.assigned_team_id == filters["assigned_team_id"])
        if filters.get("created_after"):
            query = query.filter(Task.created_at >= filters["created_after"])
        if filters.get("created_before"):
            query = query.filter(Task.created_at <= filters["created_before"])
        
        # Apply sorting
        sort_field = getattr(Task, sort["sort_by"], Task.created_at)
        if sort["sort_order"] == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        tasks = query.offset(pagination["offset"]).limit(pagination["per_page"]).all()
        
        # Convert to response models
        task_responses = []
        for task in tasks:
            task_responses.append(TaskResponse(
                id=task.id,
                uuid=task.uuid,
                title=task.title,
                description=task.description,
                original_request=task.original_request,
                status=TaskStatusAPI(task.status.value),
                category=TaskCategoryAPI(task.category.value) if task.category else None,
                priority=TaskPriorityAPI(task.priority.value) if task.priority else None,
                assigned_team_id=task.assigned_team_id,
                assigned_user_id=task.assigned_user_id,
                classification_confidence=task.classification_confidence,
                assignment_confidence=task.assignment_confidence,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                metadata=task.metadata
            ))
        
        # Calculate pagination info
        pages = (total + pagination["per_page"] - 1) // pagination["per_page"]
        has_next = pagination["page"] < pages
        has_prev = pagination["page"] > 1
        
        return TaskListResponse(
            items=task_responses,
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_permission("write")),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Create a new task."""
    
    try:
        # Create task in database
        task = TaskOperations.create_task(
            session=db_session,
            title=task_request.title,
            description=task_request.description,
            original_request=task_request.original_request,
            category=TaskCategory(task_request.category.value) if task_request.category else None,
            priority=TaskPriority(task_request.priority.value) if task_request.priority else None,
            metadata=task_request.metadata
        )
        
        # Schedule background classification and assignment if not provided
        if not task_request.category or not task_request.priority:
            background_tasks.add_task(classify_and_assign_task, task.id)
        
        logger.info(f"Created task {task.id}: {task.title}")
        
        return TaskResponse(
            id=task.id,
            uuid=task.uuid,
            title=task.title,
            description=task.description,
            original_request=task.original_request,
            status=TaskStatusAPI(task.status.value),
            category=TaskCategoryAPI(task.category.value) if task.category else None,
            priority=TaskPriorityAPI(task.priority.value) if task.priority else None,
            assigned_team_id=task.assigned_team_id,
            assigned_user_id=task.assigned_user_id,
            classification_confidence=task.classification_confidence,
            assignment_confidence=task.assignment_confidence,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            metadata=task.metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_authentication),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get a specific task by ID."""
    
    try:
        task = db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=task.id,
            uuid=task.uuid,
            title=task.title,
            description=task.description,
            original_request=task.original_request,
            status=TaskStatusAPI(task.status.value),
            category=TaskCategoryAPI(task.category.value) if task.category else None,
            priority=TaskPriorityAPI(task.priority.value) if task.priority else None,
            assigned_team_id=task.assigned_team_id,
            assigned_user_id=task.assigned_user_id,
            classification_confidence=task.classification_confidence,
            assignment_confidence=task.assignment_confidence,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            metadata=task.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task")

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdateRequest,
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_permission("write")),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Update a specific task."""
    
    try:
        task = db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update fields
        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        if task_update.status is not None:
            task.status = TaskStatus(task_update.status.value)
            if task_update.status == TaskStatusAPI.COMPLETED:
                task.completed_at = datetime.utcnow()
        if task_update.category is not None:
            task.category = TaskCategory(task_update.category.value)
        if task_update.priority is not None:
            task.priority = TaskPriority(task_update.priority.value)
        if task_update.metadata is not None:
            task.metadata = task_update.metadata
        
        task.updated_at = datetime.utcnow()
        db_session.commit()
        
        logger.info(f"Updated task {task.id}")
        
        return TaskResponse(
            id=task.id,
            uuid=task.uuid,
            title=task.title,
            description=task.description,
            original_request=task.original_request,
            status=TaskStatusAPI(task.status.value),
            category=TaskCategoryAPI(task.category.value) if task.category else None,
            priority=TaskPriorityAPI(task.priority.value) if task.priority else None,
            assigned_team_id=task.assigned_team_id,
            assigned_user_id=task.assigned_user_id,
            classification_confidence=task.classification_confidence,
            assignment_confidence=task.assignment_confidence,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            metadata=task.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_permission("write")),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Delete a specific task."""
    
    try:
        task = db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        db_session.delete(task)
        db_session.commit()
        
        logger.info(f"Deleted task {task_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/classify", response_model=ClassificationResponse)
async def classify_task(
    classification_request: ClassificationRequest,
    current_user: dict = Depends(require_authentication),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Classify a task to determine category and priority."""
    
    try:
        # Prepare task data for classification
        task_data = {
            "title": classification_request.title or "",
            "description": classification_request.text,
            "original_request": classification_request.text
        }
        
        # Perform classification
        result = classification_system.classify_task(
            task_data,
            strategy=classification_request.strategy
        )
        
        return ClassificationResponse(
            category=TaskCategoryAPI(result.category),
            priority=TaskPriorityAPI(result.priority),
            confidence=result.confidence,
            strategy_used=result.strategy_used,
            reasoning=result.reasoning,
            category_scores=result.category_scores,
            priority_scores=result.priority_scores
        )
        
    except Exception as e:
        logger.error(f"Failed to classify task: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify task")

@router.post("/{task_id}/assign", response_model=AssignmentResponse)
async def assign_task(
    task_id: int,
    assignment_request: AssignmentRequest,
    db_session: Session = Depends(get_db_session),
    current_user: dict = Depends(require_permission("write")),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Assign a task to a team."""
    
    try:
        task = db_session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Prepare task data for assignment
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category.value if task.category else "IT",
            "priority": task.priority.value if task.priority else "Medium"
        }
        
        # Perform assignment
        result = assignment_engine.assign_task(
            task_data,
            strategy=assignment_request.strategy
        )
        
        # Update task with assignment
        if result.assigned_team_id:
            task.assigned_team_id = result.assigned_team_id
            task.assignment_confidence = result.confidence
            task.updated_at = datetime.utcnow()
            db_session.commit()
        
        return AssignmentResponse(
            assigned_team_id=result.assigned_team_id,
            assigned_user_id=result.assigned_user_id,
            confidence=result.confidence,
            strategy_used=result.strategy_used,
            reasoning=result.reasoning,
            team_scores=result.team_scores,
            factors_considered=result.factors_considered
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign task")

# Background task functions
async def classify_and_assign_task(task_id: int):
    """Background task to classify and assign a task."""
    try:
        from src.database.connection import db_manager
        
        with db_manager.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found for background processing")
                return
            
            # Classify if needed
            if not task.category or not task.priority:
                task_data = {
                    "title": task.title,
                    "description": task.description,
                    "original_request": task.original_request
                }
                
                classification_result = classification_system.classify_task(task_data)
                task.category = TaskCategory(classification_result.category)
                task.priority = TaskPriority(classification_result.priority)
                task.classification_confidence = classification_result.confidence
            
            # Assign if not already assigned
            if not task.assigned_team_id:
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "category": task.category.value,
                    "priority": task.priority.value
                }
                
                assignment_result = assignment_engine.assign_task(task_data)
                if assignment_result.assigned_team_id:
                    task.assigned_team_id = assignment_result.assigned_team_id
                    task.assignment_confidence = assignment_result.confidence
            
            task.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Background processing completed for task {task_id}")
            
    except Exception as e:
        logger.error(f"Background processing failed for task {task_id}: {e}")
