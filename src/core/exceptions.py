"""
Custom exceptions for the AI-Powered Enterprise Workflow Agent.

This module defines custom exception classes for better error handling
and debugging throughout the application.
"""

class WorkflowAgentException(Exception):
    """Base exception class for the workflow agent."""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(WorkflowAgentException):
    """Raised when there's a configuration-related error."""
    pass

class DatabaseError(WorkflowAgentException):
    """Raised when there's a database-related error."""
    pass

class LLMError(WorkflowAgentException):
    """Raised when there's an LLM-related error."""
    pass

class ClassificationError(WorkflowAgentException):
    """Raised when task classification fails."""
    pass

class AssignmentError(WorkflowAgentException):
    """Raised when task assignment fails."""
    pass

class ReportGenerationError(WorkflowAgentException):
    """Raised when report generation fails."""
    pass

class ValidationError(WorkflowAgentException):
    """Raised when input validation fails."""
    pass

class ProcessingError(WorkflowAgentException):
    """Raised when general processing fails."""
    pass

class IntegrationError(WorkflowAgentException):
    """Raised when enterprise system integration fails."""
    pass
