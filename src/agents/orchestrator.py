"""
Agent Orchestrator for the AI-Powered Enterprise Workflow Agent.

This module coordinates the execution of multiple agents in the workflow
automation pipeline, managing the flow from classification to assignment to reporting.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.agents.classifier_agent import ClassifierAgent
from src.agents.assignment_agent import AssignmentAgent
from src.agents.reporter_agent import ReporterAgent
from src.database.connection import db_manager
from src.database.models import Task, TaskStatus
from src.database.operations import TaskOperations
from src.core.exceptions import ProcessingError
from src.utils.logger import get_logger

logger = get_logger("agent_orchestrator")

class AgentOrchestrator:
    """Orchestrates the execution of multiple agents in the workflow pipeline."""
    
    def __init__(self):
        self.classifier_agent = ClassifierAgent()
        self.assignment_agent = AssignmentAgent()
        self.reporter_agent = ReporterAgent()
        
        # Execution statistics
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0
        }
        
        logger.info("Agent orchestrator initialized with all agents")
    
    def process_task_workflow(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Process a complete workflow for a single task."""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting workflow processing for task {task_id}")
            
            # Get task data
            task_data = self._get_task_data(task_id)
            
            # Step 1: Classification
            classification_result = self._execute_classification(task_data, **kwargs)
            
            # Update task data with classification results
            task_data.update({
                "category": classification_result["data"]["category"],
                "priority": classification_result["data"]["priority"]
            })
            
            # Step 2: Assignment
            assignment_result = self._execute_assignment(task_data, **kwargs)
            
            # Step 3: Update task status
            self._update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            # Prepare workflow result
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            workflow_result = {
                "success": True,
                "task_id": task_id,
                "execution_time": execution_time,
                "steps": {
                    "classification": classification_result,
                    "assignment": assignment_result
                },
                "final_state": {
                    "category": classification_result["data"]["category"],
                    "priority": classification_result["data"]["priority"],
                    "assigned_team_id": assignment_result["data"]["assigned_team_id"],
                    "assigned_user_id": assignment_result["data"]["assigned_user_id"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update statistics
            self._update_stats(True, execution_time)
            
            logger.info(f"Successfully completed workflow for task {task_id} in {execution_time:.2f}s")
            return workflow_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_stats(False, execution_time)
            
            logger.error(f"Workflow processing failed for task {task_id}: {e}")
            
            # Return error result
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def process_batch_workflow(self, task_ids: List[int], **kwargs) -> List[Dict[str, Any]]:
        """Process workflows for multiple tasks."""
        logger.info(f"Starting batch workflow processing for {len(task_ids)} tasks")
        
        results = []
        
        # Process tasks sequentially for now
        # Can be enhanced with parallel processing
        for task_id in task_ids:
            try:
                result = self.process_task_workflow(task_id, **kwargs)
                results.append(result)
            except Exception as e:
                error_result = {
                    "success": False,
                    "task_id": task_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                results.append(error_result)
        
        successful_count = len([r for r in results if r.get("success", False)])
        logger.info(f"Completed batch processing: {successful_count}/{len(task_ids)} successful")
        
        return results
    
    def process_pending_tasks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process all pending tasks in the system."""
        try:
            # Get pending tasks
            with db_manager.get_session() as session:
                pending_tasks = TaskOperations.get_pending_tasks(session, limit)
            
            if not pending_tasks:
                logger.info("No pending tasks found")
                return []
            
            task_ids = [task.id for task in pending_tasks]
            logger.info(f"Found {len(task_ids)} pending tasks to process")
            
            # Process all pending tasks
            return self.process_batch_workflow(task_ids)
            
        except Exception as e:
            logger.error(f"Failed to process pending tasks: {e}")
            raise ProcessingError(f"Failed to process pending tasks: {e}")
    
    def generate_report(self, report_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report using the reporter agent."""
        try:
            logger.info(f"Generating report: {report_request.get('type', 'unknown')}")
            
            result = self.reporter_agent.execute(report_request)
            
            logger.info(f"Successfully generated report: {result['data']['report_id']}")
            return result
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ProcessingError(f"Report generation failed: {e}")
    
    def _get_task_data(self, task_id: int) -> Dict[str, Any]:
        """Get task data for processing."""
        try:
            with db_manager.get_session() as session:
                task = TaskOperations.get_task_by_id(session, task_id)
                
                if not task:
                    raise ProcessingError(f"Task {task_id} not found")
                
                return {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "original_request": task.original_request,
                    "category": task.category.value if task.category else None,
                    "priority": task.priority.value if task.priority else None,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get task data for task {task_id}: {e}")
            raise ProcessingError(f"Failed to get task data: {e}")
    
    def _execute_classification(self, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute classification step."""
        try:
            return self.classifier_agent.execute_with_tracking(
                task_id=task_data["id"],
                task_data=task_data,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Classification failed for task {task_data['id']}: {e}")
            raise ProcessingError(f"Classification failed: {e}")
    
    def _execute_assignment(self, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute assignment step."""
        try:
            return self.assignment_agent.execute_with_tracking(
                task_id=task_data["id"],
                task_data=task_data,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Assignment failed for task {task_data['id']}: {e}")
            raise ProcessingError(f"Assignment failed: {e}")
    
    def _update_task_status(self, task_id: int, status: TaskStatus):
        """Update task status."""
        try:
            with db_manager.get_session() as session:
                TaskOperations.update_task_status(session, task_id, status)
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status to {status}: {e}")
            # Don't raise exception as this is not critical for workflow
    
    def _update_stats(self, success: bool, execution_time: float):
        """Update orchestrator statistics."""
        self.stats["total_workflows"] += 1
        
        if success:
            self.stats["successful_workflows"] += 1
        else:
            self.stats["failed_workflows"] += 1
        
        # Update average execution time
        total_time = self.stats["average_execution_time"] * (self.stats["total_workflows"] - 1)
        self.stats["average_execution_time"] = (total_time + execution_time) / self.stats["total_workflows"]
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        return {
            "orchestrator": self.get_statistics(),
            "classifier": self.classifier_agent.get_statistics(),
            "assignment": self.assignment_agent.get_statistics(),
            "reporter": self.reporter_agent.get_statistics()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        success_rate = 0.0
        if self.stats["total_workflows"] > 0:
            success_rate = self.stats["successful_workflows"] / self.stats["total_workflows"]
        
        return {
            **self.stats,
            "success_rate": success_rate
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        return {
            "orchestrator": {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            },
            "agents": {
                "classifier": self.classifier_agent.health_check(),
                "assignment": self.assignment_agent.health_check(),
                "reporter": self.reporter_agent.health_check()
            }
        }
    
    def reset_statistics(self):
        """Reset all statistics."""
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0
        }
        
        self.classifier_agent.reset_statistics()
        self.assignment_agent.reset_statistics()
        self.reporter_agent.reset_statistics()

# Global orchestrator instance
orchestrator = AgentOrchestrator()
