"""
NLP Pipeline for the AI-Powered Enterprise Workflow Agent.

This module provides the main NLP pipeline that processes natural language
requests and extracts structured information for workflow automation.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time

from src.nlp.intent_extractor import IntentExtractor, ExtractedIntent
from src.nlp.text_processor import TextProcessor
from src.database.models import TaskCategory, TaskPriority
from src.core.exceptions import ProcessingError, ValidationError
from src.utils.logger import get_logger

logger = get_logger("nlp_pipeline")

class NLPPipeline:
    """Main NLP pipeline for processing natural language requests."""
    
    def __init__(self):
        self.intent_extractor = IntentExtractor()
        self.text_processor = TextProcessor()
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0
        }
    
    def process_request(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language request and return structured information."""
        start_time = time.time()
        
        try:
            # Validate input
            if not text or not text.strip():
                raise ValidationError("Empty or whitespace-only text provided")
            
            logger.info(f"Processing request: {text[:100]}...")
            
            # Step 1: Text preprocessing and feature extraction
            features = self.text_processor.extract_features(text)
            
            # Step 2: Intent extraction
            extracted_intent = self.intent_extractor.extract_intent(text)
            
            # Step 3: Validate extracted intent
            is_valid, validation_errors = self.intent_extractor.validate_intent(extracted_intent)
            if not is_valid:
                logger.warning(f"Intent validation failed: {validation_errors}")
            
            # Step 4: Post-process and enhance results
            processed_result = self._post_process_results(extracted_intent, features, context)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(True, processing_time)
            
            logger.info(f"Successfully processed request in {processing_time:.2f}s")
            return processed_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)
            logger.error(f"Failed to process request: {e}")
            raise ProcessingError(f"NLP pipeline failed: {e}")
    
    def process_batch(self, texts: List[str], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Process multiple natural language requests."""
        results = []
        
        logger.info(f"Processing batch of {len(texts)} requests")
        
        for i, text in enumerate(texts):
            try:
                result = self.process_request(text, context)
                result["batch_index"] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process request {i}: {e}")
                # Create error result
                error_result = {
                    "batch_index": i,
                    "error": str(e),
                    "original_text": text,
                    "success": False
                }
                results.append(error_result)
        
        logger.info(f"Completed batch processing: {len([r for r in results if r.get('success', True)])} successful")
        return results
    
    def _post_process_results(
        self, 
        intent: ExtractedIntent, 
        features: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Post-process and enhance extraction results."""
        
        # Convert to standardized format
        result = {
            "success": True,
            "intent": {
                "type": intent.intent_type.value,
                "confidence": intent.confidence,
                "title": intent.title,
                "description": intent.description,
                "actions": intent.actions or []
            },
            "classification": {
                "category": self._normalize_category(intent.category),
                "priority": self._normalize_priority(intent.priority),
                "category_confidence": self._calculate_category_confidence(intent, features),
                "priority_confidence": self._calculate_priority_confidence(intent, features)
            },
            "entities": intent.entities or {},
            "features": {
                "keywords": features.get("keywords", []),
                "text_length": features.get("text_length", 0),
                "word_count": features.get("word_count", 0),
                "urgency_signals": features.get("urgency_signals", {}),
                "dates": features.get("dates", [])
            },
            "metadata": {
                "processing_timestamp": datetime.utcnow().isoformat(),
                "pipeline_version": "1.0",
                "model_used": "classification",
                **(intent.metadata or {}),
                **(context or {})
            }
        }
        
        # Add quality scores
        result["quality"] = self._calculate_quality_scores(intent, features)
        
        return result
    
    def _normalize_category(self, category: Optional[str]) -> Optional[str]:
        """Normalize category to standard values."""
        if not category:
            return None
        
        category_upper = category.upper()
        if category_upper in ["IT", "INFORMATION TECHNOLOGY", "TECH", "TECHNOLOGY"]:
            return "IT"
        elif category_upper in ["HR", "HUMAN RESOURCES", "PEOPLE", "PERSONNEL"]:
            return "HR"
        elif category_upper in ["OPERATIONS", "OPS", "BUSINESS", "PROCESS"]:
            return "Operations"
        else:
            return category  # Return as-is if not recognized
    
    def _normalize_priority(self, priority: Optional[str]) -> Optional[str]:
        """Normalize priority to standard values."""
        if not priority:
            return None
        
        priority_lower = priority.lower()
        if priority_lower in ["critical", "urgent", "emergency", "p1"]:
            return "Critical"
        elif priority_lower in ["high", "important", "p2"]:
            return "High"
        elif priority_lower in ["medium", "normal", "standard", "p3"]:
            return "Medium"
        elif priority_lower in ["low", "minor", "p4"]:
            return "Low"
        else:
            return priority.title()  # Capitalize first letter
    
    def _calculate_category_confidence(self, intent: ExtractedIntent, features: Dict[str, Any]) -> float:
        """Calculate confidence score for category classification."""
        if not intent.category:
            return 0.0
        
        # Base confidence from intent extraction
        base_confidence = intent.confidence
        
        # Boost confidence based on category indicators
        category_indicators = features.get("category_indicators", {})
        category_score = category_indicators.get(intent.category, 0.0)
        
        # Combine scores
        combined_confidence = (base_confidence * 0.7) + (category_score * 0.3)
        return min(1.0, combined_confidence)
    
    def _calculate_priority_confidence(self, intent: ExtractedIntent, features: Dict[str, Any]) -> float:
        """Calculate confidence score for priority classification."""
        if not intent.priority:
            return 0.0
        
        # Base confidence from intent extraction
        base_confidence = intent.confidence
        
        # Boost confidence based on priority indicators and urgency signals
        priority_indicators = features.get("priority_indicators", {})
        urgency_signals = features.get("urgency_signals", {})
        
        priority_score = priority_indicators.get(intent.priority.lower(), 0.0)
        urgency_score = sum(urgency_signals.values()) / 10.0 if urgency_signals else 0.0  # Normalize
        
        # Combine scores
        combined_confidence = (base_confidence * 0.6) + (priority_score * 0.2) + (urgency_score * 0.2)
        return min(1.0, combined_confidence)
    
    def _calculate_quality_scores(self, intent: ExtractedIntent, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality scores for the extraction."""
        
        # Completeness score (how much information was extracted)
        completeness = 0.0
        if intent.title: completeness += 0.2
        if intent.description: completeness += 0.2
        if intent.category: completeness += 0.2
        if intent.priority: completeness += 0.2
        if intent.actions: completeness += 0.2
        
        # Confidence score (average of all confidence scores)
        confidence = intent.confidence
        
        # Clarity score (based on text features)
        text_length = features.get("text_length", 0)
        word_count = features.get("word_count", 0)
        
        clarity = 0.5  # Base score
        if text_length > 20: clarity += 0.2  # Sufficient detail
        if word_count > 5: clarity += 0.2   # Multiple words
        if features.get("keywords"): clarity += 0.1  # Has keywords
        
        clarity = min(1.0, clarity)
        
        # Overall quality (weighted average)
        overall = (completeness * 0.4) + (confidence * 0.4) + (clarity * 0.2)
        
        return {
            "completeness": completeness,
            "confidence": confidence,
            "clarity": clarity,
            "overall": overall
        }
    
    def _update_stats(self, success: bool, processing_time: float):
        """Update processing statistics."""
        self.stats["total_processed"] += 1
        
        if success:
            self.stats["successful_extractions"] += 1
        else:
            self.stats["failed_extractions"] += 1
        
        # Update average processing time
        total_time = self.stats["average_processing_time"] * (self.stats["total_processed"] - 1)
        self.stats["average_processing_time"] = (total_time + processing_time) / self.stats["total_processed"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        success_rate = 0.0
        if self.stats["total_processed"] > 0:
            success_rate = self.stats["successful_extractions"] / self.stats["total_processed"]
        
        return {
            **self.stats,
            "success_rate": success_rate
        }
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_processing_time": 0.0
        }
