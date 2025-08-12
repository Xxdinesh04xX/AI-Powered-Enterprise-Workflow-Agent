"""
Configuration management for the AI-Powered Enterprise Workflow Agent.

This module handles loading and managing configuration from various sources
including YAML files, environment variables, and default settings.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import Field
from dotenv import load_dotenv

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

# Load environment variables
load_dotenv()

class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    url: str = Field(default="sqlite:///./data/workflow_agent.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)

class LLMConfig(BaseSettings):
    """LLM configuration settings."""
    default_provider: str = Field(default="openai")
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=2000)
    timeout: int = Field(default=30)
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

class APIConfig(BaseSettings):
    """API server configuration settings."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)
    workers: int = Field(default=1)
    cors_origins: List[str] = Field(default=["http://localhost:8501", "http://127.0.0.1:8501"])

class ClassificationConfig(BaseSettings):
    """Task classification configuration settings."""
    categories: List[str] = Field(default=["IT", "HR", "Operations"])
    priorities: List[str] = Field(default=["Critical", "High", "Medium", "Low"])
    confidence_threshold: float = Field(default=0.8)
    min_confidence: float = Field(default=0.6)

class AssignmentConfig(BaseSettings):
    """Task assignment configuration settings."""
    strategy: str = Field(default="skill_based")
    confidence_threshold: float = Field(default=0.75)

class ReportConfig(BaseSettings):
    """Report generation configuration settings."""
    output_dir: str = Field(default="./reports")
    template_dir: str = Field(default="./templates")
    formats: List[str] = Field(default=["pdf", "html", "json"])

class Config:
    """Main configuration class for the workflow agent."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file and environment variables."""
        self.config_path = config_path or "config/settings.yaml"
        self._config_data = self._load_config()
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.api = APIConfig()
        self.classification = ClassificationConfig()
        self.assignment = AssignmentConfig()
        self.reports = ReportConfig()
        
        # Load additional settings from YAML
        self._load_yaml_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_yaml_config(self):
        """Load additional configuration from YAML file."""
        if not self._config_data:
            return
        
        # Update database config
        if 'database' in self._config_data:
            db_config = self._config_data['database']
            self.database.url = db_config.get('url', self.database.url)
            self.database.echo = db_config.get('echo', self.database.echo)
        
        # Update LLM config
        if 'llm' in self._config_data:
            llm_config = self._config_data['llm']
            self.llm.default_provider = llm_config.get('default_provider', self.llm.default_provider)
            self.llm.temperature = llm_config.get('temperature', self.llm.temperature)
            self.llm.max_tokens = llm_config.get('max_tokens', self.llm.max_tokens)
        
        # Update API config
        if 'api' in self._config_data:
            api_config = self._config_data['api']
            self.api.host = api_config.get('host', self.api.host)
            self.api.port = api_config.get('port', self.api.port)
            self.api.cors_origins = api_config.get('cors_origins', self.api.cors_origins)
        
        # Update classification config
        if 'classification' in self._config_data:
            class_config = self._config_data['classification']
            self.classification.categories = class_config.get('categories', self.classification.categories)
            self.classification.priorities = class_config.get('priorities', self.classification.priorities)
            self.classification.confidence_threshold = class_config.get('confidence_threshold', self.classification.confidence_threshold)
        
        # Update assignment config
        if 'assignment' in self._config_data:
            assign_config = self._config_data['assignment']
            self.assignment.strategy = assign_config.get('strategy', self.assignment.strategy)
            self.assignment.confidence_threshold = assign_config.get('confidence_threshold', self.assignment.confidence_threshold)
    
    def get_teams_by_category(self, category: str) -> List[str]:
        """Get available teams for a specific category."""
        teams_config = self._config_data.get('assignment', {}).get('teams', {})
        return teams_config.get(category, [])
    
    def get_llm_model(self, task_type: str = "default") -> str:
        """Get the appropriate LLM model for a specific task type."""
        models_config = self._config_data.get('llm', {}).get('models', {})
        provider_models = models_config.get(self.llm.default_provider, {})
        return provider_models.get(task_type, provider_models.get('default', 'gpt-3.5-turbo'))

# Global configuration instance
config = Config()
