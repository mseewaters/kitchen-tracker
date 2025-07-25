import uuid
from datetime import datetime, date
from typing import Optional

class Meal:
    def __init__(
        self,
        name: str,
        household_id: str,
        week_of: str,  # YYYY-MM-DD format (Monday of delivery week)
        recipe_url: str = None,
        delivery_date: str = None,
        meal_id: str = None
    ):
        self.meal_id = meal_id or str(uuid.uuid4())
        self.name = name  # "Bacon Cheeseburger Flatbreads", "Creamy Tuscan Chicken"
        self.household_id = household_id
        self.week_of = week_of
        self.recipe_url = recipe_url  # Home Chef online recipe link
        self.delivery_date = delivery_date
        self.status = "ordered"  # ordered -> delivered -> cooked
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def mark_delivered(self, delivery_date: str = None):
        """Mark meal as delivered"""
        self.status = "delivered"
        if delivery_date:
            self.delivery_date = delivery_date
    
    def mark_cooked(self):
        """Mark meal as cooked (removes from active inventory)"""
        self.status = "cooked"
    
    def to_dict(self) -> dict:
        return {
            'meal_id': self.meal_id,
            'name': self.name,
            'household_id': self.household_id,
            'week_of': self.week_of,
            'recipe_url': self.recipe_url,
            'delivery_date': self.delivery_date,
            'status': self.status,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Meal':
        meal = cls(
            name=data['name'],
            household_id=data['household_id'],
            week_of=data['week_of'],
            recipe_url=data.get('recipe_url'),
            delivery_date=data.get('delivery_date'),
            meal_id=data.get('meal_id')
        )
        if 'status' in data:
            meal.status = data['status']
        if 'created_at' in data:
            meal.created_at = data['created_at']
        if 'is_active' in data:
            meal.is_active = data['is_active']
        return meal


class MealRecord:
    """Records when a meal was cooked"""
    def __init__(
        self,
        meal_id: str,
        household_id: str,
        cooked_by: str = None,  # user_id of who cooked it
        cooked_date: str = None,
        cooked_at: str = None,
        notes: str = None,  # "made substitutions", "kids loved it", etc.
        record_id: str = None
    ):
        self.record_id = record_id or str(uuid.uuid4())
        self.meal_id = meal_id
        self.household_id = household_id
        self.cooked_by = cooked_by
        self.cooked_date = cooked_date or date.today().isoformat()
        self.cooked_at = cooked_at or datetime.utcnow().isoformat()
        self.notes = notes
    
    def to_dict(self) -> dict:
        return {
            'record_id': self.record_id,
            'meal_id': self.meal_id,
            'household_id': self.household_id,
            'cooked_by': self.cooked_by,
            'cooked_date': self.cooked_date,
            'cooked_at': self.cooked_at,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MealRecord':
        return cls(
            meal_id=data['meal_id'],
            household_id=data['household_id'],
            cooked_by=data.get('cooked_by'),
            cooked_date=data.get('cooked_date'),
            cooked_at=data.get('cooked_at'),
            notes=data.get('notes'),
            record_id=data.get('record_id')
        )


class WeeklyMealPlan:
    """Groups meals by delivery week for easy viewing"""
    def __init__(
        self,
        week_of: str,  # YYYY-MM-DD format (Monday of week)
        household_id: str,
        meals: list = None,
        plan_id: str = None
    ):
        self.plan_id = plan_id or str(uuid.uuid4())
        self.week_of = week_of
        self.household_id = household_id
        self.meals = meals or []  # List of Meal objects
        self.created_at = datetime.utcnow().isoformat()
    
    def add_meal(self, meal: Meal):
        """Add a meal to this week's plan"""
        self.meals.append(meal)
    
    def get_available_meals(self) -> list:
        """Get meals that are delivered but not yet cooked"""
        return [meal for meal in self.meals if meal.status == "delivered"]
    
    def to_dict(self) -> dict:
        return {
            'plan_id': self.plan_id,
            'week_of': self.week_of,
            'household_id': self.household_id,
            'meals': [meal.to_dict() for meal in self.meals],
            'created_at': self.created_at
        }