"""
Classifier Agent for the AI-Powered Enterprise Workflow Agent.

This agent specializes in classifying tasks into categories (IT, HR, Operations)
and determining priority levels (Critical, High, Medium, Low).
"""

import json
from typing import Dict, Any, Optional, Tuple, List

from src.agents.base_agent import BaseAgent, AgentResult
from src.nlp.llm_client import LLMClientFactory
from src.nlp.text_processor import TextProcessor
from src.database.connection import db_manager
from src.database.models import Task, TaskCategory, TaskPriority
from src.database.operations import TaskOperations, ClassificationOperations
from src.core.exceptions import ProcessingError, ClassificationError
from src.utils.logger import get_logger

logger = get_logger("classifier_agent")

class ClassifierAgent(BaseAgent):
    """Agent responsible for task classification and priority assessment."""
    
    def __init__(self):
        llm_client = LLMClientFactory.create_classification_client()
        super().__init__("ClassifierAgent", llm_client)
        self.text_processor = TextProcessor()
        
        # Classification schema for structured output
        self.classification_schema = {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["IT", "HR", "Operations"],
                    "description": "The primary category this task belongs to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Critical", "High", "Medium", "Low"],
                    "description": "The priority level of this task"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score for the classification"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation for the classification decision"
                },
                "category_scores": {
                    "type": "object",
                    "properties": {
                        "IT": {"type": "number"},
                        "HR": {"type": "number"},
                        "Operations": {"type": "number"}
                    },
                    "description": "Confidence scores for each category"
                },
                "priority_scores": {
                    "type": "object",
                    "properties": {
                        "Critical": {"type": "number"},
                        "High": {"type": "number"},
                        "Medium": {"type": "number"},
                        "Low": {"type": "number"}
                    },
                    "description": "Confidence scores for each priority level"
                },
                "key_indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key words or phrases that influenced the classification"
                }
            },
            "required": ["category", "priority", "confidence", "reasoning"]
        }
    
    def get_step_name(self) -> str:
        """Get the name of the processing step."""
        return "classification"
    
    def execute(self, task_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute task classification."""
        self.validate_input(task_data)
        
        try:
            # Extract task information
            task_id = task_data["id"]
            original_request = task_data.get("original_request", "")
            title = task_data.get("title", "")
            description = task_data.get("description", "")
            
            if not original_request and not description:
                raise ClassificationError("No text content available for classification")
            
            # Use original request if available, otherwise use description
            text_to_classify = original_request or description
            
            logger.info(f"Classifying task {task_id}: {text_to_classify[:100]}...")
            
            # Extract features from text
            features = self.text_processor.extract_features(text_to_classify)
            
            # Perform classification using LLM
            classification_result = self._classify_with_llm(text_to_classify, title, features)
            
            # Validate classification result
            self._validate_classification(classification_result)
            
            # Store classification in database
            self._store_classification(task_id, classification_result)
            
            # Update task with classification
            self._update_task_classification(task_id, classification_result)
            
            # Prepare result
            result = AgentResult(
                success=True,
                data={
                    "task_id": task_id,
                    "category": classification_result["category"],
                    "priority": classification_result["priority"],
                    "confidence": classification_result["confidence"],
                    "category_scores": classification_result.get("category_scores", {}),
                    "priority_scores": classification_result.get("priority_scores", {}),
                    "key_indicators": classification_result.get("key_indicators", [])
                },
                confidence=classification_result["confidence"],
                reasoning=classification_result["reasoning"],
                metadata={
                    "features_extracted": len(features.get("keywords", [])),
                    "text_length": features.get("text_length", 0),
                    "model_used": self.llm_client.model_name
                }
            )
            
            logger.info(f"Successfully classified task {task_id}: {classification_result['category']}/{classification_result['priority']}")
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Classification failed for task {task_data.get('id', 'unknown')}: {e}")
            raise ClassificationError(f"Classification failed: {e}")
    
    def _classify_with_llm(self, text: str, title: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Perform classification using LLM."""
        
        # Create system prompt
        system_prompt = self._create_classification_system_prompt()
        
        # Create user prompt with context
        user_prompt = self._create_classification_user_prompt(text, title, features)
        
        try:
            # Get structured classification from LLM
            result = self.llm_client.generate_structured_output(
                prompt=user_prompt,
                schema=self.classification_schema,
                system_prompt=system_prompt
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            raise ClassificationError(f"LLM classification failed: {e}")
    
    def _create_classification_system_prompt(self) -> str:
        """Create system prompt for classification."""
        return """You are an expert enterprise workflow classifier. Your task is to analyze business requests and classify them into the appropriate category and priority level.

CATEGORIES:
- IT: Technology-related requests including software, hardware, infrastructure, security, applications, databases, networks, and technical support
- HR: Human resources requests including recruitment, employee relations, payroll, benefits, training, performance management, and personnel issues  
- Operations: Business operations including processes, projects, planning, budgets, vendors, quality assurance, reporting, and general business activities

PRIORITY LEVELS:
- Critical: System outages, security breaches, urgent business-critical issues requiring immediate attention
- High: Important issues affecting productivity, time-sensitive requests, escalated matters
- Medium: Standard business requests, routine tasks, moderate impact issues
- Low: Nice-to-have features, minor enhancements, non-urgent requests

Consider:
1. Keywords and domain-specific terminology
2. Urgency indicators and time constraints
3. Business impact and scope
4. Context clues and implied requirements
5. Stakeholder mentions and escalation signals

Be precise, consistent, and provide clear reasoning for your classifications."""
    
    def _create_classification_user_prompt(self, text: str, title: str, features: Dict[str, Any]) -> str:
        """Create user prompt for classification."""
        
        # Extract relevant features
        keywords = features.get("keywords", [])[:10]  # Top 10 keywords
        priority_indicators = features.get("priority_indicators", {})
        category_indicators = features.get("category_indicators", {})
        urgency_signals = features.get("urgency_signals", {})
        
        prompt = f"""Please classify the following enterprise workflow request:

TITLE: {title}

REQUEST TEXT:
{text}

EXTRACTED FEATURES:
- Keywords: {', '.join(keywords)}
- Priority indicators: {priority_indicators}
- Category indicators: {category_indicators}
- Urgency signals: {urgency_signals}
- Text length: {features.get('text_length', 0)} characters
- Word count: {features.get('word_count', 0)} words

Please analyze this request and provide:
1. Primary category (IT, HR, or Operations)
2. Priority level (Critical, High, Medium, or Low)
3. Confidence score (0-1)
4. Clear reasoning for your classification
5. Confidence scores for each category and priority
6. Key indicators that influenced your decision

Focus on accuracy and provide detailed reasoning for your classification decisions."""
        
        return prompt
    
    def _validate_classification(self, result: Dict[str, Any]):
        """Validate classification result."""
        required_fields = ["category", "priority", "confidence", "reasoning"]
        for field in required_fields:
            if field not in result:
                raise ClassificationError(f"Missing required field: {field}")
        
        # Validate category
        if result["category"] not in ["IT", "HR", "Operations"]:
            raise ClassificationError(f"Invalid category: {result['category']}")
        
        # Validate priority
        if result["priority"] not in ["Critical", "High", "Medium", "Low"]:
            raise ClassificationError(f"Invalid priority: {result['priority']}")
        
        # Validate confidence
        confidence = result["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise ClassificationError(f"Invalid confidence score: {confidence}")
    
    def _store_classification(self, task_id: int, result: Dict[str, Any]):
        """Store classification result in database."""
        try:
            with db_manager.get_session() as session:
                ClassificationOperations.create_classification(
                    session=session,
                    task_id=task_id,
                    predicted_category=TaskCategory(result["category"]),
                    predicted_priority=TaskPriority(result["priority"]),
                    confidence_score=result["confidence"],
                    model_name=self.llm_client.model_name,
                    category_scores=result.get("category_scores"),
                    priority_scores=result.get("priority_scores"),
                    model_version="1.0"
                )
                
        except Exception as e:
            logger.error(f"Failed to store classification for task {task_id}: {e}")
            raise ClassificationError(f"Failed to store classification: {e}")
    
    def _update_task_classification(self, task_id: int, result: Dict[str, Any]):
        """Update task with classification results."""
        try:
            with db_manager.get_session() as session:
                TaskOperations.update_task_classification(
                    session=session,
                    task_id=task_id,
                    category=TaskCategory(result["category"]),
                    priority=TaskPriority(result["priority"]),
                    confidence=result["confidence"]
                )
                
        except Exception as e:
            logger.error(f"Failed to update task {task_id} with classification: {e}")
            raise ClassificationError(f"Failed to update task classification: {e}")
    
    def classify_batch(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify multiple tasks in batch."""
        results = []
        
        for task_data in tasks:
            try:
                result = self.execute(task_data)
                results.append(result)
            except Exception as e:
                error_result = {
                    "success": False,
                    "task_id": task_data.get("id"),
                    "error": str(e)
                }
                results.append(error_result)
        
        return results
