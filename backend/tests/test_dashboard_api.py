import pytest
import requests
import json
import os
from datetime import datetime, timedelta

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestDashboardAPI:
    """Integration tests for Dashboard API endpoints"""
    
    def _create_test_data(self):
        """Helper to create some test data across domains"""
        test_ids = {}
        
        # Create a task
        task_payload = {
            "name": "Dashboard Test Task",
            "frequency": "daily"
        }
        task_response = requests.post(
            f"{API_BASE_URL}/tasks/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(task_payload)
        )
        if task_response.status_code == 201:
            test_ids['task_id'] = task_response.json()['task_id']
        
        # Create a health item
        health_payload = {
            "name": "Dashboard Test Medication"
        }
        health_response = requests.post(
            f"{API_BASE_URL}/health/items",
            headers={"Content-Type": "application/json"},
            data=json.dumps(health_payload)
        )
        if health_response.status_code == 201:
            test_ids['health_id'] = health_response.json()['item_id']
        
        # Create a meal
        meal_payload = {
            "name": "Dashboard Test Meal",
            "delivery_date": "Monday, July 28",
            "recipe_link": "https://test.com"
        }
        meal_response = requests.post(
            f"{API_BASE_URL}/meals/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(meal_payload)
        )
        if meal_response.status_code == 201:
            test_ids['meal_id'] = meal_response.json()['meal_id']
        
        return test_ids
    
    def test_dashboard_today_structure(self):
        """Test the main dashboard endpoint structure"""
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level structure
        assert 'today' in data
        assert 'summary' in data
        assert 'items' in data
        assert 'meals' in data
        
        # Check date format
        today_str = data['today']
        assert len(today_str) == 10  # YYYY-MM-DD format
        datetime.fromisoformat(today_str)  # Should parse without error
        
        # Check summary structure
        summary = data['summary']
        assert 'total_items' in summary
        assert 'completed_today' in summary
        assert 'pending' in summary
        assert 'overdue' in summary
        
        # All summary counts should be non-negative integers
        assert isinstance(summary['total_items'], int)
        assert isinstance(summary['completed_today'], int)
        assert isinstance(summary['pending'], int)
        assert isinstance(summary['overdue'], int)
        assert all(count >= 0 for count in summary.values())
    
    def test_dashboard_items_structure(self):
        """Test dashboard items have correct structure"""
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        items = data['items']
        assert isinstance(items, list)
        
        if items:  # If there are items, check structure
            item = items[0]
            
            # Required fields
            assert 'id' in item
            assert 'type' in item
            assert 'name' in item
            assert 'status' in item
            assert 'category' in item
            
            # Optional fields (can be None)
            assert 'person' in item
            assert 'pet' in item
            assert 'due_time' in item
            assert 'notes' in item
            assert 'last_completed_by' in item
            assert 'last_completed_date' in item
            
            # Validate enum values
            assert item['type'] in ['health', 'task', 'pet_care']
            assert item['status'] in ['pending', 'completed_today', 'overdue']
    
    def test_dashboard_meals_structure(self):
        """Test meals summary structure"""
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        meals = data['meals']
        assert isinstance(meals, dict)
        
        # Check required fields
        assert 'delivered' in meals
        assert 'available_to_cook' in meals
        assert 'cooked_this_week' in meals
        
        # Check types
        assert isinstance(meals['delivered'], list)
        assert isinstance(meals['available_to_cook'], int)
        assert isinstance(meals['cooked_this_week'], int)
        
        # Counts should be non-negative
        assert meals['available_to_cook'] >= 0
        assert meals['cooked_this_week'] >= 0
        
        # available_to_cook should match delivered list length
        assert meals['available_to_cook'] == len(meals['delivered'])
    
    def test_dashboard_aggregates_all_domains(self):
        """Test that dashboard includes items from all domains"""
        # Create test data
        test_ids = self._create_test_data()
        
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        items = data['items']
        item_types = {item['type'] for item in items}
        
        # Should have items from multiple domains
        # (May not have all if no test data exists)
        possible_types = {'health', 'task', 'pet_care'}
        assert item_types.issubset(possible_types)
        
        # If we created test data, it should appear
        if test_ids.get('task_id'):
            task_items = [item for item in items if item['id'] == test_ids['task_id']]
            assert len(task_items) == 1
            assert task_items[0]['type'] == 'task'
            assert task_items[0]['name'] == "Dashboard Test Task"
        
        if test_ids.get('health_id'):
            health_items = [item for item in items if item['id'] == test_ids['health_id']]
            assert len(health_items) == 1
            assert health_items[0]['type'] == 'health'
            assert health_items[0]['name'] == "Dashboard Test Medication"
    
    def test_dashboard_summary_calculations(self):
        """Test that summary calculations are accurate"""
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data['summary']
        items = data['items']
        
        # Calculate expected values from items
        expected_total = len(items)
        expected_completed = len([item for item in items if item['status'] == 'completed_today'])
        expected_overdue = len([item for item in items if item['status'] == 'overdue'])
        expected_pending = expected_total - expected_completed
        
        # Check calculations match
        assert summary['total_items'] == expected_total
        assert summary['completed_today'] == expected_completed
        assert summary['overdue'] == expected_overdue
        assert summary['pending'] == expected_pending
    
    def test_dashboard_item_completion_workflow(self):
        """Test that completed items show correct status"""
        # Create test data
        test_ids = self._create_test_data()
        
        if test_ids.get('task_id'):
            task_id = test_ids['task_id']
            
            # Check initial status
            initial_response = requests.get(f"{API_BASE_URL}/dashboard/today")
            initial_data = initial_response.json()
            
            initial_task = next((item for item in initial_data['items'] if item['id'] == task_id), None)
            if initial_task:
                initial_status = initial_task['status']
                
                # Complete the task
                complete_payload = {
                    "task_id": task_id,
                    "completed_by": "dashboard_test"
                }
                
                complete_response = requests.post(
                    f"{API_BASE_URL}/tasks/complete",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(complete_payload)
                )
                assert complete_response.status_code == 201
                
                # Check updated status
                final_response = requests.get(f"{API_BASE_URL}/dashboard/today")
                final_data = final_response.json()
                
                final_task = next((item for item in final_data['items'] if item['id'] == task_id), None)
                assert final_task is not None
                assert final_task['status'] == 'completed_today'
                assert final_task['last_completed_by'] == "dashboard_test"
    
    def test_dashboard_overdue_endpoint(self):
        """Test the overdue summary endpoint"""
        response = requests.get(f"{API_BASE_URL}/dashboard/overdue")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert 'total_overdue' in data
        assert 'items' in data
        
        # Check types
        assert isinstance(data['total_overdue'], int)
        assert isinstance(data['items'], list)
        assert data['total_overdue'] >= 0
        
        # Check that total matches items length
        assert data['total_overdue'] == len(data['items'])
        
        # If there are overdue items, check structure
        if data['items']:
            item = data['items'][0]
            assert 'type' in item
            assert 'name' in item
            assert item['type'] in ['task']  # Currently only tasks can be overdue
    
    def test_dashboard_trends_endpoint(self):
        """Test the completion trends endpoint"""
        response = requests.get(f"{API_BASE_URL}/dashboard/trends")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert 'period_days' in data
        assert 'trends' in data
        
        # Check types
        assert isinstance(data['period_days'], int)
        assert isinstance(data['trends'], list)
        assert data['period_days'] == 7  # Default
        
        # Should have 7 days of data
        assert len(data['trends']) == 7
        
        # Check trend structure
        if data['trends']:
            trend = data['trends'][0]
            assert 'date' in trend
            assert 'total_completions' in trend
            assert 'health_completions' in trend
            assert 'task_completions' in trend
            assert 'pet_completions' in trend
            
            # Validate date format
            datetime.fromisoformat(trend['date'])
            
            # Check completion counts
            total = trend['total_completions']
            health = trend['health_completions']
            task = trend['task_completions']
            pet = trend['pet_completions']
            
            assert all(isinstance(count, int) and count >= 0 for count in [total, health, task, pet])
            assert total == health + task + pet
    
    def test_dashboard_trends_custom_period(self):
        """Test trends endpoint with custom period"""
        response = requests.get(f"{API_BASE_URL}/dashboard/trends?days=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['period_days'] == 3
        assert len(data['trends']) == 3
    
    def test_dashboard_trends_invalid_period(self):
        """Test trends endpoint with invalid period parameter"""
        # This should handle gracefully - either default to 7 or return error
        response = requests.get(f"{API_BASE_URL}/dashboard/trends?days=invalid")
        
        # Should either work with default or return 400/500
        assert response.status_code in [200, 400, 500]
    
    def test_dashboard_item_sorting(self):
        """Test that dashboard items are sorted by priority"""
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        items = data['items']
        if len(items) > 1:
            # Check sorting: overdue should come first, then pending, then completed
            status_priority = {'overdue': 0, 'pending': 1, 'completed_today': 2}
            
            for i in range(len(items) - 1):
                current_priority = status_priority.get(items[i]['status'], 3)
                next_priority = status_priority.get(items[i + 1]['status'], 3)
                
                # Current item should have equal or higher priority (lower number)
                assert current_priority <= next_priority
    
    def test_dashboard_nonexistent_endpoint(self):
        """Test accessing non-existent dashboard endpoint"""
        response = requests.get(f"{API_BASE_URL}/dashboard/nonexistent")
        
        # API Gateway returns 403 for unconfigured endpoints, not 404
        assert response.status_code == 403
        data = response.json()
        assert 'message' in data  # API Gateway error format
    
    def test_dashboard_with_no_data(self):
        """Test dashboard behavior when no items exist"""
        # This test assumes the dashboard gracefully handles empty data
        response = requests.get(f"{API_BASE_URL}/dashboard/today")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return valid structure even with no data
        assert 'summary' in data
        assert 'items' in data
        assert 'meals' in data
        
        # Summary counts might be 0 but should be valid
        summary = data['summary']
        assert all(isinstance(count, int) and count >= 0 for count in summary.values())