import pytest
import requests
import json
import os
from datetime import date

# Get API URL from environment or set manually
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

class TestPetAPI:
    """Integration tests for Pet API endpoints"""
    
    def _setup_test_dog(self, pet_name="TestFluffy"):
        """Helper method to create a test dog (not a test case)"""
        payload = {"pet_name": pet_name, "pet_type": "dog"}
        response = requests.post(
            f"{API_BASE_URL}/pets/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        assert response.status_code == 201
        data = response.json()
        return data['pet']['pet_id'], data['care_items']
    
    def test_setup_dog_pet(self):
        """Test setting up a dog with all care items"""
        payload = {"pet_name": "TestFluffy", "pet_type": "dog"}
        response = requests.post(
            f"{API_BASE_URL}/pets/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['pet']['name'] == "TestFluffy"
        assert data['pet']['pet_type'] == 'dog'
        assert 'pet_id' in data['pet']
        
        # Should create care items
        care_items = data['care_items']
        assert len(care_items) >= 4  # feeding, treat, flea_treatment, heartworm, bath
        
        # Check for dog-specific items
        care_types = [item['care_type'] for item in care_items]
        assert 'feeding' in care_types
        assert 'treat' in care_types
        assert 'flea_treatment' in care_types
        assert 'heartworm' in care_types  # Dog-specific
        assert 'bath' in care_types      # Dog-specific
    
    def test_setup_cat_pet(self):
        """Test setting up a cat (no heartworm or bath)"""
        payload = {"pet_name": "TestWhiskers", "pet_type": "cat"}
        response = requests.post(
            f"{API_BASE_URL}/pets/setup",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['pet']['name'] == "TestWhiskers"
        assert data['pet']['pet_type'] == 'cat'
        
        # Should create fewer care items than dog
        care_items = data['care_items']
        care_types = [item['care_type'] for item in care_items]
        
        # Cat should have these
        assert 'feeding' in care_types
        assert 'treat' in care_types
        assert 'flea_treatment' in care_types
        
        # Cat should NOT have these
        assert 'heartworm' not in care_types
        assert 'bath' not in care_types
    
    def test_get_pets(self):
        """Test getting all pets and their care items"""
        # First create a test pet using helper method
        pet_id, care_items = self._setup_test_dog("GetPetsTestDog")
        
        # Get all pets
        response = requests.get(f"{API_BASE_URL}/pets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should contain our test pet
        test_pets = [pet for pet in data if pet['pet_id'] == pet_id]
        assert len(test_pets) == 1
        
        test_pet = test_pets[0]
        assert test_pet['name'] == "GetPetsTestDog"
        assert test_pet['pet_type'] == 'dog'
        assert 'care_items' in test_pet
        assert len(test_pet['care_items']) >= 4
    
    def test_complete_pet_care(self):
        """Test marking pet care as completed"""
        # First create a pet and get a care item using helper method
        pet_id, care_items = self._setup_test_dog("CompleteTestDog")
        feeding_item = next((item for item in care_items if item['care_type'] == 'feeding'), None)
        assert feeding_item is not None
        
        # Mark feeding as complete
        payload = {
            "item_id": feeding_item['item_id'],
            "pet_id": pet_id,
            "notes": "Test feeding completion"
        }
        response = requests.post(
            f"{API_BASE_URL}/pets/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['item_id'] == feeding_item['item_id']
        assert data['pet_id'] == pet_id
        assert data['notes'] == "Test feeding completion"
        assert data['completed_date'] == date.today().isoformat()
        assert 'record_id' in data
    
    def test_get_today_pet_completions(self):
        """Test getting today's pet care completions"""
        # First create a pet and complete care using helper method
        pet_id, care_items = self._setup_test_dog("TodayTestDog")
        treat_item = next((item for item in care_items if item['care_type'] == 'treat'), None)
        
        # Complete the treat
        payload = {
            "item_id": treat_item['item_id'],
            "pet_id": pet_id,
            "notes": "second treat - overweight pet tracking"
        }
        completion_response = requests.post(
            f"{API_BASE_URL}/pets/complete",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        print(f"DEBUG: Completion response: {completion_response.json()}")
        
        # Get today's completions
        response = requests.get(f"{API_BASE_URL}/pets/today")
        data = response.json()
        print(f"DEBUG: Today's completions: {data}")
        
        assert response.status_code == 200
        assert isinstance(data, list)
        
        # Should contain our completion
        today_completions = [comp for comp in data if comp['pet_id'] == pet_id]
        assert len(today_completions) >= 1
        
        treat_completion = next((comp for comp in today_completions 
                               if comp['item_id'] == treat_item['item_id']), None)
        print(f"DEBUG: Looking for item_id: {treat_item['item_id']}")
        print(f"DEBUG: Found completion: {treat_completion}")
        assert treat_completion is not None
        assert treat_completion['notes'] == "second treat - overweight pet tracking"
        assert 'pet_name' in treat_completion
    
    def test_missing_pet_name_returns_400(self):
        """Test that missing pet_name returns 400 error"""
        payload = {"pet_type": "dog"}  # Missing pet_name
        response = requests.post(
            f"{API_BASE_URL}/pets/setup",
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
            f"{API_BASE_URL}/pets/setup",
            headers={"Content-Type": "application/json"},
            data="invalid json"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'Invalid JSON' in data['error']