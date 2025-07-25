import pytest
import requests
import json
import os

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestPersonAPI:
    """Integration tests for Person API endpoints"""
    
    def _create_test_person(self, name="TestPerson"):
        """Helper method to create a test person (not a test case)"""
        payload = {"name": name}
        response = requests.post(
            f"{API_BASE_URL}/people",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        assert response.status_code == 201
        return response.json()
    
    def test_create_person(self):
        """Test creating a new person"""
        payload = {"name": "Sarah"}
        response = requests.post(
            f"{API_BASE_URL}/people",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Sarah"
        assert 'person_id' in data
        assert 'household_id' in data
        assert 'created_at' in data
        assert data['is_active'] is True
    
    def test_get_people(self):
        """Test getting all people in household"""
        # First create a test person
        test_person = self._create_test_person("GetPeopleTest")
        
        # Get all people
        response = requests.get(f"{API_BASE_URL}/people")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our test person
        test_people = [person for person in data if person['person_id'] == test_person['person_id']]
        assert len(test_people) == 1
        assert test_people[0]['name'] == "GetPeopleTest"
    
    def test_create_person_health_item(self):
        """Test creating a health item for a specific person"""
        # First create a person
        person = self._create_test_person("HealthTestPerson")
        person_id = person['person_id']
        
        # Create a health item for this person
        payload = {"name": "Morning Medication"}
        response = requests.post(
            f"{API_BASE_URL}/people/{person_id}/health",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "Morning Medication"
        assert data['category'] == 'health'
        assert data['person_id'] == person_id
        assert data['person_name'] == "HealthTestPerson"
        assert 'item_id' in data
    
    def test_get_person_health_items(self):
        """Test getting health items for a specific person"""
        # Create a person and health item
        person = self._create_test_person("PersonHealthGetTest")
        person_id = person['person_id']
        
        # Create health item
        payload = {"name": "Evening Vitamins"}
        create_response = requests.post(
            f"{API_BASE_URL}/people/{person_id}/health",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        item_id = create_response.json()['item_id']
        
        # Get person's health items
        response = requests.get(f"{API_BASE_URL}/people/{person_id}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our health item
        health_items = [item for item in data if item['item_id'] == item_id]
        assert len(health_items) == 1
        assert health_items[0]['name'] == "Evening Vitamins"
        assert health_items[0]['person_id'] == person_id
    
    def test_person_health_isolation(self):
        """Test that health items are isolated per person"""
        # Create two people
        sarah = self._create_test_person("Sarah")
        john = self._create_test_person("John")
        
        # Create health items for each
        sarah_item_payload = {"name": "Sarah's Morning Bupropion"}
        requests.post(
            f"{API_BASE_URL}/people/{sarah['person_id']}/health",
            headers={"Content-Type": "application/json"},
            data=json.dumps(sarah_item_payload)
        )
        
        john_item_payload = {"name": "John's Afternoon Vitamins"}
        requests.post(
            f"{API_BASE_URL}/people/{john['person_id']}/health",
            headers={"Content-Type": "application/json"},
            data=json.dumps(john_item_payload)
        )
        
        # Get Sarah's health items
        sarah_response = requests.get(f"{API_BASE_URL}/people/{sarah['person_id']}/health")
        sarah_items = sarah_response.json()
        
        # Get John's health items
        john_response = requests.get(f"{API_BASE_URL}/people/{john['person_id']}/health")
        john_items = john_response.json()
        
        # Sarah should only see her items
        sarah_item_names = [item['name'] for item in sarah_items]
        assert "Sarah's Morning Bupropion" in sarah_item_names
        assert "John's Afternoon Vitamins" not in sarah_item_names
        
        # John should only see his items
        john_item_names = [item['name'] for item in john_items]
        assert "John's Afternoon Vitamins" in john_item_names
        assert "Sarah's Morning Bupropion" not in john_item_names
    
    def test_create_health_item_for_nonexistent_person(self):
        """Test creating health item for person that doesn't exist"""
        fake_person_id = "nonexistent-person-id"
        payload = {"name": "Should Fail"}
        
        response = requests.post(
            f"{API_BASE_URL}/people/{fake_person_id}/health",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'Person not found' in data['error']
    
    def test_missing_name_returns_400(self):
        """Test that missing name returns 400 error"""
        payload = {}  # Missing name field
        response = requests.post(
            f"{API_BASE_URL}/people",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Missing required field' in data['error']
    
    def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 error"""
        response = requests.post(
            f"{API_BASE_URL}/people",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']