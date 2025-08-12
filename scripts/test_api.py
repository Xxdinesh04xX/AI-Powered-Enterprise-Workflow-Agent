"""
API testing script for the AI-Powered Enterprise Workflow Agent.

This script tests the REST API endpoints to ensure they work correctly.
"""

import sys
import time
import requests
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logger import get_logger

logger = get_logger("api_test")

class APITester:
    """API testing class."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "dev-key-123"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health check passed: {data['status']}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def test_api_info(self) -> bool:
        """Test API info endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/info")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ API info retrieved: {data['name']}")
                return True
            else:
                logger.error(f"❌ API info failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ API info error: {e}")
            return False
    
    def test_statistics(self) -> bool:
        """Test statistics endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/v1/statistics", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Statistics retrieved: {data['total_tasks']} total tasks")
                return True
            else:
                logger.error(f"❌ Statistics failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Statistics error: {e}")
            return False
    
    def test_create_task(self) -> dict:
        """Test task creation."""
        try:
            task_data = {
                "title": "Test API Task",
                "description": "This is a test task created via API",
                "original_request": "Create a test task to verify API functionality",
                "category": "IT",
                "priority": "Medium"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/",
                headers=self.headers,
                json=task_data
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Task created: ID {data['id']}")
                return data
            else:
                logger.error(f"❌ Task creation failed: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Task creation error: {e}")
            return {}
    
    def test_get_task(self, task_id: int) -> bool:
        """Test getting a specific task."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Task retrieved: {data['title']}")
                return True
            else:
                logger.error(f"❌ Task retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Task retrieval error: {e}")
            return False
    
    def test_list_tasks(self) -> bool:
        """Test listing tasks."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/",
                headers=self.headers,
                params={"page": 1, "per_page": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Tasks listed: {data['total']} total, {len(data['items'])} returned")
                return True
            else:
                logger.error(f"❌ Task listing failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Task listing error: {e}")
            return False
    
    def test_update_task(self, task_id: int) -> bool:
        """Test updating a task."""
        try:
            update_data = {
                "status": "in_progress",
                "description": "Updated description via API test"
            }
            
            response = requests.put(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers=self.headers,
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Task updated: status = {data['status']}")
                return True
            else:
                logger.error(f"❌ Task update failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Task update error: {e}")
            return False
    
    def test_classify_task(self) -> bool:
        """Test task classification."""
        try:
            classification_data = {
                "text": "The server is down and users cannot access their email",
                "title": "Email Server Issue",
                "strategy": "hybrid"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/classify",
                headers=self.headers,
                json=classification_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Task classified: {data['category']} / {data['priority']} (confidence: {data['confidence']:.2f})")
                return True
            else:
                logger.error(f"❌ Task classification failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Task classification error: {e}")
            return False
    
    def test_assign_task(self, task_id: int) -> bool:
        """Test task assignment."""
        try:
            assignment_data = {
                "task_id": task_id,
                "strategy": "hybrid",
                "force_reassign": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/tasks/{task_id}/assign",
                headers=self.headers,
                json=assignment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Task assigned: team {data['assigned_team_id']} (confidence: {data['confidence']:.2f})")
                return True
            else:
                logger.error(f"❌ Task assignment failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Task assignment error: {e}")
            return False
    
    def test_workflow_processing(self, task_id: int) -> bool:
        """Test workflow processing."""
        try:
            workflow_data = {
                "task_id": task_id,
                "strategy": "hybrid",
                "force_reprocess": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/workflows/process",
                headers=self.headers,
                json=workflow_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Workflow processed: success = {data['success']}")
                return True
            else:
                logger.error(f"❌ Workflow processing failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Workflow processing error: {e}")
            return False
    
    def test_report_generation(self) -> bool:
        """Test report generation."""
        try:
            report_data = {
                "report_type": "daily",
                "output_formats": ["json"],
                "include_analytics": True,
                "use_ai_insights": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/reports/generate",
                headers=self.headers,
                json=report_data
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Report generated: ID {data['report_id']}")
                return True
            else:
                logger.error(f"❌ Report generation failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Report generation error: {e}")
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication with invalid API key."""
        try:
            invalid_headers = {
                "X-API-Key": "invalid-key",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/",
                headers=invalid_headers
            )
            
            if response.status_code == 401:
                logger.info("✅ Authentication properly rejected invalid API key")
                return True
            else:
                logger.error(f"❌ Authentication test failed: expected 401, got {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Authentication test error: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all API tests."""
        logger.info("Starting comprehensive API testing...")
        
        results = {}
        
        # Basic connectivity tests
        results["health_check"] = self.test_health_check()
        results["api_info"] = self.test_api_info()
        results["statistics"] = self.test_statistics()
        
        # Authentication test
        results["authentication"] = self.test_authentication()
        
        # Task management tests
        task_data = self.test_create_task()
        results["create_task"] = bool(task_data)
        
        if task_data:
            task_id = task_data["id"]
            results["get_task"] = self.test_get_task(task_id)
            results["list_tasks"] = self.test_list_tasks()
            results["update_task"] = self.test_update_task(task_id)
            results["assign_task"] = self.test_assign_task(task_id)
            results["workflow_processing"] = self.test_workflow_processing(task_id)
        else:
            results["get_task"] = False
            results["list_tasks"] = False
            results["update_task"] = False
            results["assign_task"] = False
            results["workflow_processing"] = False
        
        # Classification test
        results["classify_task"] = self.test_classify_task()
        
        # Report generation test
        results["report_generation"] = self.test_report_generation()
        
        return results

def wait_for_server(base_url: str, max_wait: int = 30) -> bool:
    """Wait for the API server to be ready."""
    logger.info(f"Waiting for API server at {base_url}...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                logger.info("✅ API server is ready")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            logger.info(f"Still waiting... ({i}/{max_wait})")
    
    logger.error("❌ API server not ready after waiting")
    return False

def main():
    """Main test function."""
    
    base_url = "http://localhost:8000"
    
    # Wait for server to be ready
    if not wait_for_server(base_url):
        print("❌ API server not available")
        return 1
    
    # Run tests
    tester = APITester(base_url)
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("API TEST RESULTS")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if success:
            passed += 1
    
    success_rate = passed / total if total > 0 else 0
    print(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1%})")
    print("="*60)
    
    if success_rate >= 0.8:
        print("\n🎉 API testing successful!")
        return 0
    else:
        print("\n⚠️  Some API tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
