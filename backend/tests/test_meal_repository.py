import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'kitchen_tracker'))

from dal.meal_repository import MealRepository
from models.meal import Meal, MealRecord

class TestMealRepository:
    """Unit tests for MealRepository"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        # Mock the BaseRepository initialization to avoid AWS dependencies
        with patch('dal.meal_repository.BaseRepository.__init__', return_value=None):
            self.repo = MealRepository()
        
        self.household_id = "test-household-123"
        
        # Mock the base repository methods
        self.repo.put_item = Mock(return_value=True)
        self.repo.get_item = Mock()
        self.repo.query_by_user = Mock(return_value=[])
    
    def create_test_meal(self, name="Test Chicken Parmesan") -> Meal:
        """Helper to create a test meal"""
        return Meal(
            name=name,
            household_id=self.household_id,
            week_of="2025-07-21",  # Monday of a test week
            recipe_url="https://homechef.com/test-recipe",
            delivery_date="Thursday, July 24"
        )
    
    def create_test_meal_record(self, meal_id="test-meal-456") -> MealRecord:
        """Helper to create a test meal record"""
        return MealRecord(
            meal_id=meal_id,
            household_id=self.household_id,
            cooked_by="sarah",
            notes="Added extra cheese"
        )

    def test_create_meal_success(self):
        """Test successfully creating a meal"""
        meal = self.create_test_meal()
        
        result = self.repo.create_meal(meal)
        
        assert result is True
        self.repo.put_item.assert_called_once()
        
        # Verify the data structure passed to put_item
        call_args = self.repo.put_item.call_args[0][0]
        assert call_args['record_type'] == 'meal'
        assert call_args['user_id'] == self.household_id
        assert call_args['item_id'] == meal.meal_id
        assert call_args['name'] == "Test Chicken Parmesan"
        assert call_args['week_of'] == "2025-07-21"
    
    def test_get_meal_found(self):
        """Test getting a meal that exists"""
        meal = self.create_test_meal()
        meal_data = meal.to_dict()
        meal_data['record_type'] = 'meal'
        
        self.repo.get_item.return_value = meal_data
        
        result = self.repo.get_meal(self.household_id, meal.meal_id)
        
        assert result is not None
        assert result.name == "Test Chicken Parmesan"
        assert result.household_id == self.household_id
        self.repo.get_item.assert_called_once_with(self.household_id, meal.meal_id)
    
    def test_get_meal_not_found(self):
        """Test getting a meal that doesn't exist"""
        self.repo.get_item.return_value = None
        
        result = self.repo.get_meal(self.household_id, "nonexistent-meal")
        
        assert result is None
    
    def test_get_meal_wrong_record_type(self):
        """Test getting an item that exists but isn't a meal"""
        wrong_data = {
            'record_type': 'pet',  # Not a meal
            'name': 'Fluffy'
        }
        self.repo.get_item.return_value = wrong_data
        
        result = self.repo.get_meal(self.household_id, "some-id")
        
        assert result is None
    
    def test_get_household_meals_all(self):
        """Test getting all meals for a household"""
        meal1_data = self.create_test_meal("Meal 1").to_dict()
        meal1_data['record_type'] = 'meal'
        
        meal2_data = self.create_test_meal("Meal 2").to_dict()
        meal2_data['record_type'] = 'meal'
        
        # Mix in non-meal data
        pet_data = {'record_type': 'pet', 'name': 'Fluffy'}
        
        self.repo.query_by_user.return_value = [meal1_data, pet_data, meal2_data]
        
        result = self.repo.get_household_meals(self.household_id)
        
        assert len(result) == 2
        assert result[0].name == "Meal 1"
        assert result[1].name == "Meal 2"
    
    def test_get_household_meals_filtered_by_week(self):
        """Test getting meals filtered by week_of"""
        # Meals from different weeks
        meal1 = self.create_test_meal("Week 1 Meal")
        meal1.week_of = "2025-07-21"
        meal1_data = meal1.to_dict()
        meal1_data['record_type'] = 'meal'
        
        meal2 = self.create_test_meal("Week 2 Meal") 
        meal2.week_of = "2025-07-28"
        meal2_data = meal2.to_dict()
        meal2_data['record_type'] = 'meal'
        
        self.repo.query_by_user.return_value = [meal1_data, meal2_data]
        
        result = self.repo.get_household_meals(self.household_id, week_of="2025-07-21")
        
        assert len(result) == 1
        assert result[0].name == "Week 1 Meal"
        assert result[0].week_of == "2025-07-21"
    
    def test_update_meal_status_success(self):
        """Test successfully updating meal status"""
        meal = self.create_test_meal()
        meal_data = meal.to_dict()
        meal_data['record_type'] = 'meal'
        
        self.repo.get_item.return_value = meal_data
        
        result = self.repo.update_meal_status(self.household_id, meal.meal_id, "cooked")
        
        assert result is True
        # Should call create_meal to update the record
        self.repo.put_item.assert_called_once()
    
    def test_update_meal_status_meal_not_found(self):
        """Test updating status when meal doesn't exist"""
        self.repo.get_item.return_value = None
        
        result = self.repo.update_meal_status(self.household_id, "nonexistent", "cooked")
        
        assert result is False
        # Should not try to update anything
        self.repo.put_item.assert_not_called()
    
    def test_get_meals_by_week(self):
        """Test getting meals by specific week (convenience method)"""
        week_of = "2025-07-21"
        
        # Mock the get_household_meals method since get_meals_by_week calls it
        with patch.object(self.repo, 'get_household_meals') as mock_get:
            mock_get.return_value = [self.create_test_meal()]
            
            result = self.repo.get_meals_by_week(self.household_id, week_of)
            
            mock_get.assert_called_once_with(self.household_id, week_of)
            assert len(result) == 1
    
    def test_create_meal_record_success(self):
        """Test creating a meal cooking record"""
        meal_record = self.create_test_meal_record()
        
        result = self.repo.create_meal_record(meal_record)
        
        assert result is True
        self.repo.put_item.assert_called_once()
        
        # Verify the data structure
        call_args = self.repo.put_item.call_args[0][0]
        assert call_args['record_type'] == 'meal_record'
        assert call_args['user_id'] == self.household_id
        assert call_args['original_meal_id'] == "test-meal-456"
        assert call_args['meal_id'] == meal_record.record_id  # Should use record_id as DynamoDB key
        assert call_args['cooked_by'] == "sarah"
        assert call_args['notes'] == "Added extra cheese"
    
    def test_get_meal_records_all(self):
        """Test getting all meal records for household"""
        record1_data = self.create_test_meal_record("meal-1").to_dict()
        record1_data['record_type'] = 'meal_record'
        record1_data['original_meal_id'] = "meal-1"
        
        record2_data = self.create_test_meal_record("meal-2").to_dict() 
        record2_data['record_type'] = 'meal_record'
        record2_data['original_meal_id'] = "meal-2"
        
        # Mix in non-meal-record data
        pet_data = {'record_type': 'pet', 'name': 'Fluffy'}
        
        self.repo.query_by_user.return_value = [record1_data, pet_data, record2_data]
        
        result = self.repo.get_meal_records(self.household_id)
        
        assert len(result) == 2
        assert result[0].meal_id == "meal-1"  # Should restore original meal_id
        assert result[1].meal_id == "meal-2"
    
    def test_get_meal_records_filtered_by_meal_id(self):
        """Test getting meal records filtered by specific meal_id"""
        record1_data = self.create_test_meal_record("target-meal").to_dict()
        record1_data['record_type'] = 'meal_record'
        record1_data['original_meal_id'] = "target-meal"
        
        record2_data = self.create_test_meal_record("other-meal").to_dict()
        record2_data['record_type'] = 'meal_record' 
        record2_data['original_meal_id'] = "other-meal"
        
        self.repo.query_by_user.return_value = [record1_data, record2_data]
        
        result = self.repo.get_meal_records(self.household_id, meal_id="target-meal")
        
        assert len(result) == 1
        assert result[0].meal_id == "target-meal"