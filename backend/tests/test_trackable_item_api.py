import pytest
import requests
import json
import os
from datetime import date

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestTrackableItemAPI:
    """Integration tests for TrackableItem API endpoints (Health category)"""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns expected message"""
        response = requests.get(f"{API_BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'kitchen-tracker API is running!'
    
    def test_create_trackable_item(self):
        """Test creating a new trackable item (health category)"""
        payload = {"name": "Test Morning Med"}
        response = requests.post(
            f"{API_BASE_URL}/health/items",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Test Morning Med"
        assert data['category'] == 'health'
        assert 'item_id' in data
        assert 'created_at' in data
        assert data['is_active'] is True
        
        # Return item_id for other tests
        return data['item_id']
    
    def test_get_trackable_items(self):
        """Test getting all trackable items (health category)"""
        # First create an item
        item_id = self.test_create_trackable_item()
        
        # Then get all items
        response = requests.get(f"{API_BASE_URL}/health/items")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our test item
        test_items = [item for item in data if item['item_id'] == item_id]
        assert len(test_items) == 1
        assert test_items[0]['name'] == "Test Morning Med"
    
    def test_complete_trackable_item(self):
        """Test marking a trackable item as complete"""
        # First create an item
        item_id = self.test_create_trackable_item()
        
        # Mark it complete
        payload = {"item_id": item_id}
        response = requests.post(
            f"{API_BASE_URL}/health/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['item_id'] == item_id
        assert 'completed_date' in data
        assert 'completed_at' in data
        assert 'record_id' in data
        
        # Should be today's date
        assert data['completed_date'] == date.today().isoformat()
    
    def test_get_today_completions(self):
        """Test getting today's completions"""
        # First create and complete an item
        item_id = self.test_create_trackable_item()
        
        payload = {"item_id": item_id}
        requests.post(
            f"{API_BASE_URL}/health/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        # Get today's completions
        response = requests.get(f"{API_BASE_URL}/health/today")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our completion
        today_completions = [comp for comp in data if comp['item_id'] == item_id]
        assert len(today_completions) >= 1
        assert today_completions[0]['completed_date'] == date.today().isoformat()
    
    def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 error"""
        response = requests.post(
            f"{API_BASE_URL}/health/items",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']
    
    def test_missing_required_field_returns_400(self):
        """Test that missing required field returns 400 error"""
        payload = {}  # Missing 'name' field
        response = requests.post(
            f"{API_BASE_URL}/health/items",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Missing required field' in data['error']
    
    def test_complete_nonexistent_item(self):
        """Test completing a nonexistent item still succeeds (by design)"""
        payload = {"item_id": "nonexistent-id"}
        response = requests.post(
            f"{API_BASE_URL}/health/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        # Should still create a completion record (system allows this)
        assert response.status_code == 201
        data = response.json()
        assert data['item_id'] == "nonexistent-id"