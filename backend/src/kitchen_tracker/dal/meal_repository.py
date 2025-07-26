from typing import List, Optional
from .base_repository import BaseRepository

class MealRepository(BaseRepository):
    """Repository for meal-related operations"""
    
    def create_meal(self, meal) -> bool:
        """Create a new meal"""
        data = meal.to_dict()
        data['record_type'] = 'meal'
        data['user_id'] = meal.household_id
        data['item_id'] = meal.meal_id
        return self.put_item(data)
    
    def get_meal(self, household_id: str, meal_id: str):
        """Get a specific meal by ID"""
        from models.meal import Meal
        
        data = self.get_item(household_id, meal_id)
        if data and data.get('record_type') == 'meal':
            return Meal.from_dict(data)
        return None
    
    def get_household_meals(self, household_id: str, week_of: str = None) -> List:
        """Get meals for a household, optionally filtered by week"""
        from models.meal import Meal
        
        items = self.query_by_user(household_id)
        meals = []
        
        for item_data in items:
            if item_data.get('record_type') == 'meal':
                meal = Meal.from_dict(item_data)
                
                if week_of is None or meal.week_of == week_of:
                    meals.append(meal)
        
        return meals
    
    def update_meal_status(self, household_id: str, meal_id: str, status: str) -> bool:
        """Update meal status (ordered -> delivered -> cooked)"""
        meal = self.get_meal(household_id, meal_id)
        if meal:
            meal.status = status
            return self.create_meal(meal)  # Update existing
        return False
    
    def get_meals_by_week(self, household_id: str, week_of: str) -> List:
        """Get all meals for a specific week"""
        return self.get_household_meals(household_id, week_of)
    
    def create_meal_record(self, meal_record) -> bool:
        """Create a meal cooking record"""
        from models.meal import MealRecord
        
        data = meal_record.to_dict()
        data['record_type'] = 'meal_record'
        data['user_id'] = meal_record.household_id
        data['item_id'] = meal_record.record_id
        # Store original meal_id for queries
        data['original_meal_id'] = data['meal_id']
        data['meal_id'] = meal_record.record_id  # Use record_id as DynamoDB key
        return self.put_item(data)
    
    def get_meal_records(self, household_id: str, meal_id: str = None) -> List:
        """Get meal cooking records, optionally filtered by meal_id"""
        from models.meal import MealRecord
        
        items = self.query_by_user(household_id)
        records = []
        
        for item_data in items:
            if (item_data.get('record_type') == 'meal_record'):
                # Check if filtering by meal_id
                if meal_id is None or item_data.get('original_meal_id') == meal_id:
                    # Restore original structure
                    record_data = item_data.copy()
                    record_data['meal_id'] = record_data.get('original_meal_id', record_data['meal_id'])
                    records.append(MealRecord.from_dict(record_data))
        
        return records