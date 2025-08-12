"""
Report generation testing script.

This script tests the report generation system and validates
that comprehensive reports are generated with analytics and insights.
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.reports.manager import ReportManager
from src.reports.generators import ReportGeneratorFactory
from src.reports.analytics import WorkflowAnalytics
from src.database.connection import init_database
from src.database.models import Task, TaskCategory, TaskPriority, TaskStatus
from src.database.operations import TaskOperations
from src.database.connection import db_manager
from src.utils.logger import get_logger

logger = get_logger("report_test")

def create_sample_tasks():
    """Create sample tasks for report testing."""
    
    logger.info("Creating sample tasks for report testing...")
    
    sample_tasks = [
        {
            "title": "Fix Production Database Issue",
            "description": "Critical database performance issue affecting all users",
            "original_request": "The production database is running extremely slow and users cannot access their data",
            "category": TaskCategory.IT,
            "priority": TaskPriority.CRITICAL,
            "status": TaskStatus.COMPLETED
        },
        {
            "title": "Onboard New Developer",
            "description": "Prepare onboarding materials for new team member",
            "original_request": "New developer John Smith starts Monday, need to prepare his onboarding",
            "category": TaskCategory.HR,
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.COMPLETED
        },
        {
            "title": "Update Security Policies",
            "description": "Review and update company security policies",
            "original_request": "Annual security policy review is due this month",
            "category": TaskCategory.IT,
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.IN_PROGRESS
        },
        {
            "title": "Process Payroll",
            "description": "Monthly payroll processing for all employees",
            "original_request": "Need to process payroll for this month",
            "category": TaskCategory.HR,
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.COMPLETED
        },
        {
            "title": "Vendor Contract Review",
            "description": "Review and negotiate vendor contracts for next year",
            "original_request": "Several vendor contracts are up for renewal",
            "category": TaskCategory.OPERATIONS,
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.PENDING
        },
        {
            "title": "Network Maintenance",
            "description": "Scheduled network maintenance and updates",
            "original_request": "Monthly network maintenance window",
            "category": TaskCategory.IT,
            "priority": TaskPriority.LOW,
            "status": TaskStatus.COMPLETED
        },
        {
            "title": "Employee Training Session",
            "description": "Conduct training session on new software tools",
            "original_request": "Team needs training on the new project management software",
            "category": TaskCategory.HR,
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.IN_PROGRESS
        },
        {
            "title": "Budget Planning Meeting",
            "description": "Quarterly budget planning and review meeting",
            "original_request": "Schedule budget planning meeting for Q4",
            "category": TaskCategory.OPERATIONS,
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.COMPLETED
        }
    ]
    
    created_tasks = []
    
    try:
        with db_manager.get_session() as session:
            for task_data in sample_tasks:
                task = Task(
                    title=task_data["title"],
                    description=task_data["description"],
                    original_request=task_data["original_request"],
                    category=task_data["category"],
                    priority=task_data["priority"],
                    status=task_data["status"],
                    created_at=datetime.utcnow() - timedelta(days=7),  # Created a week ago
                    completed_at=datetime.utcnow() - timedelta(days=1) if task_data["status"] == TaskStatus.COMPLETED else None
                )
                session.add(task)
                session.flush()
                created_tasks.append(task.id)
            
            session.commit()
            
        logger.info(f"Created {len(created_tasks)} sample tasks")
        return created_tasks
        
    except Exception as e:
        logger.error(f"Failed to create sample tasks: {e}")
        return []

def test_analytics_generation():
    """Test analytics generation."""
    
    logger.info("Testing analytics generation...")
    
    try:
        analytics = WorkflowAnalytics()
        
        # Generate analytics for the last week
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        analytics_data = analytics.generate_comprehensive_analytics(start_date, end_date)
        
        # Validate analytics data
        required_keys = ['basic_statistics', 'performance_metrics', 'trends', 'insights', 'recommendations']
        missing_keys = [key for key in required_keys if key not in analytics_data]
        
        if missing_keys:
            logger.error(f"Missing analytics keys: {missing_keys}")
            return False
        
        # Check basic statistics
        basic_stats = analytics_data['basic_statistics']
        if 'total_tasks' not in basic_stats:
            logger.error("Missing total_tasks in basic statistics")
            return False
        
        logger.info(f"Analytics generated successfully:")
        logger.info(f"  Total tasks: {basic_stats.get('total_tasks', 0)}")
        logger.info(f"  Completion rate: {basic_stats.get('completion_rate', 0):.1%}")
        logger.info(f"  Insights count: {len(analytics_data.get('insights', []))}")
        logger.info(f"  Recommendations count: {len(analytics_data.get('recommendations', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        return False

def test_report_generators():
    """Test different report generators."""
    
    logger.info("Testing report generators...")
    
    # Sample report data
    sample_data = {
        'title': 'Test Report',
        'executive_summary': 'This is a test report to validate the report generation system.',
        'key_metrics': {
            'total_tasks': 10,
            'completion_rate': '80%',
            'status_distribution': {'completed': 8, 'pending': 2},
            'category_distribution': {'IT': 5, 'HR': 3, 'Operations': 2}
        },
        'insights': [
            'High completion rate indicates efficient processing',
            'IT category dominates the workload',
            'No critical issues identified'
        ],
        'recommendations': [
            'Continue current workflow processes',
            'Monitor IT workload for potential bottlenecks',
            'Consider cross-training for better load distribution'
        ],
        'trends': [
            {
                'metric': 'Task Volume',
                'direction': 'stable',
                'significance': 'low',
                'description': 'Task volume remains consistent'
            }
        ],
        'risk_areas': [],
        'performance_highlights': [
            'Excellent completion rate of 80%',
            'Fast average processing time'
        ]
    }
    
    results = {}
    
    # Test each format
    formats = ['json', 'html', 'pdf']
    
    for format_type in formats:
        try:
            generator = ReportGeneratorFactory.create_generator(format_type)
            filename = f"test_report_{format_type}"
            file_path = generator.generate(sample_data, filename)
            
            # Check if file was created
            if Path(file_path).exists():
                results[format_type] = {'success': True, 'file_path': file_path}
                logger.info(f"✅ {format_type.upper()} report generated: {file_path}")
            else:
                results[format_type] = {'success': False, 'error': 'File not created'}
                logger.error(f"❌ {format_type.upper()} report file not found")
                
        except Exception as e:
            results[format_type] = {'success': False, 'error': str(e)}
            logger.error(f"❌ {format_type.upper()} report generation failed: {e}")
    
    return results

def test_comprehensive_report_generation():
    """Test comprehensive report generation using ReportManager."""
    
    logger.info("Testing comprehensive report generation...")
    
    try:
        report_manager = ReportManager()
        
        # Test different report types
        report_types = ['daily', 'weekly', 'monthly', 'performance']
        results = {}
        
        for report_type in report_types:
            try:
                logger.info(f"Generating {report_type} report...")
                
                result = report_manager.generate_report(
                    report_type=report_type,
                    output_formats=['html', 'json'],
                    include_analytics=True,
                    use_ai_insights=False  # Disable AI insights for testing
                )
                
                # Validate result
                if result.get('report_id') and result.get('generated_files'):
                    results[report_type] = {
                        'success': True,
                        'report_id': result['report_id'],
                        'files': result['generated_files']
                    }
                    logger.info(f"✅ {report_type} report generated successfully")
                else:
                    results[report_type] = {'success': False, 'error': 'Invalid result structure'}
                    logger.error(f"❌ {report_type} report generation returned invalid result")
                    
            except Exception as e:
                results[report_type] = {'success': False, 'error': str(e)}
                logger.error(f"❌ {report_type} report generation failed: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive report generation test failed: {e}")
        return {}

def main():
    """Main test function."""
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Create sample tasks
        task_ids = create_sample_tasks()
        if not task_ids:
            logger.warning("No sample tasks created, but continuing with tests")
        
        # Test analytics generation
        analytics_success = test_analytics_generation()
        
        # Test report generators
        generator_results = test_report_generators()
        
        # Test comprehensive report generation
        comprehensive_results = test_comprehensive_report_generation()
        
        # Print summary
        print("\n" + "="*60)
        print("REPORT GENERATION TEST RESULTS")
        print("="*60)
        
        print(f"\nSample Tasks Created: {len(task_ids)}")
        print(f"Analytics Generation: {'✅ PASS' if analytics_success else '❌ FAIL'}")
        
        print(f"\nReport Generators:")
        for format_type, result in generator_results.items():
            status = '✅ PASS' if result['success'] else '❌ FAIL'
            print(f"  {format_type.upper()}: {status}")
        
        print(f"\nComprehensive Reports:")
        for report_type, result in comprehensive_results.items():
            status = '✅ PASS' if result['success'] else '❌ FAIL'
            print(f"  {report_type.title()}: {status}")
        
        # Calculate overall success
        generator_success = all(r['success'] for r in generator_results.values())
        comprehensive_success = all(r['success'] for r in comprehensive_results.values())
        overall_success = analytics_success and generator_success and comprehensive_success
        
        print(f"\nOverall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print("="*60)
        
        if overall_success:
            print("\n🎉 All report generation tests passed!")
            return 0
        else:
            print("\n⚠️  Some report generation tests failed.")
            return 1
            
    except Exception as e:
        logger.error(f"Report generation testing failed: {e}")
        print(f"\n❌ Testing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
