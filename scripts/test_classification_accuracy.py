"""
Classification accuracy testing script.

This script generates test data and validates that the classification
system meets the >90% accuracy target.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.core.classification import EnhancedClassificationSystem, ClassificationStrategy
from src.database.models import TaskCategory, TaskPriority
from src.utils.logger import get_logger

logger = get_logger("classification_test")

def generate_test_dataset():
    """Generate comprehensive test dataset for classification validation."""
    
    test_data = [
        # IT Category - Critical Priority
        {
            "title": "Production Server Outage",
            "description": "The main production server is completely down. All users are unable to access the application. This is causing major business disruption and revenue loss.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.CRITICAL
        },
        {
            "title": "Security Breach Alert",
            "description": "Detected unauthorized access to our database. Immediate action required to secure systems and assess data compromise.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.CRITICAL
        },
        
        # IT Category - High Priority
        {
            "title": "Application Performance Issue",
            "description": "Users are reporting slow response times in the web application. Page load times have increased significantly since yesterday.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.HIGH
        },
        {
            "title": "Email System Problems",
            "description": "Email server is experiencing issues. Some emails are not being delivered and users cannot send messages.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.HIGH
        },
        
        # IT Category - Medium Priority
        {
            "title": "Software Update Request",
            "description": "Please update the CRM software to the latest version. This includes new features and bug fixes.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.MEDIUM
        },
        {
            "title": "Network Configuration",
            "description": "Configure new network settings for the branch office. This needs to be completed by end of week.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.MEDIUM
        },
        
        # IT Category - Low Priority
        {
            "title": "Documentation Update",
            "description": "Update technical documentation for the API. This can be done when time permits.",
            "expected_category": TaskCategory.IT,
            "expected_priority": TaskPriority.LOW
        },
        
        # HR Category - Critical Priority
        {
            "title": "Workplace Safety Incident",
            "description": "Employee injury reported in the warehouse. Need immediate investigation and safety protocol review.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.CRITICAL
        },
        
        # HR Category - High Priority
        {
            "title": "Urgent Recruitment Need",
            "description": "Critical position needs to be filled immediately. The project manager left unexpectedly and we need replacement ASAP.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.HIGH
        },
        {
            "title": "Payroll Discrepancy",
            "description": "Multiple employees reported incorrect salary calculations. Need to investigate and correct before next pay cycle.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.HIGH
        },
        
        # HR Category - Medium Priority
        {
            "title": "Employee Onboarding",
            "description": "New hire starts next Monday. Prepare onboarding materials and schedule orientation sessions.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.MEDIUM
        },
        {
            "title": "Performance Review Process",
            "description": "Initiate quarterly performance reviews for all team members. Schedule meetings and prepare evaluation forms.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.MEDIUM
        },
        
        # HR Category - Low Priority
        {
            "title": "Employee Handbook Update",
            "description": "Review and update employee handbook with new company policies. No immediate deadline.",
            "expected_category": TaskCategory.HR,
            "expected_priority": TaskPriority.LOW
        },
        
        # Operations Category - Critical Priority
        {
            "title": "Supply Chain Disruption",
            "description": "Major supplier has stopped deliveries due to contract dispute. This will halt production immediately.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.CRITICAL
        },
        
        # Operations Category - High Priority
        {
            "title": "Client Contract Renewal",
            "description": "Major client contract expires in 2 weeks. Need to finalize renewal terms urgently to avoid service interruption.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.HIGH
        },
        {
            "title": "Budget Overrun Alert",
            "description": "Project budget has exceeded 90% allocation. Need immediate review and cost control measures.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.HIGH
        },
        
        # Operations Category - Medium Priority
        {
            "title": "Process Optimization",
            "description": "Analyze current workflow processes and identify areas for efficiency improvements.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.MEDIUM
        },
        {
            "title": "Vendor Evaluation",
            "description": "Evaluate new vendors for office supplies contract. Compare pricing and service quality.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.MEDIUM
        },
        
        # Operations Category - Low Priority
        {
            "title": "Office Space Planning",
            "description": "Plan layout for new office space. Consider employee preferences and workflow optimization.",
            "expected_category": TaskCategory.OPERATIONS,
            "expected_priority": TaskPriority.LOW
        },
        
        # Edge Cases and Mixed Scenarios
        {
            "title": "IT-HR System Integration",
            "description": "Integrate the new HR management system with existing IT infrastructure. Requires coordination between IT and HR teams.",
            "expected_category": TaskCategory.IT,  # Technical implementation focus
            "expected_priority": TaskPriority.MEDIUM
        },
        {
            "title": "Operational IT Support",
            "description": "Provide IT support for the new business process implementation. Ensure systems can handle operational requirements.",
            "expected_category": TaskCategory.IT,  # IT support focus
            "expected_priority": TaskPriority.MEDIUM
        }
    ]
    
    return test_data

def test_classification_accuracy():
    """Test classification accuracy across different strategies."""

    logger.info("Starting classification accuracy testing...")

    # Initialize classification system
    classification_system = EnhancedClassificationSystem()

    # Generate test dataset
    test_data = generate_test_dataset()
    logger.info(f"Generated {len(test_data)} test cases")

    # Test only rule-based strategy for now (no API keys required)
    strategies = [
        ClassificationStrategy.RULE_BASED
    ]
    
    results = {}
    
    for strategy in strategies:
        logger.info(f"Testing {strategy.value} strategy...")
        
        correct_category = 0
        correct_priority = 0
        correct_both = 0
        total_tests = len(test_data)
        
        strategy_results = []
        
        for i, test_case in enumerate(test_data):
            try:
                # Perform classification
                result = classification_system.classify(
                    text=test_case["description"],
                    title=test_case["title"],
                    strategy=strategy,
                    task_id=i + 1  # Mock task ID
                )
                
                # Check accuracy
                category_correct = result.category == test_case["expected_category"]
                priority_correct = result.priority == test_case["expected_priority"]
                both_correct = category_correct and priority_correct
                
                if category_correct:
                    correct_category += 1
                if priority_correct:
                    correct_priority += 1
                if both_correct:
                    correct_both += 1
                
                # Store result details
                strategy_results.append({
                    "title": test_case["title"],
                    "predicted_category": result.category.value,
                    "expected_category": test_case["expected_category"].value,
                    "predicted_priority": result.priority.value,
                    "expected_priority": test_case["expected_priority"].value,
                    "confidence": result.confidence,
                    "category_correct": category_correct,
                    "priority_correct": priority_correct,
                    "both_correct": both_correct
                })
                
                # Validate for statistics tracking
                classification_system.validate_classification(
                    result,
                    test_case["expected_category"],
                    test_case["expected_priority"]
                )
                
            except Exception as e:
                logger.error(f"Classification failed for test case {i}: {e}")
                strategy_results.append({
                    "title": test_case["title"],
                    "error": str(e),
                    "category_correct": False,
                    "priority_correct": False,
                    "both_correct": False
                })
        
        # Calculate accuracy metrics
        category_accuracy = correct_category / total_tests
        priority_accuracy = correct_priority / total_tests
        overall_accuracy = correct_both / total_tests
        
        results[strategy.value] = {
            "category_accuracy": category_accuracy,
            "priority_accuracy": priority_accuracy,
            "overall_accuracy": overall_accuracy,
            "total_tests": total_tests,
            "correct_category": correct_category,
            "correct_priority": correct_priority,
            "correct_both": correct_both,
            "details": strategy_results
        }
        
        logger.info(f"{strategy.value} Results:")
        logger.info(f"  Category Accuracy: {category_accuracy:.2%}")
        logger.info(f"  Priority Accuracy: {priority_accuracy:.2%}")
        logger.info(f"  Overall Accuracy: {overall_accuracy:.2%}")
    
    # Get system statistics
    system_stats = classification_system.get_accuracy_statistics()
    
    # Generate report
    report = {
        "test_timestamp": datetime.utcnow().isoformat(),
        "test_dataset_size": len(test_data),
        "strategy_results": results,
        "system_statistics": system_stats,
        "accuracy_target": 0.90,
        "target_met": any(r["overall_accuracy"] >= 0.90 for r in results.values())
    }
    
    # Save report
    report_file = Path("reports/classification_accuracy_report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Classification accuracy report saved to {report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("CLASSIFICATION ACCURACY TEST RESULTS")
    print("="*60)
    
    for strategy, result in results.items():
        print(f"\n{strategy.upper()} STRATEGY:")
        print(f"  Category Accuracy: {result['category_accuracy']:.2%}")
        print(f"  Priority Accuracy: {result['priority_accuracy']:.2%}")
        print(f"  Overall Accuracy:  {result['overall_accuracy']:.2%}")
        
        if result['overall_accuracy'] >= 0.90:
            print(f"  ✅ MEETS 90% ACCURACY TARGET")
        else:
            print(f"  ❌ BELOW 90% ACCURACY TARGET")
    
    print(f"\nTarget Met: {'✅ YES' if report['target_met'] else '❌ NO'}")
    print("="*60)
    
    return report

if __name__ == "__main__":
    try:
        report = test_classification_accuracy()
        
        # Exit with appropriate code
        if report["target_met"]:
            print("\n🎉 Classification system meets the 90% accuracy target!")
            sys.exit(0)
        else:
            print("\n⚠️  Classification system needs improvement to meet 90% accuracy target.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Classification accuracy testing failed: {e}")
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)
