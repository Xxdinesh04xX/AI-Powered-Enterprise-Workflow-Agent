"""
Database operations for the AI-Powered Enterprise Workflow Agent.

This module provides high-level database operations and queries
for tasks, classifications, assignments, and reports.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from src.database.models import (
    Task, Classification, Assignment, Team, User, Report, 
    WorkflowExecution, TaskStatus, TaskPriority, TaskCategory
)
from src.database.connection import db_manager
from src.utils.logger import get_logger

logger = get_logger("database_operations")

class TaskOperations:
    """Database operations for tasks."""
    
    @staticmethod
    def create_task(
        session: Session,
        title: str,
        description: str,
        original_request: str,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            original_request=original_request,
            task_metadata=task_metadata or {}
        )
        session.add(task)
        session.flush()  # Get the ID without committing
        logger.info(f"Created task {task.id}: {task.title}")
        return task
    
    @staticmethod
    def get_task_by_id(session: Session, task_id: int) -> Optional[Task]:
        """Get a task by ID."""
        return session.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def get_task_by_uuid(session: Session, task_uuid: str) -> Optional[Task]:
        """Get a task by UUID."""
        return session.query(Task).filter(Task.uuid == task_uuid).first()
    
    @staticmethod
    def get_tasks_by_status(
        session: Session, 
        status: TaskStatus,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Get tasks by status."""
        query = session.query(Task).filter(Task.status == status)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_tasks_by_category(
        session: Session,
        category: TaskCategory,
        limit: Optional[int] = None
    ) -> List[Task]:
        """Get tasks by category."""
        query = session.query(Task).filter(Task.category == category)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_pending_tasks(session: Session, limit: Optional[int] = None) -> List[Task]:
        """Get pending tasks that need processing."""
        query = session.query(Task).filter(Task.status == TaskStatus.PENDING)
        if limit:
            query = query.limit(limit)
        return query.order_by(desc(Task.created_at)).all()
    
    @staticmethod
    def update_task_classification(
        session: Session,
        task_id: int,
        category: TaskCategory,
        priority: TaskPriority,
        confidence: float
    ) -> bool:
        """Update task classification."""
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.category = category
            task.priority = priority
            task.classification_confidence = confidence
            task.updated_at = datetime.utcnow()
            logger.info(f"Updated classification for task {task_id}: {category}/{priority}")
            return True
        return False
    
    @staticmethod
    def update_task_assignment(
        session: Session,
        task_id: int,
        team_id: Optional[int] = None,
        user_id: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> bool:
        """Update task assignment."""
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.assigned_team_id = team_id
            task.assigned_user_id = user_id
            task.assignment_confidence = confidence
            task.updated_at = datetime.utcnow()
            logger.info(f"Updated assignment for task {task_id}: team={team_id}, user={user_id}")
            return True
        return False
    
    @staticmethod
    def update_task_status(
        session: Session,
        task_id: int,
        status: TaskStatus
    ) -> bool:
        """Update task status."""
        task = session.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            task.updated_at = datetime.utcnow()
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
            logger.info(f"Updated status for task {task_id}: {status}")
            return True
        return False

class ClassificationOperations:
    """Database operations for classifications."""
    
    @staticmethod
    def create_classification(
        session: Session,
        task_id: int,
        predicted_category: TaskCategory,
        predicted_priority: TaskPriority,
        confidence_score: float,
        model_name: str,
        category_scores: Optional[Dict[str, float]] = None,
        priority_scores: Optional[Dict[str, float]] = None,
        model_version: Optional[str] = None
    ) -> Classification:
        """Create a new classification record."""
        classification = Classification(
            task_id=task_id,
            predicted_category=predicted_category,
            predicted_priority=predicted_priority,
            confidence_score=confidence_score,
            model_name=model_name,
            model_version=model_version,
            category_scores=category_scores,
            priority_scores=priority_scores
        )
        session.add(classification)
        session.flush()
        logger.info(f"Created classification for task {task_id}: {predicted_category}/{predicted_priority}")
        return classification
    
    @staticmethod
    def get_classifications_by_task(session: Session, task_id: int) -> List[Classification]:
        """Get all classifications for a task."""
        return session.query(Classification).filter(Classification.task_id == task_id).all()

class AssignmentOperations:
    """Database operations for assignments."""
    
    @staticmethod
    def create_assignment(
        session: Session,
        task_id: int,
        team_id: Optional[int],
        user_id: Optional[int],
        confidence_score: float,
        strategy_used: str,
        reasoning: Optional[str] = None
    ) -> Assignment:
        """Create a new assignment record."""
        # Deactivate previous assignments for this task
        session.query(Assignment).filter(
            Assignment.task_id == task_id,
            Assignment.is_active == True
        ).update({"is_active": False})
        
        assignment = Assignment(
            task_id=task_id,
            assigned_team_id=team_id,
            assigned_user_id=user_id,
            confidence_score=confidence_score,
            strategy_used=strategy_used,
            reasoning=reasoning,
            is_active=True
        )
        session.add(assignment)
        session.flush()
        logger.info(f"Created assignment for task {task_id}: team={team_id}, user={user_id}")
        return assignment
    
    @staticmethod
    def get_active_assignment(session: Session, task_id: int) -> Optional[Assignment]:
        """Get the active assignment for a task."""
        return session.query(Assignment).filter(
            Assignment.task_id == task_id,
            Assignment.is_active == True
        ).first()

class TeamOperations:
    """Database operations for teams."""
    
    @staticmethod
    def get_teams_by_category(session: Session, category: TaskCategory) -> List[Team]:
        """Get teams by category."""
        return session.query(Team).filter(
            Team.category == category,
            Team.is_active == True
        ).all()
    
    @staticmethod
    def get_team_workload(session: Session, team_id: int) -> int:
        """Get current workload for a team."""
        return session.query(Task).filter(
            Task.assigned_team_id == team_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).count()
    
    @staticmethod
    def update_team_load(session: Session, team_id: int) -> bool:
        """Update team's current load based on assigned tasks."""
        team = session.query(Team).filter(Team.id == team_id).first()
        if team:
            current_load = TeamOperations.get_team_workload(session, team_id)
            team.current_load = current_load
            return True
        return False

class ReportOperations:
    """Database operations for reports."""
    
    @staticmethod
    def create_report(
        session: Session,
        title: str,
        report_type: str,
        content: Dict[str, Any],
        generated_by: str,
        description: Optional[str] = None,
        summary: Optional[str] = None,
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None
    ) -> Report:
        """Create a new report."""
        report = Report(
            title=title,
            description=description,
            report_type=report_type,
            content=content,
            summary=summary,
            generated_by=generated_by,
            date_range_start=date_range_start,
            date_range_end=date_range_end
        )
        session.add(report)
        session.flush()
        logger.info(f"Created report {report.id}: {report.title}")
        return report
    
    @staticmethod
    def get_reports_by_type(
        session: Session,
        report_type: str,
        limit: Optional[int] = None
    ) -> List[Report]:
        """Get reports by type."""
        query = session.query(Report).filter(Report.report_type == report_type)
        if limit:
            query = query.limit(limit)
        return query.order_by(desc(Report.created_at)).all()

class AnalyticsOperations:
    """Database operations for analytics and metrics."""
    
    @staticmethod
    def get_task_statistics(
        session: Session,
        date_range_start: Optional[datetime] = None,
        date_range_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get task statistics for a date range."""
        query = session.query(Task)
        
        if date_range_start:
            query = query.filter(Task.created_at >= date_range_start)
        if date_range_end:
            query = query.filter(Task.created_at <= date_range_end)
        
        # Total tasks
        total_tasks = query.count()
        
        # Tasks by status
        status_counts = {}
        for status in TaskStatus:
            count = query.filter(Task.status == status).count()
            status_counts[status.value] = count
        
        # Tasks by category
        category_counts = {}
        for category in TaskCategory:
            count = query.filter(Task.category == category).count()
            category_counts[category.value] = count
        
        # Tasks by priority
        priority_counts = {}
        for priority in TaskPriority:
            count = query.filter(Task.priority == priority).count()
            priority_counts[priority.value] = count
        
        return {
            "total_tasks": total_tasks,
            "status_distribution": status_counts,
            "category_distribution": category_counts,
            "priority_distribution": priority_counts
        }
