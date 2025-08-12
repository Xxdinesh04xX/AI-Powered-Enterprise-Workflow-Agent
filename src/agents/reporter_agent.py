"""
Reporter Agent for the AI-Powered Enterprise Workflow Agent.

This agent specializes in generating comprehensive reports and analytics
from workflow data, providing insights and actionable recommendations.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent, AgentResult
from src.nlp.llm_client import LLMClientFactory
from src.database.connection import db_manager
from src.database.operations import AnalyticsOperations, ReportOperations
from src.core.exceptions import ProcessingError, ReportGenerationError
from src.utils.logger import get_logger

logger = get_logger("reporter_agent")

class ReporterAgent(BaseAgent):
    """Agent responsible for generating reports and analytics."""
    
    def __init__(self):
        llm_client = LLMClientFactory.create_reporting_client()
        super().__init__("ReporterAgent", llm_client)
        
        # Report schema for structured output
        self.report_schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the report"
                },
                "executive_summary": {
                    "type": "string",
                    "description": "High-level summary of key findings"
                },
                "key_metrics": {
                    "type": "object",
                    "description": "Important metrics and KPIs"
                },
                "insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key insights and observations"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Actionable recommendations"
                },
                "trends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric": {"type": "string"},
                            "direction": {"type": "string"},
                            "significance": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "description": "Identified trends in the data"
                },
                "risk_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas of concern or risk"
                },
                "performance_highlights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable performance achievements"
                }
            },
            "required": ["title", "executive_summary", "key_metrics", "insights", "recommendations"]
        }
    
    def get_step_name(self) -> str:
        """Get the name of the processing step."""
        return "reporting"
    
    def execute(self, report_request: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute report generation."""
        try:
            # Extract report parameters
            report_type = report_request.get("type", "general")
            date_range_start = report_request.get("date_range_start")
            date_range_end = report_request.get("date_range_end")
            filters = report_request.get("filters", {})
            
            logger.info(f"Generating {report_type} report for period {date_range_start} to {date_range_end}")
            
            # Parse date ranges
            start_date, end_date = self._parse_date_range(date_range_start, date_range_end)
            
            # Collect data based on report type
            if report_type == "daily":
                data = self._collect_daily_data(start_date, end_date, filters)
            elif report_type == "weekly":
                data = self._collect_weekly_data(start_date, end_date, filters)
            elif report_type == "monthly":
                data = self._collect_monthly_data(start_date, end_date, filters)
            elif report_type == "performance":
                data = self._collect_performance_data(start_date, end_date, filters)
            else:
                data = self._collect_general_data(start_date, end_date, filters)
            
            # Generate report using LLM
            report_content = self._generate_report_with_llm(report_type, data, start_date, end_date)
            
            # Store report in database
            report_id = self._store_report(report_type, report_content, start_date, end_date, filters)
            
            # Prepare result
            result = AgentResult(
                success=True,
                data={
                    "report_id": report_id,
                    "report_type": report_type,
                    "content": report_content,
                    "date_range": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    },
                    "data_points": len(data.get("tasks", [])),
                    "generation_timestamp": datetime.utcnow().isoformat()
                },
                confidence=0.9,  # High confidence for data-driven reports
                reasoning=f"Generated {report_type} report with {len(data.get('tasks', []))} data points",
                metadata={
                    "model_used": self.llm_client.model_name,
                    "filters_applied": filters,
                    "data_sources": list(data.keys())
                }
            )
            
            logger.info(f"Successfully generated {report_type} report with ID {report_id}")
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ReportGenerationError(f"Report generation failed: {e}")
    
    def _parse_date_range(self, start_str: Optional[str], end_str: Optional[str]) -> tuple:
        """Parse date range strings."""
        start_date = None
        end_date = None
        
        if start_str:
            try:
                start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid start date format: {start_str}")
        
        if end_str:
            try:
                end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid end date format: {end_str}")
        
        # Default to last 7 days if no dates provided
        if not start_date and not end_date:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
        elif not start_date:
            start_date = end_date - timedelta(days=7)
        elif not end_date:
            end_date = datetime.utcnow()
        
        return start_date, end_date
    
    def _collect_general_data(self, start_date: datetime, end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect general workflow data."""
        try:
            with db_manager.get_session() as session:
                # Get task statistics
                stats = AnalyticsOperations.get_task_statistics(session, start_date, end_date)
                
                # Get additional metrics
                data = {
                    "statistics": stats,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "filters": filters
                }
                
                return data
                
        except Exception as e:
            logger.error(f"Failed to collect general data: {e}")
            raise ReportGenerationError(f"Failed to collect data: {e}")
    
    def _collect_daily_data(self, start_date: datetime, end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect daily workflow data."""
        # For now, use general data collection
        # This can be enhanced with daily-specific metrics
        return self._collect_general_data(start_date, end_date, filters)
    
    def _collect_weekly_data(self, start_date: datetime, end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect weekly workflow data."""
        # For now, use general data collection
        # This can be enhanced with weekly-specific metrics
        return self._collect_general_data(start_date, end_date, filters)
    
    def _collect_monthly_data(self, start_date: datetime, end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect monthly workflow data."""
        # For now, use general data collection
        # This can be enhanced with monthly-specific metrics
        return self._collect_general_data(start_date, end_date, filters)
    
    def _collect_performance_data(self, start_date: datetime, end_date: datetime, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Collect performance-specific data."""
        # For now, use general data collection
        # This can be enhanced with performance-specific metrics
        return self._collect_general_data(start_date, end_date, filters)
    
    def _generate_report_with_llm(
        self, 
        report_type: str, 
        data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate report content using LLM."""
        
        # Create system prompt
        system_prompt = self._create_reporting_system_prompt(report_type)
        
        # Create user prompt with data
        user_prompt = self._create_reporting_user_prompt(report_type, data, start_date, end_date)
        
        try:
            # Get structured report from LLM
            result = self.llm_client.generate_structured_output(
                prompt=user_prompt,
                schema=self.report_schema,
                system_prompt=system_prompt
            )
            
            # Add metadata
            result["metadata"] = {
                "report_type": report_type,
                "generation_timestamp": datetime.utcnow().isoformat(),
                "data_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "model_used": self.llm_client.model_name
            }
            
            return result
            
        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            raise ReportGenerationError(f"LLM report generation failed: {e}")
    
    def _create_reporting_system_prompt(self, report_type: str) -> str:
        """Create system prompt for report generation."""
        return f"""You are an expert enterprise analytics and reporting specialist. Your task is to analyze workflow data and generate comprehensive {report_type} reports.

Your reports should:
1. Provide clear, actionable insights from the data
2. Identify trends, patterns, and anomalies
3. Offer specific recommendations for improvement
4. Highlight both achievements and areas of concern
5. Use professional business language
6. Focus on metrics that matter to enterprise stakeholders

Report Structure:
- Executive Summary: High-level overview for leadership
- Key Metrics: Important KPIs and measurements
- Insights: Data-driven observations and findings
- Recommendations: Specific, actionable next steps
- Trends: Patterns and changes over time
- Risk Areas: Potential issues requiring attention
- Performance Highlights: Notable successes and achievements

Be analytical, objective, and focus on providing value to business decision-makers."""
    
    def _create_reporting_user_prompt(
        self, 
        report_type: str, 
        data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> str:
        """Create user prompt for report generation."""
        
        stats = data.get("statistics", {})
        
        prompt = f"""Please generate a comprehensive {report_type} report based on the following workflow data:

REPORTING PERIOD: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

WORKFLOW STATISTICS:
- Total Tasks: {stats.get('total_tasks', 0)}
- Status Distribution: {stats.get('status_distribution', {})}
- Category Distribution: {stats.get('category_distribution', {})}
- Priority Distribution: {stats.get('priority_distribution', {})}

DATA CONTEXT:
{json.dumps(data, indent=2, default=str)}

Please analyze this data and provide:
1. A clear executive summary of the key findings
2. Important metrics and KPIs
3. Data-driven insights and observations
4. Specific recommendations for improvement
5. Identified trends and patterns
6. Areas of risk or concern
7. Performance highlights and achievements

Focus on providing actionable intelligence that can help improve workflow efficiency and business outcomes."""
        
        return prompt
    
    def _store_report(
        self, 
        report_type: str, 
        content: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime, 
        filters: Dict[str, Any]
    ) -> int:
        """Store generated report in database."""
        try:
            with db_manager.get_session() as session:
                report = ReportOperations.create_report(
                    session=session,
                    title=content.get("title", f"{report_type.title()} Report"),
                    report_type=report_type,
                    content=content,
                    generated_by=self.agent_name,
                    description=content.get("executive_summary", ""),
                    summary=content.get("executive_summary", ""),
                    date_range_start=start_date,
                    date_range_end=end_date
                )
                
                return report.id
                
        except Exception as e:
            logger.error(f"Failed to store report: {e}")
            raise ReportGenerationError(f"Failed to store report: {e}")
    
    def generate_batch_reports(self, report_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate multiple reports in batch."""
        results = []
        
        for request in report_requests:
            try:
                result = self.execute(request)
                results.append(result)
            except Exception as e:
                error_result = {
                    "success": False,
                    "report_type": request.get("type", "unknown"),
                    "error": str(e)
                }
                results.append(error_result)
        
        return results
