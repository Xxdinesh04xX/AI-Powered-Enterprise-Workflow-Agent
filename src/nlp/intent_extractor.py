"""
Intent extraction for the AI-Powered Enterprise Workflow Agent.

This module extracts intent, actions, and structured information from
natural language requests using LLM-based processing.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.nlp.llm_client import LLMClientFactory
from src.nlp.text_processor import TextProcessor
from src.core.exceptions import ProcessingError
from src.utils.logger import get_logger

logger = get_logger("intent_extractor")

class IntentType(Enum):
    """Types of intents that can be extracted."""
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    ASSIGN_TASK = "assign_task"
    GENERATE_REPORT = "generate_report"
    QUERY_STATUS = "query_status"
    ESCALATE_ISSUE = "escalate_issue"
    REQUEST_INFO = "request_info"
    SCHEDULE_MEETING = "schedule_meeting"
    OTHER = "other"

@dataclass
class ExtractedIntent:
    """Structured representation of extracted intent."""
    intent_type: IntentType
    confidence: float
    title: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    actions: List[str] = None
    entities: Dict[str, List[str]] = None
    metadata: Dict[str, Any] = None

class IntentExtractor:
    """Extracts intent and structured information from natural language."""
    
    def __init__(self):
        self.llm_client = LLMClientFactory.create_classification_client()
        self.text_processor = TextProcessor()
        
        # Intent classification schema
        self.intent_schema = {
            "type": "object",
            "properties": {
                "intent_type": {
                    "type": "string",
                    "enum": [intent.value for intent in IntentType]
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "title": {
                    "type": "string",
                    "description": "A concise title for the request"
                },
                "description": {
                    "type": "string",
                    "description": "A detailed description of what needs to be done"
                },
                "category": {
                    "type": "string",
                    "enum": ["IT", "HR", "Operations"],
                    "description": "The category this request belongs to"
                },
                "priority": {
                    "type": "string",
                    "enum": ["Critical", "High", "Medium", "Low"],
                    "description": "The priority level of this request"
                },
                "actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific actions that need to be taken"
                },
                "entities": {
                    "type": "object",
                    "description": "Named entities extracted from the text"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata about the request"
                }
            },
            "required": ["intent_type", "confidence", "title", "description"]
        }
    
    def extract_intent(self, text: str) -> ExtractedIntent:
        """Extract intent and structured information from text."""
        if not text or not text.strip():
            raise ProcessingError("Empty text provided for intent extraction")
        
        try:
            # First, extract basic features using text processor
            features = self.text_processor.extract_features(text)
            
            # Create system prompt for intent extraction
            system_prompt = self._create_system_prompt()
            
            # Create user prompt with context
            user_prompt = self._create_user_prompt(text, features)
            
            # Get structured output from LLM
            result = self.llm_client.generate_structured_output(
                prompt=user_prompt,
                schema=self.intent_schema,
                system_prompt=system_prompt
            )
            
            # Validate and create ExtractedIntent object
            intent = self._create_extracted_intent(result, features)
            
            logger.info(f"Extracted intent: {intent.intent_type.value} with confidence {intent.confidence}")
            return intent
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            raise ProcessingError(f"Failed to extract intent: {e}")
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for intent extraction."""
        return """You are an expert AI assistant specialized in analyzing enterprise workflow requests. 
Your task is to extract structured information from natural language requests and classify them appropriately.

You should:
1. Identify the main intent/purpose of the request
2. Determine the appropriate category (IT, HR, or Operations)
3. Assess the priority level based on urgency indicators
4. Extract specific actions that need to be taken
5. Generate a clear title and description
6. Identify relevant entities and metadata

Be precise and consistent in your classifications. Consider context clues, urgency indicators, and domain-specific terminology."""
    
    def _create_user_prompt(self, text: str, features: Dict[str, Any]) -> str:
        """Create user prompt with context and features."""
        prompt = f"""Please analyze the following enterprise workflow request and extract structured information:

REQUEST TEXT:
{text}

EXTRACTED FEATURES:
- Keywords: {', '.join(features.get('keywords', [])[:10])}
- Priority indicators: {features.get('priority_indicators', {})}
- Category indicators: {features.get('category_indicators', {})}
- Urgency signals: {features.get('urgency_signals', {})}
- Word count: {features.get('word_count', 0)}

Please provide a structured analysis that includes:
1. Intent type classification
2. Confidence score (0-1)
3. Clear, concise title
4. Detailed description
5. Category classification
6. Priority assessment
7. Specific actionable steps
8. Relevant entities
9. Additional metadata

Focus on accuracy and provide reasoning for your classifications."""
        
        return prompt
    
    def _create_extracted_intent(self, result: Dict[str, Any], features: Dict[str, Any]) -> ExtractedIntent:
        """Create ExtractedIntent object from LLM result."""
        try:
            # Validate required fields
            intent_type_str = result.get("intent_type", "other")
            try:
                intent_type = IntentType(intent_type_str)
            except ValueError:
                intent_type = IntentType.OTHER
            
            confidence = float(result.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            title = result.get("title", "").strip()
            if not title:
                title = self.text_processor.generate_summary(features.get("original_text", ""), 50)
            
            description = result.get("description", "").strip()
            if not description:
                description = title
            
            # Optional fields
            category = result.get("category")
            priority = result.get("priority")
            actions = result.get("actions", [])
            entities = result.get("entities", {})
            metadata = result.get("metadata", {})
            
            # Add features to metadata
            metadata.update({
                "text_length": features.get("text_length", 0),
                "word_count": features.get("word_count", 0),
                "keywords_count": len(features.get("keywords", [])),
                "urgency_score": sum(features.get("urgency_signals", {}).values()) if isinstance(features.get("urgency_signals"), dict) else 0
            })
            
            return ExtractedIntent(
                intent_type=intent_type,
                confidence=confidence,
                title=title,
                description=description,
                category=category,
                priority=priority,
                actions=actions or [],
                entities=entities,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to create ExtractedIntent: {e}")
            raise ProcessingError(f"Failed to process extraction result: {e}")
    
    def extract_batch(self, texts: List[str]) -> List[ExtractedIntent]:
        """Extract intents from multiple texts."""
        results = []
        for i, text in enumerate(texts):
            try:
                intent = self.extract_intent(text)
                results.append(intent)
            except Exception as e:
                logger.error(f"Failed to extract intent for text {i}: {e}")
                # Create a fallback intent
                fallback_intent = ExtractedIntent(
                    intent_type=IntentType.OTHER,
                    confidence=0.1,
                    title=f"Processing failed for request {i+1}",
                    description=text[:200] + "..." if len(text) > 200 else text,
                    actions=[],
                    entities={},
                    metadata={"error": str(e)}
                )
                results.append(fallback_intent)
        
        return results
    
    def validate_intent(self, intent: ExtractedIntent) -> Tuple[bool, List[str]]:
        """Validate an extracted intent and return validation results."""
        errors = []
        
        # Check required fields
        if not intent.title or not intent.title.strip():
            errors.append("Title is required")
        
        if not intent.description or not intent.description.strip():
            errors.append("Description is required")
        
        if intent.confidence < 0 or intent.confidence > 1:
            errors.append("Confidence must be between 0 and 1")
        
        # Check category validity
        if intent.category and intent.category not in ["IT", "HR", "Operations"]:
            errors.append(f"Invalid category: {intent.category}")
        
        # Check priority validity
        if intent.priority and intent.priority not in ["Critical", "High", "Medium", "Low"]:
            errors.append(f"Invalid priority: {intent.priority}")
        
        # Check if actions are meaningful
        if intent.actions:
            for action in intent.actions:
                if not action or not action.strip():
                    errors.append("Empty action found in actions list")
        
        is_valid = len(errors) == 0
        return is_valid, errors
