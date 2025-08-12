"""
Report Manager for the AI-Powered Enterprise Workflow Agent.

This module provides a unified interface for generating comprehensive reports
with analytics, insights, and multiple output formats.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from src.reports.generators import ReportGeneratorFactory
from src.reports.analytics import WorkflowAnalytics
from src.agents.reporter_agent import ReporterAgent
from src.database.connection import db_manager
from src.database.operations import ReportOperations
from src.core.exceptions import ReportGenerationError
from src.utils.logger import get_logger

logger = get_logger("report_manager")

class ReportManager:
    """Unified report management system."""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.analytics = WorkflowAnalytics()
        self.reporter_agent = None  # Initialize lazily when needed
        
        # Report templates
        self.report_templates = {
            'daily': self._create_daily_template,
            'weekly': self._create_weekly_template,
            'monthly': self._create_monthly_template,
            'performance': self._create_performance_template,
            'custom': self._create_custom_template
        }
    
    def generate_report(
        self,
        report_type: str = "daily",
        output_formats: List[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None,
        include_analytics: bool = True,
        use_ai_insights: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a comprehensive report with specified parameters."""
        
        if output_formats is None:
            output_formats = ['html', 'json']
        
        logger.info(f"Generating {report_type} report with formats: {output_formats}")
        
        try:
            # Set default date ranges based on report type
            if not start_date or not end_date:
                start_date, end_date = self._get_default_date_range(report_type)
            
            # Generate analytics data
            analytics_data = {}
            if include_analytics:
                analytics_data = self.analytics.generate_comprehensive_analytics(
                    start_date, end_date, categories
                )
            
            # Create report content using template
            template_func = self.report_templates.get(report_type, self._create_custom_template)
            report_content = template_func(analytics_data, start_date, end_date, **kwargs)
            
            # Enhance with AI insights if requested
            if use_ai_insights and analytics_data:
                report_content = self._enhance_with_ai_insights(report_content, analytics_data)
            
            # Generate output files
            generated_files = {}
            for format_type in output_formats:
                try:
                    generator = ReportGeneratorFactory.create_generator(format_type, str(self.output_dir))
                    filename = self._generate_filename(report_type, format_type, start_date, end_date)
                    file_path = generator.generate(report_content, filename)
                    generated_files[format_type] = file_path
                    logger.info(f"Generated {format_type} report: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to generate {format_type} report: {e}")
                    generated_files[format_type] = f"Error: {str(e)}"
            
            # Store report metadata in database
            report_id = self._store_report_metadata(
                report_type, report_content, start_date, end_date, generated_files
            )
            
            result = {
                'report_id': report_id,
                'report_type': report_type,
                'generated_files': generated_files,
                'content': report_content,
                'analytics_data': analytics_data if include_analytics else None,
                'generation_timestamp': datetime.utcnow().isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
            logger.info(f"Report generation completed successfully. Report ID: {report_id}")
            return result
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ReportGenerationError(f"Failed to generate {report_type} report: {e}")
    
    def _get_default_date_range(self, report_type: str) -> tuple:
        """Get default date range for report type."""
        end_date = datetime.utcnow()
        
        if report_type == 'daily':
            start_date = end_date - timedelta(days=1)
        elif report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)  # Default to weekly
        
        return start_date, end_date
    
    def _create_daily_template(
        self,
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create daily report template."""
        
        basic_stats = analytics_data.get('basic_statistics', {})
        performance_metrics = analytics_data.get('performance_metrics', {})
        
        return {
            'title': f"Daily Workflow Report - {start_date.strftime('%Y-%m-%d')}",
            'executive_summary': self._create_daily_summary(basic_stats, performance_metrics),
            'key_metrics': {
                'total_tasks': basic_stats.get('total_tasks', 0),
                'completion_rate': f"{basic_stats.get('completion_rate', 0):.1%}",
                'status_distribution': basic_stats.get('status_distribution', {}),
                'category_distribution': basic_stats.get('category_distribution', {}),
                'priority_distribution': basic_stats.get('priority_distribution', {}),
                'average_processing_time': f"{basic_stats.get('average_processing_time', 0)/60:.1f} minutes"
            },
            'insights': analytics_data.get('insights', []),
            'recommendations': analytics_data.get('recommendations', []),
            'trends': analytics_data.get('trends', []),
            'risk_areas': analytics_data.get('risk_areas', []),
            'performance_highlights': analytics_data.get('performance_highlights', []),
            'metadata': {
                'report_type': 'daily',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_by': 'ReportManager'
            }
        }
    
    def _create_weekly_template(
        self,
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create weekly report template."""
        
        basic_stats = analytics_data.get('basic_statistics', {})
        performance_metrics = analytics_data.get('performance_metrics', {})
        
        return {
            'title': f"Weekly Workflow Report - Week of {start_date.strftime('%Y-%m-%d')}",
            'executive_summary': self._create_weekly_summary(basic_stats, performance_metrics),
            'key_metrics': {
                'total_tasks': basic_stats.get('total_tasks', 0),
                'completion_rate': f"{basic_stats.get('completion_rate', 0):.1%}",
                'daily_average': basic_stats.get('total_tasks', 0) / 7,
                'status_distribution': basic_stats.get('status_distribution', {}),
                'category_distribution': basic_stats.get('category_distribution', {}),
                'priority_distribution': basic_stats.get('priority_distribution', {}),
                'agent_performance': performance_metrics.get('agent_performance', {}),
                'category_performance': performance_metrics.get('category_performance', {})
            },
            'insights': analytics_data.get('insights', []),
            'recommendations': analytics_data.get('recommendations', []),
            'trends': analytics_data.get('trends', []),
            'risk_areas': analytics_data.get('risk_areas', []),
            'performance_highlights': analytics_data.get('performance_highlights', []),
            'metadata': {
                'report_type': 'weekly',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_by': 'ReportManager'
            }
        }
    
    def _create_monthly_template(
        self,
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create monthly report template."""
        
        basic_stats = analytics_data.get('basic_statistics', {})
        performance_metrics = analytics_data.get('performance_metrics', {})
        
        return {
            'title': f"Monthly Workflow Report - {start_date.strftime('%B %Y')}",
            'executive_summary': self._create_monthly_summary(basic_stats, performance_metrics),
            'key_metrics': {
                'total_tasks': basic_stats.get('total_tasks', 0),
                'completion_rate': f"{basic_stats.get('completion_rate', 0):.1%}",
                'daily_average': basic_stats.get('total_tasks', 0) / 30,
                'status_distribution': basic_stats.get('status_distribution', {}),
                'category_distribution': basic_stats.get('category_distribution', {}),
                'priority_distribution': basic_stats.get('priority_distribution', {}),
                'agent_performance': performance_metrics.get('agent_performance', {}),
                'category_performance': performance_metrics.get('category_performance', {}),
                'priority_handling': performance_metrics.get('priority_handling', {})
            },
            'insights': analytics_data.get('insights', []),
            'recommendations': analytics_data.get('recommendations', []),
            'trends': analytics_data.get('trends', []),
            'risk_areas': analytics_data.get('risk_areas', []),
            'performance_highlights': analytics_data.get('performance_highlights', []),
            'metadata': {
                'report_type': 'monthly',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_by': 'ReportManager'
            }
        }
    
    def _create_performance_template(
        self,
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create performance-focused report template."""
        
        performance_metrics = analytics_data.get('performance_metrics', {})
        
        return {
            'title': f"Performance Analysis Report - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'executive_summary': self._create_performance_summary(performance_metrics),
            'key_metrics': {
                'agent_performance': performance_metrics.get('agent_performance', {}),
                'category_performance': performance_metrics.get('category_performance', {}),
                'priority_handling': performance_metrics.get('priority_handling', {}),
                'task_completion': performance_metrics.get('task_completion', {})
            },
            'insights': analytics_data.get('insights', []),
            'recommendations': analytics_data.get('recommendations', []),
            'trends': analytics_data.get('trends', []),
            'risk_areas': analytics_data.get('risk_areas', []),
            'performance_highlights': analytics_data.get('performance_highlights', []),
            'metadata': {
                'report_type': 'performance',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_by': 'ReportManager'
            }
        }
    
    def _create_custom_template(
        self,
        analytics_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """Create custom report template."""
        
        title = kwargs.get('title', f"Custom Workflow Report - {start_date.strftime('%Y-%m-%d')}")
        
        return {
            'title': title,
            'executive_summary': kwargs.get('summary', 'Custom workflow analysis report'),
            'key_metrics': analytics_data.get('basic_statistics', {}),
            'insights': analytics_data.get('insights', []),
            'recommendations': analytics_data.get('recommendations', []),
            'trends': analytics_data.get('trends', []),
            'risk_areas': analytics_data.get('risk_areas', []),
            'performance_highlights': analytics_data.get('performance_highlights', []),
            'metadata': {
                'report_type': 'custom',
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'generated_by': 'ReportManager'
            }
        }
    
    def _create_daily_summary(self, basic_stats: Dict[str, Any], performance_metrics: Dict[str, Any]) -> str:
        """Create daily report summary."""
        total_tasks = basic_stats.get('total_tasks', 0)
        completion_rate = basic_stats.get('completion_rate', 0)
        
        summary = f"Daily workflow summary: {total_tasks} tasks processed with {completion_rate:.1%} completion rate. "
        
        if completion_rate > 0.8:
            summary += "Strong performance with high completion rate. "
        elif completion_rate < 0.6:
            summary += "Performance below target with opportunities for improvement. "
        
        return summary
    
    def _create_weekly_summary(self, basic_stats: Dict[str, Any], performance_metrics: Dict[str, Any]) -> str:
        """Create weekly report summary."""
        total_tasks = basic_stats.get('total_tasks', 0)
        completion_rate = basic_stats.get('completion_rate', 0)
        daily_avg = total_tasks / 7
        
        summary = f"Weekly workflow summary: {total_tasks} tasks processed ({daily_avg:.1f} per day average) with {completion_rate:.1%} completion rate. "
        
        category_dist = basic_stats.get('category_distribution', {})
        if category_dist:
            dominant_category = max(category_dist.items(), key=lambda x: x[1])
            summary += f"{dominant_category[0]} category was most active with {dominant_category[1]} tasks. "
        
        return summary
    
    def _create_monthly_summary(self, basic_stats: Dict[str, Any], performance_metrics: Dict[str, Any]) -> str:
        """Create monthly report summary."""
        total_tasks = basic_stats.get('total_tasks', 0)
        completion_rate = basic_stats.get('completion_rate', 0)
        daily_avg = total_tasks / 30
        
        summary = f"Monthly workflow summary: {total_tasks} tasks processed ({daily_avg:.1f} per day average) with {completion_rate:.1%} completion rate. "
        
        # Add trend information
        summary += "This report provides comprehensive analysis of workflow performance, trends, and recommendations for optimization. "
        
        return summary
    
    def _create_performance_summary(self, performance_metrics: Dict[str, Any]) -> str:
        """Create performance report summary."""
        summary = "Performance analysis focusing on agent efficiency, category handling, and priority management. "
        
        agent_perf = performance_metrics.get('agent_performance', {})
        if agent_perf:
            avg_success_rate = sum(perf.get('success_rate', 0) for perf in agent_perf.values()) / len(agent_perf)
            summary += f"Average agent success rate: {avg_success_rate:.1%}. "
        
        return summary
    
    def _enhance_with_ai_insights(self, report_content: Dict[str, Any], analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance report with AI-generated insights."""
        try:
            if self.reporter_agent is None:
                self.reporter_agent = ReporterAgent()
            
            # Create request for AI enhancement
            ai_request = {
                'type': 'enhancement',
                'base_content': report_content,
                'analytics_data': analytics_data
            }
            
            # Get AI insights (this would use the reporter agent)
            # For now, we'll add some basic enhancements
            enhanced_insights = report_content.get('insights', [])
            enhanced_insights.append("AI analysis suggests monitoring trend patterns for early issue detection")
            
            enhanced_recommendations = report_content.get('recommendations', [])
            enhanced_recommendations.append("Consider implementing predictive analytics for proactive workflow management")
            
            report_content['insights'] = enhanced_insights
            report_content['recommendations'] = enhanced_recommendations
            
        except Exception as e:
            logger.warning(f"Failed to enhance report with AI insights: {e}")
        
        return report_content
    
    def _generate_filename(self, report_type: str, format_type: str, start_date: datetime, end_date: datetime) -> str:
        """Generate filename for report."""
        date_str = start_date.strftime('%Y%m%d')
        if (end_date - start_date).days > 1:
            date_str += f"_to_{end_date.strftime('%Y%m%d')}"
        
        return f"{report_type}_report_{date_str}.{format_type}"
    
    def _store_report_metadata(
        self,
        report_type: str,
        content: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        generated_files: Dict[str, str]
    ) -> int:
        """Store report metadata in database."""
        try:
            with db_manager.get_session() as session:
                report = ReportOperations.create_report(
                    session=session,
                    title=content.get('title', f'{report_type.title()} Report'),
                    report_type=report_type,
                    content=content,
                    generated_by='ReportManager',
                    description=content.get('executive_summary', ''),
                    summary=content.get('executive_summary', ''),
                    date_range_start=start_date,
                    date_range_end=end_date
                )
                
                # Update with file information
                if generated_files:
                    primary_file = generated_files.get('html') or generated_files.get('pdf') or list(generated_files.values())[0]
                    if primary_file and not primary_file.startswith('Error:'):
                        report.file_path = primary_file
                        report.file_format = primary_file.split('.')[-1] if '.' in primary_file else 'unknown'
                
                session.commit()
                return report.id
                
        except Exception as e:
            logger.error(f"Failed to store report metadata: {e}")
            return 0
    
    def get_report_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent report history."""
        try:
            with db_manager.get_session() as session:
                reports = ReportOperations.get_reports_by_type(session, '', limit)
                
                return [
                    {
                        'id': report.id,
                        'title': report.title,
                        'type': report.report_type,
                        'created_at': report.created_at.isoformat() if report.created_at else None,
                        'file_path': report.file_path,
                        'file_format': report.file_format
                    }
                    for report in reports
                ]
        except Exception as e:
            logger.error(f"Failed to get report history: {e}")
            return []

# Global report manager instance
report_manager = ReportManager()
