"""
Base agent class for the AI-Powered Enterprise Workflow Agent.

This module provides the base class and common functionality for all
specialized agents in the workflow automation system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import uuid

from src.nlp.llm_client import BaseLLMClient, LLMClientFactory
from src.database.connection import db_manager
from src.database.models import WorkflowExecution
from src.core.exceptions import ProcessingError
from src.utils.logger import get_logger

logger = get_logger("base_agent")

class BaseAgent(ABC):
    """Base class for all workflow agents."""
    
    def __init__(self, agent_name: str, llm_client: Optional[BaseLLMClient] = None):
        self.agent_name = agent_name
        self.llm_client = llm_client or LLMClientFactory.create_client()
        
        # Agent statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "total_tokens_used": 0,
            "total_cost": 0.0
        }
        
        logger.info(f"Initialized {self.agent_name} agent")
    
    @abstractmethod
    def execute(self, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the agent's main functionality."""
        pass
    
    def execute_with_tracking(
        self, 
        task_id: int, 
        task_data: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """Execute agent functionality with performance tracking."""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"{self.agent_name} starting execution {execution_id} for task {task_id}")
        
        try:
            # Record execution start
            with db_manager.get_session() as session:
                execution = WorkflowExecution(
                    task_id=task_id,
                    execution_id=execution_id,
                    agent_name=self.agent_name,
                    step_name=self.get_step_name(),
                    status="running",
                    started_at=datetime.utcnow()
                )
                session.add(execution)
                session.commit()
            
            # Execute the agent
            result = self.execute(task_data, **kwargs)
            
            # Calculate execution metrics
            execution_time = time.time() - start_time
            tokens_used = result.get("tokens_used", 0)
            cost = result.get("cost", 0.0)
            
            # Update execution record
            with db_manager.get_session() as session:
                execution = session.query(WorkflowExecution).filter(
                    WorkflowExecution.execution_id == execution_id
                ).first()
                
                if execution:
                    execution.status = "success"
                    execution.result = result
                    execution.execution_time = execution_time
                    execution.tokens_used = tokens_used
                    execution.cost = cost
                    execution.completed_at = datetime.utcnow()
                    session.commit()
            
            # Update agent statistics
            self._update_stats(True, execution_time, tokens_used, cost)
            
            logger.info(f"{self.agent_name} completed execution {execution_id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            # Update execution record with error
            with db_manager.get_session() as session:
                execution = session.query(WorkflowExecution).filter(
                    WorkflowExecution.execution_id == execution_id
                ).first()
                
                if execution:
                    execution.status = "failure"
                    execution.error_message = error_message
                    execution.execution_time = execution_time
                    execution.completed_at = datetime.utcnow()
                    session.commit()
            
            # Update agent statistics
            self._update_stats(False, execution_time, 0, 0.0)
            
            logger.error(f"{self.agent_name} execution {execution_id} failed: {e}")
            raise ProcessingError(f"{self.agent_name} execution failed: {e}")
    
    @abstractmethod
    def get_step_name(self) -> str:
        """Get the name of the processing step this agent performs."""
        pass
    
    def validate_input(self, task_data: Dict[str, Any]) -> bool:
        """Validate input data for the agent."""
        if not isinstance(task_data, dict):
            raise ProcessingError("Task data must be a dictionary")
        
        if "id" not in task_data:
            raise ProcessingError("Task data must contain an 'id' field")
        
        return True
    
    def create_system_prompt(self) -> str:
        """Create a system prompt for the agent's LLM interactions."""
        return f"""You are a specialized AI agent called {self.agent_name} in an enterprise workflow automation system.
Your role is to {self.get_step_name().lower().replace('_', ' ')} for incoming workflow requests.

You should:
1. Be precise and consistent in your analysis
2. Follow enterprise standards and best practices
3. Provide clear reasoning for your decisions
4. Handle edge cases gracefully
5. Return structured, actionable results

Always maintain professionalism and focus on accuracy."""
    
    def _update_stats(self, success: bool, execution_time: float, tokens_used: int, cost: float):
        """Update agent statistics."""
        self.stats["total_executions"] += 1
        
        if success:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1
        
        # Update average execution time
        total_time = self.stats["average_execution_time"] * (self.stats["total_executions"] - 1)
        self.stats["average_execution_time"] = (total_time + execution_time) / self.stats["total_executions"]
        
        # Update token and cost tracking
        self.stats["total_tokens_used"] += tokens_used
        self.stats["total_cost"] += cost
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        success_rate = 0.0
        if self.stats["total_executions"] > 0:
            success_rate = self.stats["successful_executions"] / self.stats["total_executions"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "agent_name": self.agent_name
        }
    
    def reset_statistics(self):
        """Reset agent statistics."""
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "total_tokens_used": 0,
            "total_cost": 0.0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the agent."""
        try:
            # Test LLM client
            test_response = self.llm_client.generate_completion(
                "Test message for health check",
                system_prompt="Respond with 'OK' if you can process this message."
            )
            
            llm_healthy = "ok" in test_response.lower()
            
            return {
                "agent_name": self.agent_name,
                "status": "healthy" if llm_healthy else "degraded",
                "llm_client": "healthy" if llm_healthy else "unhealthy",
                "statistics": self.get_statistics(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "agent_name": self.agent_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class AgentResult:
    """Standardized result format for agent executions."""
    
    def __init__(
        self,
        success: bool,
        data: Dict[str, Any],
        confidence: float = 1.0,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0,
        cost: float = 0.0
    ):
        self.success = success
        self.data = data
        self.confidence = confidence
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.tokens_used = tokens_used
        self.cost = cost
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "data": self.data,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat()
        }
