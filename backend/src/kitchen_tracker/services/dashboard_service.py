from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from models.dashboard import (
    DashboardResponse, DashboardItem, MealSummary,
    create_dashboard_item_from_health,
    create_dashboard_item_from_task,
    create_dashboard_item_from_pet_care,
    determine_item_status
)

class DashboardService:
    """Service to aggregate data from all domains for unified dashboard"""
    
    def __init__(self):
        # Import repositories here to avoid circular imports
        from dal.trackable_item_repository import TrackableItemRepository
        from dal.task_repository import TaskRepository
        from dal.pet_repository import PetRepository
        from dal.meal_repository import MealRepository
        
        self.health_repo = TrackableItemRepository()
        self.task_repo = TaskRepository()
        self.pet_repo = PetRepository()
        self.meal_repo = MealRepository()
    
    def get_today_dashboard(self, household_id: str, target_date: date = None) -> DashboardResponse:
        """Get complete dashboard data for today"""
        today = target_date or date.today()
        today_str = today.isoformat()
        
        dashboard = DashboardResponse(today)
        
        # Get all domain data
        health_items = self._get_health_dashboard_items(household_id, today_str)
        task_items = self._get_task_dashboard_items(household_id)
        pet_items = self._get_pet_dashboard_items(household_id, today_str)
        meal_summary = self._get_meal_summary(household_id)
        
        # Add all items to dashboard
        dashboard.items.extend(health_items)
        dashboard.items.extend(task_items)
        dashboard.items.extend(pet_items)
        
        # Set meal summary
        dashboard.meals = meal_summary
        
        # Calculate summary and sort
        dashboard.calculate_summary()
        dashboard.sort_items()
        
        return dashboard
    
    def _get_health_dashboard_items(self, household_id: str, today_str: str) -> List[DashboardItem]:
        """Get health items with completion status"""
        items = []
        
        try:
            # Get all health trackable items
            health_items = self.health_repo.get_household_trackable_items(household_id, 'health')
            
            # Get today's completions
            today_completions = self.health_repo.get_user_completions_today(household_id, today_str)
            
            # Get all people for person names
            people = self.health_repo.get_household_people(household_id)
            person_names = {person.person_id: person.name for person in people}
            
            for health_item in health_items:
                # Determine completion status
                status = determine_item_status(
                    health_item.item_id,
                    today_completions
                )
                
                # Get person name if applicable
                person_name = person_names.get(health_item.person_id) if hasattr(health_item, 'person_id') else None
                
                dashboard_item = create_dashboard_item_from_health(
                    health_item, 
                    status,
                    person_name
                )
                items.append(dashboard_item)
                
        except Exception as e:
            print(f"Error getting health dashboard items: {e}")
        
        return items
    
    def _get_task_dashboard_items(self, household_id: str) -> List[DashboardItem]:
        """Get task items with completion status"""
        items = []
        
        try:
            # Get all task statuses (includes completion info)
            task_statuses = self.task_repo.get_task_statuses(household_id)
            
            for task_status in task_statuses:
                # Only include active tasks
                if task_status.task.is_active:
                    dashboard_item = create_dashboard_item_from_task(task_status)
                    items.append(dashboard_item)
                    
        except Exception as e:
            print(f"Error getting task dashboard items: {e}")
        
        return items
    
    def _get_pet_dashboard_items(self, household_id: str, today_str: str) -> List[DashboardItem]:
        """Get pet care items with completion status"""
        items = []
        
        try:
            # Get all pets
            pets = self.pet_repo.get_household_pets(household_id)
            pet_names = {pet.pet_id: pet.name for pet in pets}
            
            # Get all pet care items
            for pet in pets:
                pet_care_items = self.pet_repo.get_pet_care_items(household_id, pet.pet_id)
                
                # Get today's completions for this pet
                today_completions = self.pet_repo.get_pet_care_records_today(household_id, today_str)
                
                for pet_care_item in pet_care_items:
                    # Determine completion status
                    status = determine_item_status(
                        pet_care_item.item_id,
                        today_completions
                    )
                    
                    dashboard_item = create_dashboard_item_from_pet_care(
                        pet_care_item,
                        status, 
                        pet_names.get(pet.pet_id)
                    )
                    items.append(dashboard_item)
                    
        except Exception as e:
            print(f"Error getting pet dashboard items: {e}")
        
        return items
    
    def _get_meal_summary(self, household_id: str) -> MealSummary:
        """Get meal summary for dashboard"""
        try:
            # Get all meals
            all_meals = self.meal_repo.get_household_meals(household_id)
            
            # Filter delivered meals (available to cook)
            delivered_meals = [
                meal.to_dict() for meal in all_meals 
                if meal.status == 'delivered'
            ]
            
            # Count available to cook
            available_to_cook = len(delivered_meals)
            
            # Count cooked this week (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            cooked_this_week = len([
                meal for meal in all_meals 
                if (meal.status == 'cooked' and 
                    hasattr(meal, 'created_at') and
                    datetime.fromisoformat(meal.created_at) >= week_ago)
            ])
            
            return MealSummary(
                delivered_meals=delivered_meals,
                available_to_cook=available_to_cook,
                cooked_this_week=cooked_this_week
            )
            
        except Exception as e:
            print(f"Error getting meal summary: {e}")
            return MealSummary([], 0, 0)
    
    def get_overdue_summary(self, household_id: str) -> Dict[str, Any]:
        """Get summary of all overdue items across domains"""
        overdue_items = []
        
        try:
            # Get overdue tasks
            overdue_tasks = self.task_repo.get_overdue_tasks(household_id)
            for task_status in overdue_tasks:
                overdue_items.append({
                    'type': 'task',
                    'name': task_status.task.name,
                    'overdue_since': task_status.last_completed_date.isoformat() if task_status.last_completed_date else None
                })
            
            # Note: Health and pet items don't have built-in overdue logic yet
            # This could be enhanced to include items not completed for X days
            
            return {
                'total_overdue': len(overdue_items),
                'items': overdue_items
            }
            
        except Exception as e:
            print(f"Error getting overdue summary: {e}")
            return {'total_overdue': 0, 'items': []}
    
    def get_completion_trends(self, household_id: str, days: int = 7) -> Dict[str, Any]:
        """Get completion trends over the last N days"""
        try:
            trends = []
            
            for i in range(days):
                target_date = date.today() - timedelta(days=i)
                date_str = target_date.isoformat()
                
                # Get completions for this date
                health_completions = self.health_repo.get_user_completions_today(household_id, date_str)
                task_completions = self.task_repo.get_task_completions(household_id, date_filter=date_str)
                pet_completions = self.pet_repo.get_pet_care_records_today(household_id, date_str)
                
                total_completions = len(health_completions) + len(task_completions) + len(pet_completions)
                
                trends.append({
                    'date': date_str,
                    'total_completions': total_completions,
                    'health_completions': len(health_completions),
                    'task_completions': len(task_completions),
                    'pet_completions': len(pet_completions)
                })
            
            return {
                'period_days': days,
                'trends': trends
            }
            
        except Exception as e:
            print(f"Error getting completion trends: {e}")
            return {'period_days': days, 'trends': []}