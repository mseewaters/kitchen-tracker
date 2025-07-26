import pytest
import requests
import json
import os
from datetime import datetime, timedelta

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestTaskAPI:
    """Integration tests for Task API endpoints"""
    
    def _create_test_task(self, name="Test Weekly Task", frequency="weekly", day_of_week=1):
        """Helper method to create a test task"""
        payload = {
            "name": name,
            "frequency": frequency
        }
        
        if frequency == "weekly":
            payload["day_of_week"] = day_of_week
        elif frequency == "monthly":
            payload["day_of_month"] = day_of_week  # Reuse param for simplicity
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        assert response.status_code == 201
        return response.json()
    
    def test_create_weekly_task(self):
        """Test creating a weekly recurring task"""
        payload = {
            "name": "Take out recycling",
            "frequency": "weekly",
            "day_of_week": 1  # Monday
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Take out recycling"
        assert data['frequency'] == "weekly"
        assert data['frequency_config']['day_of_week'] == 1
        assert 'task_id' in data
        assert 'household_id' in data
        assert data['is_active'] is True
    
    def test_create_daily_task(self):
        """Test creating a daily recurring task"""
        payload = {
            "name": "Water plants",
            "frequency": "daily"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Water plants"
        assert data['frequency'] == "daily"
        assert data['frequency_config'] == {}  # No config needed for daily
    
    def test_create_monthly_task(self):
        """Test creating a monthly recurring task"""
        payload = {
            "name": "Pay rent",
            "frequency": "monthly",
            "day_of_month": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Pay rent"
        assert data['frequency'] == "monthly"
        assert data['frequency_config']['day_of_month'] == 1
    
    def test_create_task_missing_name(self):
        """Test error handling when name is missing"""
        payload = {
            "frequency": "weekly"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'name' in data['error']
    
    def test_create_task_invalid_json(self):
        """Test error handling for invalid JSON"""
        response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']
    
    def test_get_all_tasks_with_status(self):
        """Test getting all tasks with their completion status"""
        # Create a test task first
        test_task = self._create_test_task("Status Test Task")
        
        response = requests.get(f"{API_BASE_URL}/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Find our test task
        our_task = next((task for task in data if task['task_id'] == test_task['task_id']), None)
        assert our_task is not None
        assert our_task['name'] == "Status Test Task"
        
        # Should have status fields
        assert 'status' in our_task
        assert 'is_due_today' in our_task
        assert 'is_overdue' in our_task
        assert 'next_due_date' in our_task
        assert 'last_completed_date' in our_task
        assert 'last_completed_by' in our_task
    
    def test_complete_task(self):
        """Test marking a task as completed"""
        # Create a test task
        task = self._create_test_task("Completion Test Task")
        task_id = task['task_id']
        
        # Complete it
        complete_payload = {
            "task_id": task_id,
            "completed_by": "sarah",
            "notes": "Completed as part of test"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(complete_payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['task_id'] == task_id
        assert data['completed_by'] == "sarah"
        assert data['notes'] == "Completed as part of test"
        assert 'record_id' in data
        assert 'completed_date' in data
        assert 'completed_at' in data
    
    def test_complete_task_minimal(self):
        """Test completing task with only required fields"""
        task = self._create_test_task("Minimal Completion Test")
        task_id = task['task_id']
        
        complete_payload = {
            "task_id": task_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(complete_payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['task_id'] == task_id
        assert data['completed_by'] is None
        assert data['notes'] is None
    
    def test_complete_task_missing_task_id(self):
        """Test error when task_id is missing from completion"""
        complete_payload = {
            "completed_by": "sarah"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/tasks/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(complete_payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'task_id' in data['error']
    
    def test_get_tasks_due_today(self):
        """Test getting tasks that are due today"""
        # Create a daily task (should be due today since never completed)
        daily_task = self._create_test_task("Daily Due Today", "daily")
        
        response = requests.get(f"{API_BASE_URL}/tasks/today")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our daily task
        our_tasks = [task for task in data if task['task_id'] == daily_task['task_id']]
        assert len(our_tasks) == 1
        assert our_tasks[0]['is_due_today'] is True
    
    def test_get_overdue_tasks(self):
        """Test getting overdue tasks"""
        response = requests.get(f"{API_BASE_URL}/tasks/overdue")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All returned tasks should be overdue
        for task in data:
            assert task['is_overdue'] is True
    
    def test_get_completed_tasks_today(self):
        """Test getting tasks completed today"""
        # Create and complete a task
        task = self._create_test_task("Completed Today Test")
        task_id = task['task_id']
        
        complete_payload = {
            "task_id": task_id,
            "completed_by": "john",
            "notes": "Completed today test"
        }
        
        complete_response = requests.post(
            f"{API_BASE_URL}/tasks/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(complete_payload)
        )
        assert complete_response.status_code == 201
        
        # Get completed tasks
        response = requests.get(f"{API_BASE_URL}/tasks/completed")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our completed task
        our_completions = [record for record in data if record['task_id'] == task_id]
        assert len(our_completions) == 1
        assert our_completions[0]['completed_by'] == "john"
        assert our_completions[0]['task_name'] == "Completed Today Test"
    
    def test_get_specific_task_by_id(self):
        """Test getting a specific task by ID"""
        task = self._create_test_task("Get By ID Test")
        task_id = task['task_id']
        
        response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['task_id'] == task_id
        assert data['name'] == "Get By ID Test"
        assert 'status' in data  # Should include status information
    
    def test_get_nonexistent_task(self):
        """Test getting a task that doesn't exist"""
        fake_task_id = "nonexistent-task-123"
        
        response = requests.get(f"{API_BASE_URL}/tasks/{fake_task_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_update_task_status_deactivate(self):
        """Test deactivating a task"""
        task = self._create_test_task("Deactivation Test")
        task_id = task['task_id']
        
        # Deactivate the task
        status_payload = {
            "is_active": False
        }
        
        response = requests.put(
            f"{API_BASE_URL}/tasks/{task_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(status_payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_active'] is False
        assert data['task_id'] == task_id
    
    def test_update_task_status_reactivate(self):
        """Test reactivating a deactivated task"""
        task = self._create_test_task("Reactivation Test")
        task_id = task['task_id']
        
        # First deactivate
        deactivate_payload = {"is_active": False}
        deactivate_response = requests.put(
            f"{API_BASE_URL}/tasks/{task_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(deactivate_payload)
        )
        assert deactivate_response.status_code == 200
        
        # Then reactivate
        reactivate_payload = {"is_active": True}
        response = requests.put(
            f"{API_BASE_URL}/tasks/{task_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(reactivate_payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_active'] is True
    
    def test_update_nonexistent_task_status(self):
        """Test updating status of nonexistent task"""
        fake_task_id = "nonexistent-task-456"
        
        status_payload = {
            "is_active": False
        }
        
        response = requests.put(
            f"{API_BASE_URL}/tasks/{fake_task_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(status_payload)
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
    
    def test_task_status_after_completion(self):
        """Test that task status changes after completion"""
        # Create a daily task
        task = self._create_test_task("Status Change Test", "daily")
        task_id = task['task_id']
        
        # Check initial status (should be due today)
        initial_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        initial_data = initial_response.json()
        assert initial_data['status'] in ['due_today', 'overdue']
        
        # Complete the task
        complete_payload = {
            "task_id": task_id,
            "completed_by": "test_user"
        }
        
        complete_response = requests.post(
            f"{API_BASE_URL}/tasks/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(complete_payload)
        )
        assert complete_response.status_code == 201
        
        # Check status after completion
        final_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        final_data = final_response.json()
        assert final_data['status'] == 'completed_today'
        assert final_data['last_completed_by'] == "test_user"
        assert final_data['last_completed_date'] is not None