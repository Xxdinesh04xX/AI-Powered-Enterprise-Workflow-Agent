"""
Text processing utilities for the AI-Powered Enterprise Workflow Agent.

This module provides text preprocessing, cleaning, and feature extraction
capabilities for natural language processing tasks.
"""

import re
import string
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

from src.utils.logger import get_logger

logger = get_logger("text_processor")

class TextProcessor:
    """Text processing and feature extraction utilities."""
    
    def __init__(self):
        self.nlp = None
        self._load_spacy_model()
        
        # Priority keywords
        self.priority_keywords = {
            "critical": ["critical", "urgent", "emergency", "asap", "immediately", "crisis", "outage", "down"],
            "high": ["high", "important", "priority", "soon", "quickly", "fast", "escalate"],
            "medium": ["medium", "normal", "standard", "regular", "moderate"],
            "low": ["low", "minor", "when possible", "eventually", "nice to have", "enhancement"]
        }
        
        # Category keywords
        self.category_keywords = {
            "IT": [
                "server", "network", "database", "application", "software", "hardware",
                "bug", "error", "crash", "performance", "security", "backup", "deploy",
                "infrastructure", "system", "code", "api", "website", "email", "vpn",
                "firewall", "patch", "update", "install", "configure", "troubleshoot"
            ],
            "HR": [
                "employee", "staff", "hire", "recruit", "interview", "onboard", "training",
                "payroll", "benefits", "leave", "vacation", "sick", "performance review",
                "promotion", "termination", "resignation", "policy", "compliance",
                "harassment", "diversity", "compensation", "salary", "bonus"
            ],
            "Operations": [
                "process", "workflow", "procedure", "project", "task", "deadline",
                "meeting", "schedule", "planning", "budget", "cost", "vendor",
                "contract", "procurement", "quality", "audit", "compliance",
                "reporting", "analytics", "metrics", "kpi", "improvement"
            ]
        }
    
    def _load_spacy_model(self):
        """Load spaCy model for NLP processing."""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available. Some features may be limited.")
            self.nlp = None
            return

        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Some features may be limited.")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Clean text
        cleaned_text = self.clean_text(text)
        
        if self.nlp:
            # Use spaCy for better keyword extraction
            doc = self.nlp(cleaned_text)
            keywords = []
            
            for token in doc:
                # Extract meaningful tokens (nouns, verbs, adjectives)
                if (token.pos_ in ['NOUN', 'VERB', 'ADJ'] and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2):
                    keywords.append(token.lemma_)
            
            return list(set(keywords))
        else:
            # Fallback to simple tokenization
            words = cleaned_text.split()
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            return list(set(keywords))
    
    def extract_priority_indicators(self, text: str) -> Dict[str, float]:
        """Extract priority indicators from text."""
        if not text:
            return {}
        
        cleaned_text = self.clean_text(text)
        priority_scores = {}
        
        for priority, keywords in self.priority_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of priority keywords
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', cleaned_text))
                score += count
            
            # Normalize score
            priority_scores[priority] = score / len(keywords) if keywords else 0
        
        return priority_scores
    
    def extract_category_indicators(self, text: str) -> Dict[str, float]:
        """Extract category indicators from text."""
        if not text:
            return {}
        
        cleaned_text = self.clean_text(text)
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of category keywords
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', cleaned_text))
                score += count
            
            # Normalize score
            category_scores[category] = score / len(keywords) if keywords else 0
        
        return category_scores
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        if not text or not self.nlp:
            return {}
        
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            entity_type = ent.label_
            entity_text = ent.text
            
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].append(entity_text)
        
        return entities
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract date references from text."""
        if not text:
            return []
        
        dates = []
        
        # Common date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
            r'\b(?:today|tomorrow|yesterday)\b',     # Relative dates
            r'\b(?:next|last)\s+(?:week|month|year)\b',  # Relative periods
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',  # Days of week
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                dates.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return dates
    
    def extract_urgency_signals(self, text: str) -> Dict[str, Any]:
        """Extract urgency signals from text."""
        if not text:
            return {}
        
        cleaned_text = self.clean_text(text)
        
        urgency_signals = {
            "exclamation_marks": len(re.findall(r'!', text)),
            "caps_words": len(re.findall(r'\b[A-Z]{2,}\b', text)),
            "urgent_phrases": 0,
            "time_constraints": []
        }
        
        # Urgent phrases
        urgent_phrases = [
            "asap", "urgent", "emergency", "critical", "immediately",
            "right away", "as soon as possible", "time sensitive"
        ]
        
        for phrase in urgent_phrases:
            if phrase in cleaned_text:
                urgency_signals["urgent_phrases"] += 1
        
        # Time constraints
        time_patterns = [
            r'\bby\s+\w+\b',  # "by Friday"
            r'\bwithin\s+\d+\s+\w+\b',  # "within 2 hours"
            r'\bbefore\s+\w+\b',  # "before noon"
            r'\bdeadline\b',
            r'\bdue\s+\w+\b'  # "due tomorrow"
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, cleaned_text)
            urgency_signals["time_constraints"].extend(matches)
        
        return urgency_signals
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive features from text."""
        if not text:
            return {}
        
        features = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "keywords": self.extract_keywords(text),
            "priority_indicators": self.extract_priority_indicators(text),
            "category_indicators": self.extract_category_indicators(text),
            "urgency_signals": self.extract_urgency_signals(text),
            "dates": self.extract_dates(text),
            "entities": self.extract_entities(text)
        }
        
        return features
    
    def generate_summary(self, text: str, max_length: int = 100) -> str:
        """Generate a summary of the text."""
        if not text:
            return ""
        
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Take the first sentence as summary
        summary = sentences[0].strip()
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
