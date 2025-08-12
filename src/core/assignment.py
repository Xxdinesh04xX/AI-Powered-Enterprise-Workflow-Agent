"""
Enhanced Assignment Engine for the AI-Powered Enterprise Workflow Agent.

This module provides advanced assignment capabilities with multiple
assignment strategies, skill matching, and workload balancing.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
from datetime import datetime
from dataclasses import dataclass

from src.agents.assignment_agent import AssignmentAgent
from src.database.connection import db_manager
from src.database.models import TaskCategory, TaskPriority, Team, User
from src.database.operations import TeamOperations
from src.core.exceptions import AssignmentError
from src.utils.logger import get_logger

logger = get_logger("assignment_engine")

class AssignmentStrategy(Enum):
    """Available assignment strategies."""
    SKILL_BASED = "skill_based"
    WORKLOAD_BASED = "workload_based"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"
    HYBRID = "hybrid"

@dataclass
class AssignmentResult:
    """Structured assignment result."""
    assigned_team_id: Optional[int]
    assigned_user_id: Optional[int]
    confidence: float
    strategy_used: str
    reasoning: str
    team_scores: Dict[str, float]
    factors_considered: List[str]
    alternative_assignments: List[Dict[str, Any]]

class EnhancedAssignmentEngine:
    """Enhanced assignment engine with multiple strategies."""
    
    def __init__(self):
        self.assignment_agent = None  # Initialize lazily when needed
        
        # Skill mapping for different categories
        self.category_skills = {
            TaskCategory.IT: [
                "programming", "database", "network", "security", "infrastructure",
                "cloud", "devops", "system administration", "troubleshooting",
                "software development", "api", "web development", "mobile"
            ],
            TaskCategory.HR: [
                "recruitment", "onboarding", "payroll", "benefits", "training",
                "performance management", "employee relations", "compliance",
                "policy development", "talent acquisition", "compensation"
            ],
            TaskCategory.OPERATIONS: [
                "project management", "process improvement", "quality assurance",
                "vendor management", "budget planning", "analytics", "reporting",
                "business analysis", "coordination", "logistics", "procurement"
            ]
        }
        
        # Priority weights for assignment
        self.priority_weights = {
            TaskPriority.CRITICAL: 3.0,
            TaskPriority.HIGH: 2.0,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 0.5
        }
        
        # Assignment statistics
        self.stats = {
            "total_assignments": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "assignments_by_strategy": {},
            "assignments_by_category": {},
            "average_confidence": 0.0
        }
    
    def assign_task(
        self,
        task_data: Dict[str, Any],
        strategy: AssignmentStrategy = AssignmentStrategy.HYBRID,
        **kwargs
    ) -> AssignmentResult:
        """Assign a task using the specified strategy."""
        
        if not task_data.get("category"):
            raise AssignmentError("Task category is required for assignment")
        
        logger.info(f"Assigning task {task_data.get('id')} using {strategy.value} strategy")
        
        try:
            # Get available teams
            teams_data = self._get_available_teams(task_data["category"])
            
            if not teams_data:
                raise AssignmentError(f"No available teams found for category: {task_data['category']}")
            
            # Perform assignment based on strategy
            if strategy == AssignmentStrategy.SKILL_BASED:
                result = self._assign_skill_based(task_data, teams_data)
            elif strategy == AssignmentStrategy.WORKLOAD_BASED:
                result = self._assign_workload_based(task_data, teams_data)
            elif strategy == AssignmentStrategy.ROUND_ROBIN:
                result = self._assign_round_robin(task_data, teams_data)
            elif strategy == AssignmentStrategy.PRIORITY_BASED:
                result = self._assign_priority_based(task_data, teams_data)
            elif strategy == AssignmentStrategy.HYBRID:
                result = self._assign_hybrid(task_data, teams_data)
            else:
                raise AssignmentError(f"Unknown assignment strategy: {strategy}")
            
            # Update statistics
            self._update_stats(True, strategy, result.confidence, task_data.get("category"))
            
            logger.info(f"Successfully assigned task {task_data.get('id')} to team {result.assigned_team_id}")
            return result
            
        except Exception as e:
            self._update_stats(False, strategy, 0.0, task_data.get("category"))
            logger.error(f"Assignment failed for task {task_data.get('id')}: {e}")
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
    
    def _assign_skill_based(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> AssignmentResult:
        """Assign task based on skill matching."""
        
        title = task_data.get("title", "").lower()
        description = task_data.get("description", "").lower()
        text = f"{title} {description}"
        
        category = TaskCategory(task_data["category"])
        relevant_skills = self.category_skills.get(category, [])
        
        best_team = None
        best_score = 0.0
        team_scores = {}
        alternatives = []
        
        for team in teams_data:
            if not team["is_active"] or team["availability"] <= 0:
                team_scores[team["name"]] = 0.0
                continue
            
            # Calculate skill match score
            team_skills = [skill.lower() for skill in team.get("skills", [])]
            skill_score = 0.0
            matched_skills = []
            
            # Check for skill matches in task text
            for skill in team_skills:
                if skill in text:
                    skill_score += 2.0  # Direct skill match
                    matched_skills.append(skill)
            
            # Check for relevant category skills
            for skill in relevant_skills:
                if skill.lower() in text and skill.lower() in team_skills:
                    skill_score += 1.5  # Category-relevant skill match
                    if skill not in matched_skills:
                        matched_skills.append(skill)
            
            # Normalize by team skills count
            if team_skills:
                skill_score = skill_score / len(team_skills)
            
            # Factor in availability and priority weight
            availability_factor = team["availability"] / team["capacity"]
            priority_factor = team.get("priority_weight", 1.0)
            
            total_score = skill_score * 0.6 + availability_factor * 0.3 + priority_factor * 0.1
            team_scores[team["name"]] = total_score
            
            # Store alternative
            alternatives.append({
                "team_id": team["id"],
                "team_name": team["name"],
                "score": total_score,
                "matched_skills": matched_skills,
                "reasoning": f"Skill match: {skill_score:.2f}, Availability: {availability_factor:.2f}"
            })
            
            if total_score > best_score:
                best_score = total_score
                best_team = team
        
        if not best_team:
            raise AssignmentError("No suitable team found for skill-based assignment")
        
        # Sort alternatives by score
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        return AssignmentResult(
            assigned_team_id=best_team["id"],
            assigned_user_id=None,
            confidence=min(best_score, 1.0),
            strategy_used="skill_based",
            reasoning=f"Assigned to {best_team['name']} based on skill matching (score: {best_score:.2f})",
            team_scores=team_scores,
            factors_considered=["skill_matching", "team_availability", "priority_weight"],
            alternative_assignments=alternatives[:3]  # Top 3 alternatives
        )
    
    def _assign_workload_based(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> AssignmentResult:
        """Assign task based on workload balancing."""

        priority_str = task_data.get("priority", "Medium")
        # Handle string priority values
        if isinstance(priority_str, str):
            priority_str = priority_str.title()  # Ensure proper case

        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM  # Default fallback

        priority_weight = self.priority_weights.get(priority, 1.0)
        
        # Filter active teams with availability
        available_teams = [t for t in teams_data if t["is_active"] and t["availability"] > 0]
        
        if not available_teams:
            raise AssignmentError("No available teams for workload-based assignment")
        
        best_team = None
        best_score = 0.0
        team_scores = {}
        alternatives = []
        
        for team in available_teams:
            # Calculate workload score (higher availability = higher score)
            availability_ratio = team["availability"] / team["capacity"]
            
            # Adjust for task priority
            adjusted_priority_weight = team.get("priority_weight", 1.0) * priority_weight
            
            # Consider team efficiency (inverse of current load ratio)
            load_ratio = team["current_load"] / team["capacity"] if team["capacity"] > 0 else 1.0
            efficiency_factor = 1.0 - load_ratio
            
            total_score = availability_ratio * 0.5 + adjusted_priority_weight * 0.3 + efficiency_factor * 0.2
            team_scores[team["name"]] = total_score
            
            alternatives.append({
                "team_id": team["id"],
                "team_name": team["name"],
                "score": total_score,
                "reasoning": f"Availability: {availability_ratio:.2f}, Load: {load_ratio:.2f}"
            })
            
            if total_score > best_score:
                best_score = total_score
                best_team = team
        
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        return AssignmentResult(
            assigned_team_id=best_team["id"],
            assigned_user_id=None,
            confidence=0.9,  # High confidence for workload-based assignment
            strategy_used="workload_based",
            reasoning=f"Assigned to {best_team['name']} for optimal workload distribution",
            team_scores=team_scores,
            factors_considered=["workload_balance", "team_capacity", "task_priority", "team_efficiency"],
            alternative_assignments=alternatives[:3]
        )
    
    def _assign_round_robin(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> AssignmentResult:
        """Assign task using round-robin strategy."""
        
        # Filter active teams with availability
        available_teams = [t for t in teams_data if t["is_active"] and t["availability"] > 0]
        
        if not available_teams:
            raise AssignmentError("No available teams for round-robin assignment")
        
        # Sort by current load (ascending) to balance workload
        available_teams.sort(key=lambda t: t["current_load"])
        
        # Select team with lowest current load
        selected_team = available_teams[0]
        
        team_scores = {t["name"]: 1.0 / (t["current_load"] + 1) for t in available_teams}
        
        alternatives = [
            {
                "team_id": team["id"],
                "team_name": team["name"],
                "score": team_scores[team["name"]],
                "reasoning": f"Current load: {team['current_load']}"
            }
            for team in available_teams[:3]
        ]
        
        return AssignmentResult(
            assigned_team_id=selected_team["id"],
            assigned_user_id=None,
            confidence=0.8,  # High confidence for rule-based assignment
            strategy_used="round_robin",
            reasoning=f"Assigned to {selected_team['name']} using round-robin (lowest load: {selected_team['current_load']})",
            team_scores=team_scores,
            factors_considered=["current_workload", "team_availability"],
            alternative_assignments=alternatives
        )
    
    def _assign_priority_based(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> AssignmentResult:
        """Assign task based on priority and team priority weights."""

        priority_str = task_data.get("priority", "Medium")
        # Handle string priority values
        if isinstance(priority_str, str):
            priority_str = priority_str.title()  # Ensure proper case

        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM  # Default fallback

        priority_multiplier = self.priority_weights.get(priority, 1.0)
        
        available_teams = [t for t in teams_data if t["is_active"] and t["availability"] > 0]
        
        if not available_teams:
            raise AssignmentError("No available teams for priority-based assignment")
        
        best_team = None
        best_score = 0.0
        team_scores = {}
        alternatives = []
        
        for team in available_teams:
            # Calculate priority-weighted score
            team_priority_weight = team.get("priority_weight", 1.0)
            availability_factor = team["availability"] / team["capacity"]
            
            # Higher priority tasks go to teams with higher priority weights
            priority_score = team_priority_weight * priority_multiplier
            
            total_score = priority_score * 0.7 + availability_factor * 0.3
            team_scores[team["name"]] = total_score
            
            alternatives.append({
                "team_id": team["id"],
                "team_name": team["name"],
                "score": total_score,
                "reasoning": f"Priority weight: {team_priority_weight}, Task priority: {priority.value}"
            })
            
            if total_score > best_score:
                best_score = total_score
                best_team = team
        
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        
        return AssignmentResult(
            assigned_team_id=best_team["id"],
            assigned_user_id=None,
            confidence=0.85,
            strategy_used="priority_based",
            reasoning=f"Assigned to {best_team['name']} based on priority matching for {priority.value} task",
            team_scores=team_scores,
            factors_considered=["task_priority", "team_priority_weight", "availability"],
            alternative_assignments=alternatives[:3]
        )
    
    def _assign_hybrid(self, task_data: Dict[str, Any], teams_data: List[Dict[str, Any]]) -> AssignmentResult:
        """Assign task using hybrid approach combining multiple strategies."""
        
        # Get results from multiple strategies
        strategies_to_try = [
            AssignmentStrategy.SKILL_BASED,
            AssignmentStrategy.WORKLOAD_BASED,
            AssignmentStrategy.PRIORITY_BASED
        ]
        
        results = []
        for strategy in strategies_to_try:
            try:
                if strategy == AssignmentStrategy.SKILL_BASED:
                    result = self._assign_skill_based(task_data, teams_data)
                elif strategy == AssignmentStrategy.WORKLOAD_BASED:
                    result = self._assign_workload_based(task_data, teams_data)
                elif strategy == AssignmentStrategy.PRIORITY_BASED:
                    result = self._assign_priority_based(task_data, teams_data)
                
                results.append((strategy, result))
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed in hybrid assignment: {e}")
        
        if not results:
            raise AssignmentError("All strategies failed in hybrid assignment")
        
        # Weighted voting based on confidence and strategy importance
        team_votes = {}
        strategy_weights = {
            AssignmentStrategy.SKILL_BASED: 0.4,
            AssignmentStrategy.WORKLOAD_BASED: 0.3,
            AssignmentStrategy.PRIORITY_BASED: 0.3
        }
        
        for strategy, result in results:
            weight = strategy_weights.get(strategy, 0.2) * result.confidence
            team_id = result.assigned_team_id
            
            if team_id not in team_votes:
                team_votes[team_id] = {"score": 0.0, "strategies": [], "team_name": ""}
            
            team_votes[team_id]["score"] += weight
            team_votes[team_id]["strategies"].append(strategy.value)
            
            # Get team name
            for team in teams_data:
                if team["id"] == team_id:
                    team_votes[team_id]["team_name"] = team["name"]
                    break
        
        # Select team with highest vote score
        best_team_id = max(team_votes.items(), key=lambda x: x[1]["score"])[0]
        best_vote = team_votes[best_team_id]
        
        # Calculate hybrid confidence
        total_confidence = sum(result.confidence for _, result in results)
        hybrid_confidence = total_confidence / len(results) if results else 0.5
        
        # Boost confidence if multiple strategies agree
        if len(set(result.assigned_team_id for _, result in results)) == 1:
            hybrid_confidence = min(hybrid_confidence * 1.2, 1.0)
        
        return AssignmentResult(
            assigned_team_id=best_team_id,
            assigned_user_id=None,
            confidence=hybrid_confidence,
            strategy_used="hybrid",
            reasoning=f"Hybrid assignment to {best_vote['team_name']} (strategies: {', '.join(best_vote['strategies'])})",
            team_scores={str(tid): vote["score"] for tid, vote in team_votes.items()},
            factors_considered=["skill_matching", "workload_balance", "priority_alignment", "multi_strategy_consensus"],
            alternative_assignments=[
                {
                    "team_id": tid,
                    "team_name": vote["team_name"],
                    "score": vote["score"],
                    "strategies": vote["strategies"]
                }
                for tid, vote in sorted(team_votes.items(), key=lambda x: x[1]["score"], reverse=True)[:3]
            ]
        )
    
    def _update_stats(self, success: bool, strategy: AssignmentStrategy, confidence: float, category: str):
        """Update assignment statistics."""
        self.stats["total_assignments"] += 1
        
        if success:
            self.stats["successful_assignments"] += 1
        else:
            self.stats["failed_assignments"] += 1
        
        # Update strategy stats
        strategy_key = strategy.value
        if strategy_key not in self.stats["assignments_by_strategy"]:
            self.stats["assignments_by_strategy"][strategy_key] = {"total": 0, "successful": 0}
        
        self.stats["assignments_by_strategy"][strategy_key]["total"] += 1
        if success:
            self.stats["assignments_by_strategy"][strategy_key]["successful"] += 1
        
        # Update category stats
        if category not in self.stats["assignments_by_category"]:
            self.stats["assignments_by_category"][category] = {"total": 0, "successful": 0}
        
        self.stats["assignments_by_category"][category]["total"] += 1
        if success:
            self.stats["assignments_by_category"][category]["successful"] += 1
        
        # Update average confidence
        if success:
            total_confidence = self.stats["average_confidence"] * (self.stats["successful_assignments"] - 1)
            self.stats["average_confidence"] = (total_confidence + confidence) / self.stats["successful_assignments"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get assignment statistics."""
        success_rate = 0.0
        if self.stats["total_assignments"] > 0:
            success_rate = self.stats["successful_assignments"] / self.stats["total_assignments"]
        
        return {
            **self.stats,
            "success_rate": success_rate
        }

# Global assignment engine instance
assignment_engine = EnhancedAssignmentEngine()
