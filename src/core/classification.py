"""
Enhanced Classification System for the AI-Powered Enterprise Workflow Agent.

This module provides advanced classification capabilities with multiple
classification strategies, confidence scoring, and accuracy tracking.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.agents.classifier_agent import ClassifierAgent
from src.nlp.text_processor import TextProcessor
from src.database.connection import db_manager
from src.database.models import TaskCategory, TaskPriority, Classification
from src.core.exceptions import ClassificationError
from src.utils.logger import get_logger

logger = get_logger("classification_system")

class ClassificationStrategy(Enum):
    """Available classification strategies."""
    LLM_BASED = "llm_based"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    ENSEMBLE = "ensemble"

class ClassificationResult:
    """Structured classification result."""
    
    def __init__(
        self,
        category: TaskCategory,
        priority: TaskPriority,
        confidence: float,
        strategy_used: str,
        reasoning: str,
        category_scores: Optional[Dict[str, float]] = None,
        priority_scores: Optional[Dict[str, float]] = None
    ):
        self.category = category
        self.priority = priority
        self.confidence = confidence
        self.strategy_used = strategy_used
        self.reasoning = reasoning
        self.category_scores = category_scores or {}
        self.priority_scores = priority_scores or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "category": self.category.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "strategy_used": self.strategy_used,
            "reasoning": self.reasoning,
            "category_scores": self.category_scores,
            "priority_scores": self.priority_scores,
            "timestamp": self.timestamp.isoformat()
        }

class EnhancedClassificationSystem:
    """Enhanced classification system with multiple strategies."""
    
    def __init__(self):
        self.classifier_agent = None  # Initialize lazily when needed
        self.text_processor = TextProcessor()
        
        # Enhanced rule-based classification patterns
        self.category_patterns = {
            TaskCategory.IT: [
                # Core IT terms
                "server", "network", "database", "application", "software", "hardware",
                "bug", "error", "crash", "performance", "security", "backup", "deploy",
                "infrastructure", "system", "code", "api", "website", "email", "vpn",
                "firewall", "patch", "update", "install", "configure", "troubleshoot",
                "programming", "development", "technical", "IT", "technology",
                # Additional IT terms
                "outage", "down", "connection", "access", "login", "password", "data",
                "file", "folder", "disk", "memory", "cpu", "bandwidth", "internet",
                "web", "browser", "mobile", "app", "platform", "cloud", "azure", "aws",
                "linux", "windows", "mac", "unix", "sql", "query", "table", "index",
                "script", "automation", "monitoring", "alert", "log", "debug", "fix"
            ],
            TaskCategory.HR: [
                # Core HR terms
                "employee", "staff", "hire", "recruit", "interview", "onboard", "training",
                "payroll", "benefits", "leave", "vacation", "sick", "performance review",
                "promotion", "termination", "resignation", "policy", "compliance",
                "harassment", "diversity", "compensation", "salary", "bonus", "HR",
                "human resources", "personnel", "workforce", "talent",
                # Additional HR terms
                "candidate", "applicant", "job", "position", "role", "team member",
                "manager", "supervisor", "department", "office", "workplace", "safety",
                "incident", "injury", "health", "insurance", "retirement", "401k",
                "pto", "time off", "holiday", "overtime", "schedule", "shift", "work",
                "employment", "contract", "agreement", "evaluation", "feedback"
            ],
            TaskCategory.OPERATIONS: [
                # Core Operations terms
                "process", "workflow", "procedure", "project", "task", "deadline",
                "meeting", "schedule", "planning", "budget", "cost", "vendor",
                "contract", "procurement", "quality", "audit", "compliance",
                "reporting", "analytics", "metrics", "kpi", "improvement",
                "operations", "business", "management", "coordination",
                # Additional Operations terms
                "supplier", "delivery", "shipment", "inventory", "stock", "warehouse",
                "production", "manufacturing", "supply chain", "logistics", "customer",
                "client", "service", "support", "sales", "marketing", "finance",
                "accounting", "invoice", "payment", "revenue", "profit", "loss",
                "strategy", "goal", "objective", "milestone", "timeline", "resource"
            ]
        }
        
        self.priority_patterns = {
            TaskPriority.CRITICAL: [
                "critical", "urgent", "emergency", "asap", "immediately", "crisis",
                "outage", "down", "broken", "failed", "security breach", "data loss",
                "major", "severe", "blocking", "showstopper", "production", "live",
                "business disruption", "revenue loss", "cannot access", "not working",
                "completely", "totally", "all users", "entire system", "halt"
            ],
            TaskPriority.HIGH: [
                "high", "important", "priority", "soon", "quickly", "fast", "escalate",
                "deadline", "time sensitive", "urgent", "needs attention", "significant",
                "affecting", "impact", "multiple users", "team", "department",
                "expires", "renewal", "contract", "client", "customer", "asap"
            ],
            TaskPriority.MEDIUM: [
                "medium", "normal", "standard", "regular", "moderate", "routine",
                "scheduled", "planned", "next week", "end of week", "monthly",
                "quarterly", "review", "update", "improve", "optimize", "analyze"
            ],
            TaskPriority.LOW: [
                "low", "minor", "when possible", "eventually", "nice to have",
                "enhancement", "future", "optional", "convenience", "time permits",
                "no deadline", "no rush", "background", "documentation", "cleanup"
            ]
        }
        
        # Initialize TF-IDF vectorizer for similarity-based classification
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._initialize_reference_vectors()
        
        # Classification accuracy tracking
        self.accuracy_stats = {
            "total_classifications": 0,
            "correct_classifications": 0,
            "accuracy_by_strategy": {},
            "accuracy_by_category": {},
            "accuracy_by_priority": {}
        }
    
    def classify(
        self, 
        text: str, 
        title: str = "", 
        strategy: ClassificationStrategy = ClassificationStrategy.HYBRID,
        **kwargs
    ) -> ClassificationResult:
        """Classify text using the specified strategy."""
        
        if not text or not text.strip():
            raise ClassificationError("Empty text provided for classification")
        
        logger.info(f"Classifying text using {strategy.value} strategy")
        
        try:
            if strategy == ClassificationStrategy.LLM_BASED:
                result = self._classify_llm_based(text, title, **kwargs)
            elif strategy == ClassificationStrategy.RULE_BASED:
                result = self._classify_rule_based(text, title, **kwargs)
            elif strategy == ClassificationStrategy.HYBRID:
                result = self._classify_hybrid(text, title, **kwargs)
            elif strategy == ClassificationStrategy.ENSEMBLE:
                result = self._classify_ensemble(text, title, **kwargs)
            else:
                raise ClassificationError(f"Unknown classification strategy: {strategy}")
            
            # Update accuracy tracking
            self._update_accuracy_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Classification failed with strategy {strategy.value}: {e}")
            raise ClassificationError(f"Classification failed: {e}")
    
    def _classify_llm_based(self, text: str, title: str, **kwargs) -> ClassificationResult:
        """Classify using LLM-based approach."""

        # Initialize classifier agent if not already done
        if self.classifier_agent is None:
            from src.agents.classifier_agent import ClassifierAgent
            self.classifier_agent = ClassifierAgent()

        # Prepare task data for the classifier agent
        task_data = {
            "id": kwargs.get("task_id", 0),
            "title": title,
            "description": text,
            "original_request": text
        }

        # Use the classifier agent
        agent_result = self.classifier_agent.execute(task_data)
        
        if not agent_result.get("success", False):
            raise ClassificationError("LLM classification failed")
        
        data = agent_result["data"]
        
        return ClassificationResult(
            category=TaskCategory(data["category"]),
            priority=TaskPriority(data["priority"]),
            confidence=data["confidence"],
            strategy_used="llm_based",
            reasoning=agent_result.get("reasoning", "LLM-based classification"),
            category_scores=data.get("category_scores", {}),
            priority_scores=data.get("priority_scores", {})
        )
    
    def _classify_rule_based(self, text: str, title: str, **kwargs) -> ClassificationResult:
        """Classify using enhanced rule-based approach."""

        # Combine title and text, giving title more weight
        full_text = f"{title} {title} {text}".lower()  # Title appears twice for emphasis

        # Calculate category scores with weighted matching
        category_scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0
            matches = 0
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in full_text:
                    # Count occurrences and give weight based on pattern importance
                    count = full_text.count(pattern_lower)

                    # Weight based on pattern length (longer patterns are more specific)
                    weight = len(pattern_lower.split()) * 1.5 if len(pattern_lower.split()) > 1 else 1.0

                    # Extra weight for exact matches in title
                    if pattern_lower in title.lower():
                        weight *= 2.0

                    score += count * weight
                    matches += 1

            # Normalize score considering both matches and total patterns
            if patterns:
                # Boost score if many patterns match
                match_ratio = matches / len(patterns)
                normalized_score = (score / len(patterns)) * (1 + match_ratio)
                category_scores[category.value] = min(normalized_score, 1.0)
            else:
                category_scores[category.value] = 0

        # Calculate priority scores with context awareness
        priority_scores = {}
        for priority, patterns in self.priority_patterns.items():
            score = 0
            matches = 0
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if pattern_lower in full_text:
                    count = full_text.count(pattern_lower)

                    # Weight based on pattern importance
                    weight = 1.0
                    if priority == TaskPriority.CRITICAL:
                        weight = 3.0  # Critical patterns get highest weight
                    elif priority == TaskPriority.HIGH:
                        weight = 2.0
                    elif priority == TaskPriority.MEDIUM:
                        weight = 1.0
                    else:  # LOW
                        weight = 0.5

                    # Extra weight for title matches
                    if pattern_lower in title.lower():
                        weight *= 1.5

                    score += count * weight
                    matches += 1

            # Normalize score
            if patterns:
                match_ratio = matches / len(patterns)
                normalized_score = (score / len(patterns)) * (1 + match_ratio * 0.5)
                priority_scores[priority.value] = min(normalized_score, 1.0)
            else:
                priority_scores[priority.value] = 0

        # Determine best category and priority
        best_category = max(category_scores.items(), key=lambda x: x[1])
        best_priority = max(priority_scores.items(), key=lambda x: x[1])

        # Calculate confidence with improved logic
        category_confidence = best_category[1]
        priority_confidence = best_priority[1]

        # Check if there's a clear winner (significant difference from second best)
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        sorted_priorities = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)

        category_margin = 0
        priority_margin = 0

        if len(sorted_categories) > 1:
            category_margin = sorted_categories[0][1] - sorted_categories[1][1]
        if len(sorted_priorities) > 1:
            priority_margin = sorted_priorities[0][1] - sorted_priorities[1][1]

        # Boost confidence if there's a clear winner
        if category_margin > 0.2:
            category_confidence *= 1.2
        if priority_margin > 0.2:
            priority_confidence *= 1.2

        overall_confidence = (category_confidence + priority_confidence) / 2

        # Apply minimum thresholds and defaults
        if overall_confidence < 0.05 or best_category[1] < 0.01:
            # Very low confidence - use defaults based on common patterns
            if any(word in full_text for word in ["server", "system", "application", "software", "network"]):
                category = TaskCategory.IT
            elif any(word in full_text for word in ["employee", "staff", "hire", "payroll", "training"]):
                category = TaskCategory.HR
            else:
                category = TaskCategory.OPERATIONS

            if any(word in full_text for word in ["urgent", "critical", "emergency", "asap", "immediately"]):
                priority = TaskPriority.HIGH
            elif any(word in full_text for word in ["low", "minor", "when possible", "eventually"]):
                priority = TaskPriority.LOW
            else:
                priority = TaskPriority.MEDIUM

            overall_confidence = 0.4
            reasoning = "Default classification with fallback patterns"
        else:
            category = TaskCategory(best_category[0])
            priority = TaskPriority(best_priority[0])
            reasoning = f"Rule-based classification with {category_confidence:.2f} category confidence and {priority_confidence:.2f} priority confidence"

        return ClassificationResult(
            category=category,
            priority=priority,
            confidence=min(overall_confidence, 1.0),
            strategy_used="rule_based",
            reasoning=reasoning,
            category_scores=category_scores,
            priority_scores=priority_scores
        )
    
    def _classify_hybrid(self, text: str, title: str, **kwargs) -> ClassificationResult:
        """Classify using hybrid approach (LLM + rules)."""
        
        try:
            # Get LLM classification
            llm_result = self._classify_llm_based(text, title, **kwargs)
        except Exception as e:
            logger.warning(f"LLM classification failed, falling back to rule-based: {e}")
            return self._classify_rule_based(text, title, **kwargs)
        
        # Get rule-based classification
        rule_result = self._classify_rule_based(text, title, **kwargs)
        
        # Combine results with weighted average
        llm_weight = 0.7
        rule_weight = 0.3
        
        # If both agree, increase confidence
        if (llm_result.category == rule_result.category and 
            llm_result.priority == rule_result.priority):
            
            combined_confidence = min(
                llm_result.confidence * llm_weight + rule_result.confidence * rule_weight + 0.2,
                1.0
            )
            
            return ClassificationResult(
                category=llm_result.category,
                priority=llm_result.priority,
                confidence=combined_confidence,
                strategy_used="hybrid",
                reasoning=f"Hybrid classification with agreement between LLM and rules",
                category_scores=llm_result.category_scores,
                priority_scores=llm_result.priority_scores
            )
        else:
            # If they disagree, use LLM result but with lower confidence
            combined_confidence = llm_result.confidence * 0.8
            
            return ClassificationResult(
                category=llm_result.category,
                priority=llm_result.priority,
                confidence=combined_confidence,
                strategy_used="hybrid",
                reasoning=f"Hybrid classification with LLM preference due to disagreement",
                category_scores=llm_result.category_scores,
                priority_scores=llm_result.priority_scores
            )
    
    def _classify_ensemble(self, text: str, title: str, **kwargs) -> ClassificationResult:
        """Classify using ensemble approach (multiple strategies)."""
        
        results = []
        
        # Try all strategies
        strategies = [ClassificationStrategy.LLM_BASED, ClassificationStrategy.RULE_BASED]
        
        for strategy in strategies:
            try:
                if strategy == ClassificationStrategy.LLM_BASED:
                    result = self._classify_llm_based(text, title, **kwargs)
                elif strategy == ClassificationStrategy.RULE_BASED:
                    result = self._classify_rule_based(text, title, **kwargs)
                
                results.append(result)
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed in ensemble: {e}")
        
        if not results:
            raise ClassificationError("All ensemble strategies failed")
        
        # Voting mechanism
        category_votes = {}
        priority_votes = {}
        total_confidence = 0
        
        for result in results:
            # Weight votes by confidence
            weight = result.confidence
            
            category_votes[result.category] = category_votes.get(result.category, 0) + weight
            priority_votes[result.priority] = priority_votes.get(result.priority, 0) + weight
            total_confidence += weight
        
        # Determine winners
        best_category = max(category_votes.items(), key=lambda x: x[1])[0]
        best_priority = max(priority_votes.items(), key=lambda x: x[1])[0]
        
        # Calculate ensemble confidence
        ensemble_confidence = total_confidence / len(results) if results else 0.5
        
        return ClassificationResult(
            category=best_category,
            priority=best_priority,
            confidence=min(ensemble_confidence, 1.0),
            strategy_used="ensemble",
            reasoning=f"Ensemble classification from {len(results)} strategies",
            category_scores={cat.value: votes for cat, votes in category_votes.items()},
            priority_scores={pri.value: votes for pri, votes in priority_votes.items()}
        )
    
    def _initialize_reference_vectors(self):
        """Initialize reference vectors for similarity-based classification."""
        # This could be enhanced with pre-trained embeddings
        # For now, we'll use the pattern keywords as reference
        reference_texts = []
        
        for category, patterns in self.category_patterns.items():
            reference_text = " ".join(patterns)
            reference_texts.append(reference_text)
        
        if reference_texts:
            try:
                self.reference_vectors = self.vectorizer.fit_transform(reference_texts)
            except Exception as e:
                logger.warning(f"Failed to initialize reference vectors: {e}")
                self.reference_vectors = None
    
    def _update_accuracy_stats(self, result: ClassificationResult):
        """Update accuracy statistics."""
        self.accuracy_stats["total_classifications"] += 1
        
        # Update strategy-specific stats
        strategy = result.strategy_used
        if strategy not in self.accuracy_stats["accuracy_by_strategy"]:
            self.accuracy_stats["accuracy_by_strategy"][strategy] = {
                "total": 0, "correct": 0, "accuracy": 0.0
            }
        
        self.accuracy_stats["accuracy_by_strategy"][strategy]["total"] += 1
    
    def get_accuracy_statistics(self) -> Dict[str, Any]:
        """Get classification accuracy statistics."""
        overall_accuracy = 0.0
        if self.accuracy_stats["total_classifications"] > 0:
            overall_accuracy = (
                self.accuracy_stats["correct_classifications"] / 
                self.accuracy_stats["total_classifications"]
            )
        
        return {
            "overall_accuracy": overall_accuracy,
            "total_classifications": self.accuracy_stats["total_classifications"],
            "accuracy_by_strategy": self.accuracy_stats["accuracy_by_strategy"],
            "accuracy_by_category": self.accuracy_stats["accuracy_by_category"],
            "accuracy_by_priority": self.accuracy_stats["accuracy_by_priority"]
        }
    
    def validate_classification(
        self, 
        result: ClassificationResult, 
        expected_category: TaskCategory, 
        expected_priority: TaskPriority
    ) -> bool:
        """Validate a classification result against expected values."""
        
        is_correct = (
            result.category == expected_category and 
            result.priority == expected_priority
        )
        
        if is_correct:
            self.accuracy_stats["correct_classifications"] += 1
        
        # Update category-specific accuracy
        category_key = expected_category.value
        if category_key not in self.accuracy_stats["accuracy_by_category"]:
            self.accuracy_stats["accuracy_by_category"][category_key] = {
                "total": 0, "correct": 0, "accuracy": 0.0
            }
        
        self.accuracy_stats["accuracy_by_category"][category_key]["total"] += 1
        if result.category == expected_category:
            self.accuracy_stats["accuracy_by_category"][category_key]["correct"] += 1
        
        # Update priority-specific accuracy
        priority_key = expected_priority.value
        if priority_key not in self.accuracy_stats["accuracy_by_priority"]:
            self.accuracy_stats["accuracy_by_priority"][priority_key] = {
                "total": 0, "correct": 0, "accuracy": 0.0
            }
        
        self.accuracy_stats["accuracy_by_priority"][priority_key]["total"] += 1
        if result.priority == expected_priority:
            self.accuracy_stats["accuracy_by_priority"][priority_key]["correct"] += 1
        
        # Recalculate accuracy percentages
        self._recalculate_accuracy_percentages()
        
        return is_correct
    
    def _recalculate_accuracy_percentages(self):
        """Recalculate accuracy percentages for all categories."""
        
        # Strategy accuracy
        for strategy_stats in self.accuracy_stats["accuracy_by_strategy"].values():
            if strategy_stats["total"] > 0:
                strategy_stats["accuracy"] = strategy_stats["correct"] / strategy_stats["total"]
        
        # Category accuracy
        for category_stats in self.accuracy_stats["accuracy_by_category"].values():
            if category_stats["total"] > 0:
                category_stats["accuracy"] = category_stats["correct"] / category_stats["total"]
        
        # Priority accuracy
        for priority_stats in self.accuracy_stats["accuracy_by_priority"].values():
            if priority_stats["total"] > 0:
                priority_stats["accuracy"] = priority_stats["correct"] / priority_stats["total"]

# Global classification system instance
classification_system = EnhancedClassificationSystem()
