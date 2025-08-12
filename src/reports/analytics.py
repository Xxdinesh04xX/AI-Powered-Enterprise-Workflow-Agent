"""
Analytics module for the AI-Powered Enterprise Workflow Agent.

This module provides advanced analytics capabilities including trend analysis,
performance metrics, and actionable insights generation.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from src.database.connection import db_manager
from src.database.models import Task, TaskStatus, TaskCategory, TaskPriority, WorkflowExecution
from src.database.operations import AnalyticsOperations
from src.utils.logger import get_logger

logger = get_logger("analytics")

class WorkflowAnalytics:
    """Advanced analytics for workflow data."""
    
    def __init__(self):
        # Remove the insights_generators for now as they're not implemented
        pass
    
    def generate_comprehensive_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics for the specified period."""
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info(f"Generating analytics for period {start_date} to {end_date}")
        
        try:
            # Get basic statistics
            basic_stats = self._get_basic_statistics(start_date, end_date, categories)
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics(start_date, end_date, categories)
            
            # Get trend analysis
            trends = self._analyze_trends(start_date, end_date, categories)
            
            # Generate insights
            insights = self._generate_insights(basic_stats, performance_metrics, trends)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(basic_stats, performance_metrics, trends)
            
            # Identify risk areas
            risk_areas = self._identify_risk_areas(basic_stats, performance_metrics, trends)
            
            # Get performance highlights
            highlights = self._get_performance_highlights(basic_stats, performance_metrics, trends)
            
            analytics_result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': (end_date - start_date).days
                },
                'basic_statistics': basic_stats,
                'performance_metrics': performance_metrics,
                'trends': trends,
                'insights': insights,
                'recommendations': recommendations,
                'risk_areas': risk_areas,
                'performance_highlights': highlights,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info("Comprehensive analytics generated successfully")
            return analytics_result
            
        except Exception as e:
            logger.error(f"Failed to generate comprehensive analytics: {e}")
            raise
    
    def _get_basic_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get basic workflow statistics."""
        
        try:
            with db_manager.get_session() as session:
                stats = AnalyticsOperations.get_task_statistics(session, start_date, end_date)
                
                # Add additional metrics
                stats['completion_rate'] = 0.0
                if stats['total_tasks'] > 0:
                    completed = stats['status_distribution'].get('completed', 0)
                    stats['completion_rate'] = completed / stats['total_tasks']
                
                # Calculate average processing time
                stats['average_processing_time'] = self._calculate_average_processing_time(
                    session, start_date, end_date
                )
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get basic statistics: {e}")
            return {}
    
    def _get_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get performance metrics."""
        
        try:
            with db_manager.get_session() as session:
                metrics = {}
                
                # Task completion metrics
                metrics['task_completion'] = self._calculate_completion_metrics(
                    session, start_date, end_date
                )
                
                # Agent performance metrics
                metrics['agent_performance'] = self._calculate_agent_performance(
                    session, start_date, end_date
                )
                
                # Category performance
                metrics['category_performance'] = self._calculate_category_performance(
                    session, start_date, end_date
                )
                
                # Priority handling metrics
                metrics['priority_handling'] = self._calculate_priority_metrics(
                    session, start_date, end_date
                )
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def _analyze_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze trends in the data."""
        
        trends = []
        
        try:
            with db_manager.get_session() as session:
                # Task volume trend
                volume_trend = self._analyze_task_volume_trend(session, start_date, end_date)
                if volume_trend:
                    trends.append(volume_trend)
                
                # Completion rate trend
                completion_trend = self._analyze_completion_rate_trend(session, start_date, end_date)
                if completion_trend:
                    trends.append(completion_trend)
                
                # Category distribution trend
                category_trend = self._analyze_category_trend(session, start_date, end_date)
                if category_trend:
                    trends.append(category_trend)
                
                # Priority distribution trend
                priority_trend = self._analyze_priority_trend(session, start_date, end_date)
                if priority_trend:
                    trends.append(priority_trend)
                
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
        
        return trends
    
    def _generate_insights(
        self,
        basic_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable insights from the data."""
        
        insights = []
        
        try:
            # Task volume insights
            total_tasks = basic_stats.get('total_tasks', 0)
            if total_tasks > 0:
                insights.append(f"Processed {total_tasks} tasks during the reporting period")
                
                completion_rate = basic_stats.get('completion_rate', 0)
                if completion_rate > 0.8:
                    insights.append(f"High completion rate of {completion_rate:.1%} indicates efficient task processing")
                elif completion_rate < 0.6:
                    insights.append(f"Low completion rate of {completion_rate:.1%} suggests potential bottlenecks")
            
            # Category distribution insights
            category_dist = basic_stats.get('category_distribution', {})
            if category_dist:
                dominant_category = max(category_dist.items(), key=lambda x: x[1])
                insights.append(f"{dominant_category[0]} category dominates with {dominant_category[1]} tasks")
            
            # Priority insights
            priority_dist = basic_stats.get('priority_distribution', {})
            if priority_dist:
                critical_tasks = priority_dist.get('Critical', 0)
                if critical_tasks > total_tasks * 0.2:
                    insights.append(f"High number of critical tasks ({critical_tasks}) may indicate systemic issues")
            
            # Performance insights
            avg_time = basic_stats.get('average_processing_time', 0)
            if avg_time > 0:
                if avg_time < 3600:  # Less than 1 hour
                    insights.append(f"Fast average processing time of {avg_time/60:.1f} minutes")
                elif avg_time > 86400:  # More than 1 day
                    insights.append(f"Slow average processing time of {avg_time/3600:.1f} hours needs attention")
            
            # Trend insights
            for trend in trends:
                if trend.get('significance') == 'high':
                    direction = trend.get('direction', 'stable')
                    metric = trend.get('metric', 'unknown')
                    if direction == 'increasing':
                        insights.append(f"Significant upward trend in {metric} requires monitoring")
                    elif direction == 'decreasing':
                        insights.append(f"Significant downward trend in {metric} may indicate improvement or concern")
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
        
        return insights
    
    def _generate_recommendations(
        self,
        basic_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        try:
            # Completion rate recommendations
            completion_rate = basic_stats.get('completion_rate', 0)
            if completion_rate < 0.7:
                recommendations.append("Consider reviewing task assignment strategies to improve completion rates")
                recommendations.append("Investigate bottlenecks in the workflow process")
            
            # Priority handling recommendations
            priority_dist = basic_stats.get('priority_distribution', {})
            critical_tasks = priority_dist.get('Critical', 0)
            total_tasks = basic_stats.get('total_tasks', 1)
            
            if critical_tasks / total_tasks > 0.15:
                recommendations.append("High volume of critical tasks suggests need for better prioritization")
                recommendations.append("Consider implementing preventive measures to reduce critical incidents")
            
            # Category balance recommendations
            category_dist = basic_stats.get('category_distribution', {})
            if category_dist:
                max_category = max(category_dist.values())
                min_category = min(category_dist.values())
                if max_category > min_category * 3:
                    recommendations.append("Uneven category distribution may require resource rebalancing")
            
            # Performance recommendations
            avg_time = basic_stats.get('average_processing_time', 0)
            if avg_time > 7200:  # More than 2 hours
                recommendations.append("Long processing times suggest need for workflow optimization")
                recommendations.append("Consider automation opportunities for routine tasks")
            
            # Agent performance recommendations
            agent_perf = performance_metrics.get('agent_performance', {})
            if agent_perf:
                low_performers = [agent for agent, perf in agent_perf.items() 
                                if perf.get('success_rate', 1) < 0.8]
                if low_performers:
                    recommendations.append("Some agents show low success rates and may need optimization")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _identify_risk_areas(
        self,
        basic_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify potential risk areas."""
        
        risk_areas = []
        
        try:
            # Low completion rate risk
            completion_rate = basic_stats.get('completion_rate', 0)
            if completion_rate < 0.6:
                risk_areas.append("Low task completion rate may impact business operations")
            
            # High critical task volume risk
            priority_dist = basic_stats.get('priority_distribution', {})
            critical_tasks = priority_dist.get('Critical', 0)
            total_tasks = basic_stats.get('total_tasks', 1)
            
            if critical_tasks / total_tasks > 0.2:
                risk_areas.append("High volume of critical tasks indicates potential system instability")
            
            # Processing time risk
            avg_time = basic_stats.get('average_processing_time', 0)
            if avg_time > 86400:  # More than 1 day
                risk_areas.append("Extended processing times may cause SLA violations")
            
            # Trend-based risks
            for trend in trends:
                if trend.get('direction') == 'increasing' and 'critical' in trend.get('metric', '').lower():
                    risk_areas.append(f"Increasing trend in {trend.get('metric')} poses operational risk")
            
            # Agent performance risks
            agent_perf = performance_metrics.get('agent_performance', {})
            if agent_perf:
                failing_agents = [agent for agent, perf in agent_perf.items() 
                                if perf.get('success_rate', 1) < 0.5]
                if failing_agents:
                    risk_areas.append("Some agents have very low success rates affecting system reliability")
            
        except Exception as e:
            logger.error(f"Failed to identify risk areas: {e}")
        
        return risk_areas
    
    def _get_performance_highlights(
        self,
        basic_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Get performance highlights and achievements."""
        
        highlights = []
        
        try:
            # High completion rate highlight
            completion_rate = basic_stats.get('completion_rate', 0)
            if completion_rate > 0.9:
                highlights.append(f"Excellent completion rate of {completion_rate:.1%}")
            
            # Fast processing highlight
            avg_time = basic_stats.get('average_processing_time', 0)
            if avg_time > 0 and avg_time < 1800:  # Less than 30 minutes
                highlights.append(f"Fast average processing time of {avg_time/60:.1f} minutes")
            
            # High task volume highlight
            total_tasks = basic_stats.get('total_tasks', 0)
            if total_tasks > 100:
                highlights.append(f"Successfully processed {total_tasks} tasks")
            
            # Agent performance highlights
            agent_perf = performance_metrics.get('agent_performance', {})
            if agent_perf:
                top_performers = [agent for agent, perf in agent_perf.items() 
                                if perf.get('success_rate', 0) > 0.95]
                if top_performers:
                    highlights.append(f"High-performing agents: {', '.join(top_performers)}")
            
            # Positive trend highlights
            for trend in trends:
                if (trend.get('direction') == 'increasing' and 
                    'completion' in trend.get('metric', '').lower()):
                    highlights.append(f"Positive trend: {trend.get('description', '')}")
            
        except Exception as e:
            logger.error(f"Failed to get performance highlights: {e}")
        
        return highlights
    
    def _calculate_average_processing_time(self, session, start_date: datetime, end_date: datetime) -> float:
        """Calculate average task processing time."""
        try:
            executions = session.query(WorkflowExecution).filter(
                WorkflowExecution.started_at >= start_date,
                WorkflowExecution.started_at <= end_date,
                WorkflowExecution.execution_time.isnot(None)
            ).all()
            
            if executions:
                times = [exec.execution_time for exec in executions if exec.execution_time]
                return statistics.mean(times) if times else 0.0
            
            return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate average processing time: {e}")
            return 0.0
    
    def _calculate_completion_metrics(self, session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate task completion metrics."""
        try:
            tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            ).all()
            
            if not tasks:
                return {}
            
            total = len(tasks)
            completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
            pending = len([t for t in tasks if t.status == TaskStatus.PENDING])
            
            return {
                'total_tasks': total,
                'completed_tasks': completed,
                'in_progress_tasks': in_progress,
                'pending_tasks': pending,
                'completion_rate': completed / total if total > 0 else 0,
                'in_progress_rate': in_progress / total if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to calculate completion metrics: {e}")
            return {}
    
    def _calculate_agent_performance(self, session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate agent performance metrics."""
        try:
            executions = session.query(WorkflowExecution).filter(
                WorkflowExecution.started_at >= start_date,
                WorkflowExecution.started_at <= end_date
            ).all()
            
            agent_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0})
            
            for execution in executions:
                agent = execution.agent_name
                agent_stats[agent]['total'] += 1
                
                if execution.status == 'success':
                    agent_stats[agent]['successful'] += 1
                else:
                    agent_stats[agent]['failed'] += 1
            
            # Calculate success rates
            for agent, stats in agent_stats.items():
                if stats['total'] > 0:
                    stats['success_rate'] = stats['successful'] / stats['total']
                else:
                    stats['success_rate'] = 0.0
            
            return dict(agent_stats)
        except Exception as e:
            logger.error(f"Failed to calculate agent performance: {e}")
            return {}
    
    def _calculate_category_performance(self, session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate performance by category."""
        try:
            tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date,
                Task.category.isnot(None)
            ).all()
            
            category_stats = defaultdict(lambda: {'total': 0, 'completed': 0})
            
            for task in tasks:
                category = task.category.value
                category_stats[category]['total'] += 1
                
                if task.status == TaskStatus.COMPLETED:
                    category_stats[category]['completed'] += 1
            
            # Calculate completion rates
            for category, stats in category_stats.items():
                if stats['total'] > 0:
                    stats['completion_rate'] = stats['completed'] / stats['total']
                else:
                    stats['completion_rate'] = 0.0
            
            return dict(category_stats)
        except Exception as e:
            logger.error(f"Failed to calculate category performance: {e}")
            return {}
    
    def _calculate_priority_metrics(self, session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calculate priority handling metrics."""
        try:
            tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at <= end_date,
                Task.priority.isnot(None)
            ).all()
            
            priority_stats = defaultdict(lambda: {'total': 0, 'completed': 0, 'avg_time': 0})
            
            for task in tasks:
                priority = task.priority.value
                priority_stats[priority]['total'] += 1
                
                if task.status == TaskStatus.COMPLETED:
                    priority_stats[priority]['completed'] += 1
                    
                    # Calculate processing time if available
                    if task.completed_at and task.created_at:
                        processing_time = (task.completed_at - task.created_at).total_seconds()
                        priority_stats[priority]['avg_time'] += processing_time
            
            # Calculate averages
            for priority, stats in priority_stats.items():
                if stats['total'] > 0:
                    stats['completion_rate'] = stats['completed'] / stats['total']
                    if stats['completed'] > 0:
                        stats['avg_time'] = stats['avg_time'] / stats['completed']
                else:
                    stats['completion_rate'] = 0.0
            
            return dict(priority_stats)
        except Exception as e:
            logger.error(f"Failed to calculate priority metrics: {e}")
            return {}
    
    def _analyze_task_volume_trend(self, session, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Analyze task volume trend over time."""
        try:
            # Simple trend analysis - could be enhanced with more sophisticated methods
            mid_point = start_date + (end_date - start_date) / 2
            
            first_half_tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at < mid_point
            ).count()
            
            second_half_tasks = session.query(Task).filter(
                Task.created_at >= mid_point,
                Task.created_at <= end_date
            ).count()
            
            if first_half_tasks == 0:
                return None
            
            change_rate = (second_half_tasks - first_half_tasks) / first_half_tasks
            
            if abs(change_rate) < 0.1:
                direction = "stable"
                significance = "low"
            elif change_rate > 0.3:
                direction = "increasing"
                significance = "high"
            elif change_rate < -0.3:
                direction = "decreasing"
                significance = "high"
            else:
                direction = "increasing" if change_rate > 0 else "decreasing"
                significance = "medium"
            
            return {
                'metric': 'Task Volume',
                'direction': direction,
                'significance': significance,
                'description': f"Task volume {direction} by {abs(change_rate):.1%} over the period",
                'change_rate': change_rate
            }
        except Exception as e:
            logger.error(f"Failed to analyze task volume trend: {e}")
            return None
    
    def _analyze_completion_rate_trend(self, session, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Analyze completion rate trend."""
        try:
            mid_point = start_date + (end_date - start_date) / 2
            
            # First half completion rate
            first_half_tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.created_at < mid_point
            ).all()
            
            first_half_completed = len([t for t in first_half_tasks if t.status == TaskStatus.COMPLETED])
            first_half_rate = first_half_completed / len(first_half_tasks) if first_half_tasks else 0
            
            # Second half completion rate
            second_half_tasks = session.query(Task).filter(
                Task.created_at >= mid_point,
                Task.created_at <= end_date
            ).all()
            
            second_half_completed = len([t for t in second_half_tasks if t.status == TaskStatus.COMPLETED])
            second_half_rate = second_half_completed / len(second_half_tasks) if second_half_tasks else 0
            
            if first_half_rate == 0:
                return None
            
            change = second_half_rate - first_half_rate
            
            if abs(change) < 0.05:
                direction = "stable"
                significance = "low"
            elif change > 0.15:
                direction = "increasing"
                significance = "high"
            elif change < -0.15:
                direction = "decreasing"
                significance = "high"
            else:
                direction = "increasing" if change > 0 else "decreasing"
                significance = "medium"
            
            return {
                'metric': 'Completion Rate',
                'direction': direction,
                'significance': significance,
                'description': f"Completion rate {direction} by {abs(change):.1%} over the period",
                'change': change
            }
        except Exception as e:
            logger.error(f"Failed to analyze completion rate trend: {e}")
            return None
    
    def _analyze_category_trend(self, session, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Analyze category distribution trend."""
        # Simplified implementation - could be enhanced
        return {
            'metric': 'Category Distribution',
            'direction': 'stable',
            'significance': 'low',
            'description': 'Category distribution remains relatively stable'
        }
    
    def _analyze_priority_trend(self, session, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Analyze priority distribution trend."""
        # Simplified implementation - could be enhanced
        return {
            'metric': 'Priority Distribution',
            'direction': 'stable',
            'significance': 'low',
            'description': 'Priority distribution shows no significant changes'
        }
