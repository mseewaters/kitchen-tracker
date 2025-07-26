import pytest
import requests
import json
import os
from datetime import datetime, timedelta

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestMealRecordAPI:
    """Integration tests for MealRecord API endpoints"""
    
    def _create_test_meal(self, name="Test Chicken Parmesan", delivery_date="Thursday, July 3"):
        """Helper method to create a test meal for cooking tests"""
        payload = {
            "name": name,
            "delivery_date": delivery_date,
            "recipe_link": "https://click.e.homechef.com/test-recipe-link",
            "source": "home_chef_email"
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        assert response.status_code == 201
        return response.json()
    
    def test_record_meal_cooking(self):
        """Test recording when a meal is cooked"""
        # First create a meal
        meal = self._create_test_meal("Cooking Test Meal")
        meal_id = meal['meal_id']
        
        # Record cooking it
        cook_payload = {
            "meal_id": meal_id,
            "cooked_by": "sarah",
            "notes": "Added extra cheese, kids loved it!"
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['meal_id'] == meal_id
        assert data['cooked_by'] == "sarah"
        assert data['notes'] == "Added extra cheese, kids loved it!"
        assert 'record_id' in data
        assert 'cooked_date' in data
        assert 'cooked_at' in data
    
    def test_record_meal_cooking_minimal(self):
        """Test recording meal cooking with minimal data"""
        # Create a meal
        meal = self._create_test_meal("Minimal Cooking Test")
        meal_id = meal['meal_id']
        
        # Record cooking with just meal_id
        cook_payload = {
            "meal_id": meal_id
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['meal_id'] == meal_id
        assert data['cooked_by'] is None  # Optional field
        assert data['notes'] is None  # Optional field
    
    def test_record_meal_cooking_updates_status(self):
        """Test that cooking a meal updates its status to 'cooked'"""
        # Create a meal
        meal = self._create_test_meal("Status Update Test")
        meal_id = meal['meal_id']
        
        # Verify initial status is 'delivered'
        assert meal['status'] == 'delivered'
        
        # Cook the meal
        cook_payload = {
            "meal_id": meal_id,
            "cooked_by": "john"
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        assert response.status_code == 201
        
        # Check that meal status was updated
        meal_response = requests.get(f"{API_BASE_URL}/meals/{meal_id}")
        assert meal_response.status_code == 200
        updated_meal = meal_response.json()
        assert updated_meal['status'] == 'cooked'
    
    def test_get_specific_meal_by_id(self):
        """Test getting a specific meal by ID"""
        # Create a meal
        meal = self._create_test_meal("Get By ID Test")
        meal_id = meal['meal_id']
        
        # Get the meal by ID
        response = requests.get(f"{API_BASE_URL}/meals/{meal_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['meal_id'] == meal_id
        assert data['name'] == "Get By ID Test"
        assert 'household_id' in data
        assert 'week_of' in data
    
    def test_get_nonexistent_meal(self):
        """Test getting a meal that doesn't exist"""
        fake_meal_id = "nonexistent-meal-123"
        
        response = requests.get(f"{API_BASE_URL}/meals/{fake_meal_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_update_meal_status(self):
        """Test updating meal status directly"""
        # Create a meal
        meal = self._create_test_meal("Status Update Direct Test")
        meal_id = meal['meal_id']
        
        # Update status to cooked
        status_payload = {
            "status": "cooked"
        }
        response = requests.put(
            f"{API_BASE_URL}/meals/{meal_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(status_payload)
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'cooked'
        assert data['meal_id'] == meal_id
    
    def test_update_nonexistent_meal_status(self):
        """Test updating status of nonexistent meal"""
        fake_meal_id = "nonexistent-meal-456"
        
        status_payload = {
            "status": "cooked"
        }
        response = requests.put(
            f"{API_BASE_URL}/meals/{fake_meal_id}/status",
            headers={"Content-Type": "application/json"},
            data=json.dumps(status_payload)
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
    
    def test_get_all_cooking_records(self):
        """Test getting all cooking records for household"""
        # Create and cook a meal
        meal = self._create_test_meal("All Records Test")
        meal_id = meal['meal_id']
        
        cook_payload = {
            "meal_id": meal_id,
            "cooked_by": "sarah",
            "notes": "Test cooking record"
        }
        cook_response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        assert cook_response.status_code == 201
        
        # Get all cooking records
        response = requests.get(f"{API_BASE_URL}/meals/records")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our cooking record
        our_records = [record for record in data if record['meal_id'] == meal_id]
        assert len(our_records) == 1
        assert our_records[0]['cooked_by'] == "sarah"
        assert our_records[0]['notes'] == "Test cooking record"
    
    def test_get_cooking_records_for_specific_meal(self):
        """Test getting cooking records filtered by meal_id"""
        # Create and cook a meal
        meal = self._create_test_meal("Specific Meal Records Test")
        meal_id = meal['meal_id']
        
        cook_payload = {
            "meal_id": meal_id,
            "cooked_by": "john",
            "notes": "Specific meal test"
        }
        cook_response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        assert cook_response.status_code == 201
        
        # Get records for this specific meal
        response = requests.get(f"{API_BASE_URL}/meals/records?meal_id={meal_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All records should be for our meal
        for record in data:
            assert record['meal_id'] == meal_id
        
        # Should contain our cooking record
        assert len(data) >= 1
        our_record = data[0]  # Should be our record since we filtered
        assert our_record['cooked_by'] == "john"
        assert our_record['notes'] == "Specific meal test"
    
    def test_cook_meal_missing_meal_id(self):
        """Test error handling when meal_id is missing"""
        cook_payload = {
            "cooked_by": "sarah"
            # Missing meal_id
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'meal_id' in data['error']
    
    def test_cook_nonexistent_meal(self):
        """Test cooking a meal that doesn't exist"""
        cook_payload = {
            "meal_id": "nonexistent-meal-789",
            "cooked_by": "sarah"
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(cook_payload)
        )
        
        # Should still create the record even if meal doesn't exist
        # (This is current behavior - could be changed to validate meal exists)
        assert response.status_code == 201
        data = response.json()
        assert data['meal_id'] == "nonexistent-meal-789"
    
    def test_cook_meal_invalid_json(self):
        """Test error handling for invalid JSON"""
        response = requests.post(
            f"{API_BASE_URL}/meals/cook",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']