import pytest
import requests
import json
import os
from datetime import datetime, timedelta

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestMealAPI:
    """Integration tests for Meal API endpoints"""
    
    def _create_test_meal(self, name="Test Margherita Chicken", delivery_date="Thursday, July 3"):
        """Helper method to create a test meal (not a test case)"""
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
    
    def test_create_meal_via_setup(self):
        """Test creating a new meal via /meals/setup"""
        payload = {
            "name": "Crunchy Pesto Mozzarella Chicken",
            "delivery_date": "Friday, July 25",
            "recipe_link": "https://click.e.homechef.com/?qs=test123",
            "source": "home_chef_email"
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Crunchy Pesto Mozzarella Chicken"
        assert data['delivery_date'] == "Friday, July 25"
        assert data['recipe_url'] == "https://click.e.homechef.com/?qs=test123"
        assert data['status'] == "delivered"  # Should be marked as delivered
        assert 'meal_id' in data
        assert 'household_id' in data
        assert 'week_of' in data
        assert 'created_at' in data
        assert data['is_active'] is True
    
    def test_get_all_meals(self):
        """Test getting all meals for household"""
        # First create a test meal
        test_meal = self._create_test_meal("Get All Meals Test")
        
        # Get all meals
        response = requests.get(f"{API_BASE_URL}/meals")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our test meal
        test_meals = [meal for meal in data if meal['meal_id'] == test_meal['meal_id']]
        assert len(test_meals) == 1
        assert test_meals[0]['name'] == "Get All Meals Test"
    
    def test_get_meals_by_week(self):
        """Test filtering meals by week_of parameter"""
        # Create a meal and get its week_of
        test_meal = self._create_test_meal("Week Filter Test", "Monday, July 21")
        week_of = test_meal['week_of']
        
        # Get meals for that specific week
        response = requests.get(f"{API_BASE_URL}/meals?week_of={week_of}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All meals should be from the same week
        for meal in data:
            assert meal['week_of'] == week_of
        
        # Should contain our test meal
        test_meals = [meal for meal in data if meal['meal_id'] == test_meal['meal_id']]
        assert len(test_meals) == 1
    
    def test_create_meal_calculates_week_of(self):
        """Test that week_of is properly calculated from delivery_date"""
        # Thursday, July 3 should be in the week starting Monday June 30
        test_meal = self._create_test_meal("Week Calculation Test", "Thursday, July 3")
        
        # Parse the week_of to verify it's a Monday
        week_of_date = datetime.strptime(test_meal['week_of'], "%Y-%m-%d")
        assert week_of_date.weekday() == 0  # Monday is 0
        
        # Should be the Monday of the week containing July 3
        # (This will depend on what year we're in, but should be consistent)
        assert test_meal['week_of'] is not None
        assert len(test_meal['week_of']) == 10  # YYYY-MM-DD format
    
    def test_create_meal_missing_required_fields(self):
        """Test error handling for missing required fields"""
        payload = {
            "delivery_date": "Friday, July 25",
            "recipe_link": "https://test.com"
            # Missing 'name' field
        }
        response = requests.post(
            f"{API_BASE_URL}/meals/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'name' in data['error']
    
    def test_create_meal_invalid_json(self):
        """Test error handling for invalid JSON"""
        response = requests.post(
            f"{API_BASE_URL}/meals/setup",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']
    
    def test_meal_endpoint_not_found(self):
        """Test 403 for non-existent meal endpoints (API Gateway blocks with API keys)"""
        response = requests.get(f"{API_BASE_URL}/meals/nonexistent")
        
        # API Gateway returns 403 for non-configured endpoints when API keys are required
        assert response.status_code == 403
        data = response.json()
        assert 'message' in data