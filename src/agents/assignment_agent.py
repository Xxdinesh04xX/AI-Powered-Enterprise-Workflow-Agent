"""
Assignment Agent for the AI-Powered Enterprise Workflow Agent.

This agent specializes in assigning tasks to appropriate teams and users
based on category, priority, workload, and skill matching.
"""

import json
from typing import Dict, Any, Optional, List, Tuple

from src.agents.base_agent import BaseAgent, AgentResult
from src.nlp.llm_client import LLMClientFactory
from src.database.connection import db_manager
from src.database.models import Task, Team, User, TaskCategory
from src.database.operations import TaskOperations, AssignmentOperations, TeamOperations
from src.core.exceptions import ProcessingError, AssignmentError
from src.core.config import config
from src.utils.logger import get_logger

logger = get_logger("assignment_agent")

class AssignmentAgent(BaseAgent):
    """Agent responsible for task assignment to teams and users."""
    
    def __init__(self):
        llm_client = LLMClientFactory.create_assignment_client()
        super().__init__("AssignmentAgent", llm_client)
        
        # Assignment schema for structured output
        self.assignment_schema = {
            "type": "object",
            "properties": {
                "assigned_team_id": {
                    "type": ["integer", "null"],
                    "description": "ID of the team to assign the task to"
                },
                "assigned_user_id": {
                    "type": ["integer", "null"],
                    "description": "ID of the user to assign the task to"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score for the assignment"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation for the assignment decision"
                },
                "team_scores": {
                    "type": "object",
                    "description": "Confidence scores for each considered team"
                },
                "factors_considered": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors that influenced the assignment decision"
                },
                "alternative_assignments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "team_id": {"type": "integer"},
                            "user_id": {"type": ["integer", "null"]},
                            "score": {"type": "number"},
                            "reason": {"type": "string"}
                        }
                    },
                    "description": "Alternative assignment options considered"
                }
            },
            "required": ["confidence", "reasoning"]
        }
    
    def get_step_name(self) -> str:
        """Get the name of the processing step."""
        return "assignment"
    
    def execute(self, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute task assignment."""
        self.validate_input(task_data)
        
        try:
            # Extract task information
            task_id = task_data["id"]
            category = task_data.get("category")
            priority = task_data.get("priority")
            title = task_data.get("title", "")
            description = task_data.get("description", "")
            
            if not category:
                raise AssignmentError("Task category is required for assignment")
            
            logger.info(f"Assigning task {task_id} (Category: {category}, Priority: {priority})")
            
            # Get available teams and users
            teams_data = self._get_available_teams(category)
            
            if not teams_data:
                raise AssignmentError(f"No available teams found for category: {category}")
            
            # Determine assignment strategy
            strategy = kwargs.get("strategy", config.assignment.strategy)
            
            # Perform assignment based on strategy
            if strategy == "skill_based":
                assignment_result = self._assign_skill_based(task_data, teams_data)
            elif strategy == "round_robin":
                assignment_result = self._assign_round_robin(task_data, teams_data)
            elif strategy == "workload_based":
                assignment_result = self._assign_workload_based(task_data, teams_data)
            else:
                # Use LLM-based intelligent assignment
                assignment_result = self._assign_with_llm(task_data, teams_data)
            
            # Validate assignment result
            self._validate_assignment(assignment_result, teams_data)
            
            # Store assignment in database
            self._store_assignment(task_id, assignment_result, strategy)
            
            # Update task with assignment
            self._update_task_assignment(task_id, assignment_result)
            
            # Update team workload
            if assignment_result.get("assigned_team_id"):
                self._update_team_workload(assignment_result["assigned_team_id"])
            
            # Prepare result
            result = AgentResult(
                success=True,
                data={
                    "task_id": task_id,
                    "assigned_team_id": assignment_result.get("assigned_team_id"),
                    "assigned_user_id": assignment_result.get("assigned_user_id"),
                    "confidence": assignment_result["confidence"],
                    "strategy_used": strategy,
                    "team_scores": assignment_result.get("team_scores", {}),
                    "factors_considered": assignment_result.get("factors_considered", [])
                },
                confidence=assignment_result["confidence"],
                reasoning=assignment_result["reasoning"],
                metadata={
                    "teams_considered": len(teams_data),
                    "strategy_used": strategy,
                    "model_used": self.llm_client.model_name if strategy not in ["round_robin", "workload_based"] else "rule_based"
                }
            )
            
            logger.info(f"Successfully assigned task {task_id} to team {assignment_result.get('assigned_team_id')}")
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Assignment failed for task {task_data.get('id', 'unknown')}: {e}")
            raise AssignmentError(f"Assignment failed: {e}")
    
    def _get_available_teams(self, category: str) -> List[Dict[str, Any]]:
        """Get available teams for the given category."""
        try:
            with db_manager.get_session() as session:
                teams = TeamOperations.get_teams_by_category(session, TaskCategory(category))
                
                teams_data = []
                for team in teams:
                    # Get current workload
                    current_load = TeamOperations.get_team_workload(session, team.id)
                    
                    team_data = {
                        "id": team.id,
                        "name": team.name,
                        "category": team.category.value,
                        "description": team.description,
                        "skills": team.skills or [],
                        "capacity": team.capacity,
                        "current_load": current_load,
                        "availability": max(0, team.capacity - current_load),
                        "priority_weight": team.priority_weight,
                        "is_active": team.is_active
                    }
                    teams_data.append(team_data)
                
                return teams_data
                
        except Exception as e:
            logger.error(f"Failed to get available teams for category {category}: {e}")
            raise AssignmentError(f"Failed to get available teams: {e}")
    
    def _assign_skill_based(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign task based on skill matching."""
        title = task_data.get("title", "")
        description = task_data.get("description", "")
        text = f"{title} {description}".lower()
        
        best_team = None
        best_score = 0.0
        team_scores = {}
        
        for team in teams_data:
            if not team["is_active"] or team["availability"] <= 0:
                team_scores[team["name"]] = 0.0
                continue
            
            # Calculate skill match score
            skills = team.get("skills", [])
            skill_score = 0.0
            
            for skill in skills:
                if skill.lower() in text:
                    skill_score += 1.0
            
            # Normalize by number of skills
            if skills:
                skill_score = skill_score / len(skills)
            
            # Factor in availability and priority weight
            availability_factor = team["availability"] / team["capacity"]
            priority_factor = team.get("priority_weight", 1.0)
            
            total_score = skill_score * 0.6 + availability_factor * 0.3 + priority_factor * 0.1
            team_scores[team["name"]] = total_score
            
            if total_score > best_score:
                best_score = total_score
                best_team = team
        
        if not best_team:
            raise AssignmentError("No suitable team found for assignment")
        
        return {
            "assigned_team_id": best_team["id"],
            "assigned_user_id": None,  # Could be enhanced to assign specific users
            "confidence": min(best_score, 1.0),
            "reasoning": f"Assigned to {best_team['name']} based on skill matching and availability",
            "team_scores": team_scores,
            "factors_considered": ["skill_matching", "team_availability", "priority_weight"]
        }
    
    def _assign_round_robin(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign task using round-robin strategy."""
        # Filter active teams with availability
        available_teams = [t for t in teams_data if t["is_active"] and t["availability"] > 0]
        
        if not available_teams:
            raise AssignmentError("No available teams for round-robin assignment")
        
        # Sort by current load (ascending) to balance workload
        available_teams.sort(key=lambda t: t["current_load"])
        
        # Select team with lowest current load
        selected_team = available_teams[0]
        
        return {
            "assigned_team_id": selected_team["id"],
            "assigned_user_id": None,
            "confidence": 0.8,  # High confidence for rule-based assignment
            "reasoning": f"Assigned to {selected_team['name']} using round-robin strategy (lowest current load)",
            "team_scores": {t["name"]: 1.0 / (t["current_load"] + 1) for t in available_teams},
            "factors_considered": ["current_workload", "team_availability"]
        }
    
    def _assign_workload_based(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign task based on workload balancing."""
        priority = task_data.get("priority", "Medium")
        
        # Filter active teams with availability
        available_teams = [t for t in teams_data if t["is_active"] and t["availability"] > 0]
        
        if not available_teams:
            raise AssignmentError("No available teams for workload-based assignment")
        
        best_team = None
        best_score = 0.0
        team_scores = {}
        
        for team in available_teams:
            # Calculate workload score (higher availability = higher score)
            availability_ratio = team["availability"] / team["capacity"]
            
            # Priority weight factor
            priority_factor = team.get("priority_weight", 1.0)
            
            # Adjust for task priority
            if priority == "Critical":
                priority_factor *= 1.5
            elif priority == "High":
                priority_factor *= 1.2
            elif priority == "Low":
                priority_factor *= 0.8
            
            total_score = availability_ratio * priority_factor
            team_scores[team["name"]] = total_score
            
            if total_score > best_score:
                best_score = total_score
                best_team = team
        
        return {
            "assigned_team_id": best_team["id"],
            "assigned_user_id": None,
            "confidence": 0.9,  # High confidence for workload-based assignment
            "reasoning": f"Assigned to {best_team['name']} based on workload balancing and priority",
            "team_scores": team_scores,
            "factors_considered": ["workload_balance", "team_capacity", "task_priority"]
        }
    
    def _assign_with_llm(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assign task using LLM-based intelligent assignment."""
        
        # Create system prompt
        system_prompt = self._create_assignment_system_prompt()
        
        # Create user prompt with context
        user_prompt = self._create_assignment_user_prompt(task_data, teams_data)
        
        try:
            # Get structured assignment from LLM
            result = self.llm_client.generate_structured_output(
                prompt=user_prompt,
                schema=self.assignment_schema,
                system_prompt=system_prompt
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM assignment failed: {e}")
            # Fallback to workload-based assignment
            logger.info("Falling back to workload-based assignment")
            return self._assign_workload_based(task_data, teams_data)

    def _create_assignment_system_prompt(self) -> str:
        """Create system prompt for assignment."""
        return """You are an expert enterprise task assignment specialist. Your role is to analyze tasks and assign them to the most appropriate teams based on multiple factors.

Consider these factors when making assignments:
1. Team expertise and skills relevant to the task
2. Current workload and capacity of teams
3. Task priority and urgency
4. Team availability and active status
5. Historical performance and specialization

Assignment Principles:
- Match tasks to teams with relevant skills and experience
- Balance workload across teams to prevent overload
- Prioritize critical and high-priority tasks appropriately
- Consider team capacity and current assignments
- Provide clear reasoning for assignment decisions

Be strategic in your assignments to optimize both task completion and team utilization."""

    def _create_assignment_user_prompt(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> str:
        """Create user prompt for assignment."""

        task_info = f"""TASK TO ASSIGN:
ID: {task_data.get('id')}
Title: {task_data.get('title', '')}
Description: {task_data.get('description', '')}
Category: {task_data.get('category', '')}
Priority: {task_data.get('priority', '')}
"""

        teams_info = "AVAILABLE TEAMS:\n"
        for team in teams_data:
            teams_info += f"""
Team ID: {team['id']}
Name: {team['name']}
Category: {team['category']}
Description: {team.get('description', '')}
Skills: {', '.join(team.get('skills', []))}
Capacity: {team['capacity']}
Current Load: {team['current_load']}
Availability: {team['availability']}
Active: {team['is_active']}
Priority Weight: {team.get('priority_weight', 1.0)}
"""

        prompt = f"""{task_info}

{teams_info}

Please analyze this task and assign it to the most appropriate team. Consider:
1. Which team has the most relevant skills for this task?
2. Which teams have available capacity?
3. How does the task priority affect the assignment?
4. What are the trade-offs between different assignment options?

Provide your assignment decision with confidence score and detailed reasoning."""

        return prompt

    def _validate_assignment(self, result: Dict[str, Any], teams_data: List[Dict[str, Any]]):
        """Validate assignment result."""
        if "confidence" not in result:
            raise AssignmentError("Missing confidence score in assignment result")

        if "reasoning" not in result:
            raise AssignmentError("Missing reasoning in assignment result")

        confidence = result["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise AssignmentError(f"Invalid confidence score: {confidence}")

        # Validate team assignment
        assigned_team_id = result.get("assigned_team_id")
        if assigned_team_id is not None:
            team_ids = [team["id"] for team in teams_data]
            if assigned_team_id not in team_ids:
                raise AssignmentError(f"Invalid team ID: {assigned_team_id}")

    def _store_assignment(self, task_id: int, result: Dict[str, Any], strategy: str):
        """Store assignment result in database."""
        try:
            with db_manager.get_session() as session:
                AssignmentOperations.create_assignment(
                    session=session,
                    task_id=task_id,
                    team_id=result.get("assigned_team_id"),
                    user_id=result.get("assigned_user_id"),
                    confidence_score=result["confidence"],
                    strategy_used=strategy,
                    reasoning=result["reasoning"]
                )

        except Exception as e:
            logger.error(f"Failed to store assignment for task {task_id}: {e}")
            raise AssignmentError(f"Failed to store assignment: {e}")

    def _update_task_assignment(self, task_id: int, result: Dict[str, Any]):
        """Update task with assignment results."""
        try:
            with db_manager.get_session() as session:
                TaskOperations.update_task_assignment(
                    session=session,
                    task_id=task_id,
                    team_id=result.get("assigned_team_id"),
                    user_id=result.get("assigned_user_id"),
                    confidence=result["confidence"]
                )

        except Exception as e:
            logger.error(f"Failed to update task {task_id} with assignment: {e}")
            raise AssignmentError(f"Failed to update task assignment: {e}")

    def _update_team_workload(self, team_id: int):
        """Update team's current workload."""
        try:
            with db_manager.get_session() as session:
                TeamOperations.update_team_load(session, team_id)

        except Exception as e:
            logger.error(f"Failed to update workload for team {team_id}: {e}")
            # Don't raise exception as this is not critical

    def assign_batch(self, tasks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Assign multiple tasks in batch."""
        results = []

        for task_data in tasks:
            try:
                result = self.execute(task_data, **kwargs)
                results.append(result)
            except Exception as e:
                error_result = {
                    "success": False,
                    "task_id": task_data.get("id"),
                    "error": str(e)
                }
                results.append(error_result)

        return results
