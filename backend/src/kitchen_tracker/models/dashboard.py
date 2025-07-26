from datetime import date, datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DashboardItem:
    """Unified representation of any item that can be completed"""
    
    id: str
    type: str  # 'health', 'task', 'pet_care'
    name: str
    status: str  # 'pending', 'completed_today', 'overdue'
    category: str  # 'medication', 'household', 'feeding', 'treat', etc.
    person: Optional[str] = None  # For health items
    pet: Optional[str] = None  # For pet care items
    due_time: Optional[str] = None  # Future enhancement
    notes: Optional[str] = None
    last_completed_by: Optional[str] = None
    last_completed_date: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'status': self.status,
            'category': self.category,
            'person': self.person,
            'pet': self.pet,
            'due_time': self.due_time,
            'notes': self.notes,
            'last_completed_by': self.last_completed_by,
            'last_completed_date': self.last_completed_date
        }

@dataclass 
class DashboardSummary:
    """Summary statistics for the dashboard"""
    
    total_items: int
    completed_today: int
    pending: int
    overdue: int
    
    def to_dict(self) -> dict:
        return {
            'total_items': self.total_items,
            'completed_today': self.completed_today,
            'pending': self.pending,
            'overdue': self.overdue
        }

@dataclass
class MealSummary:
    """Summary of meal status for dashboard"""
    
    delivered_meals: List[Dict[str, Any]]
    available_to_cook: int
    cooked_this_week: int
    
    def to_dict(self) -> dict:
        return {
            'delivered': self.delivered_meals,
            'available_to_cook': self.available_to_cook,
            'cooked_this_week': self.cooked_this_week
        }

class DashboardResponse:
    """Complete dashboard data for today"""
    
    def __init__(self, target_date: date = None):
        self.today = target_date or date.today()
        self.items: List[DashboardItem] = []
        self.summary: DashboardSummary = DashboardSummary(0, 0, 0, 0)
        self.meals: MealSummary = MealSummary([], 0, 0)
    
    def add_item(self, item: DashboardItem):
        """Add an item to the dashboard"""
        self.items.append(item)
    
    def calculate_summary(self):
        """Calculate summary statistics from items"""
        total = len(self.items)
        completed = len([item for item in self.items if item.status == 'completed_today'])
        overdue = len([item for item in self.items if item.status == 'overdue'])
        pending = total - completed
        
        self.summary = DashboardSummary(
            total_items=total,
            completed_today=completed,
            pending=pending,
            overdue=overdue
        )
    
    def sort_items(self):
        """Sort items by priority: overdue first, then pending, then completed"""
        priority_order = {'overdue': 0, 'pending': 1, 'completed_today': 2}
        self.items.sort(key=lambda item: (
            priority_order.get(item.status, 3),
            item.type,
            item.name
        ))
    
    def to_dict(self) -> dict:
        return {
            'today': self.today.isoformat(),
            'summary': self.summary.to_dict(),
            'items': [item.to_dict() for item in self.items],
            'meals': self.meals.to_dict()
        }

def create_dashboard_item_from_health(health_item, completion_status: str, person_name: str = None) -> DashboardItem:
    """Convert a health trackable item to dashboard item"""
    return DashboardItem(
        id=health_item.item_id,
        type='health',
        name=health_item.name,
        status=completion_status,
        category='medication',  # Could be expanded to differentiate types
        person=person_name
    )

def create_dashboard_item_from_task(task_status) -> DashboardItem:
    """Convert a task status to dashboard item"""
    return DashboardItem(
        id=task_status.task.task_id,
        type='task',
        name=task_status.task.name,
        status=task_status.status,
        category='household',
        last_completed_by=task_status.last_completed_by,
        last_completed_date=task_status.last_completed_date.isoformat() if task_status.last_completed_date else None
    )

def create_dashboard_item_from_pet_care(pet_care_item, completion_status: str, pet_name: str = None) -> DashboardItem:
    """Convert a pet care item to dashboard item"""
    
    # Determine category from item name
    category = 'other'
    name_lower = pet_care_item.name.lower()
    if 'feed' in name_lower or 'food' in name_lower:
        category = 'feeding'
    elif 'treat' in name_lower:
        category = 'treats'
    elif 'medication' in name_lower or 'medicine' in name_lower:
        category = 'medication'
    elif 'bath' in name_lower or 'grooming' in name_lower:
        category = 'grooming'
    
    return DashboardItem(
        id=pet_care_item.item_id,
        type='pet_care',
        name=pet_care_item.name,
        status=completion_status,
        category=category,
        pet=pet_name
    )

def determine_item_status(item_id: str, today_completions: List, overdue_logic: callable = None) -> str:
    """Determine if an item is completed today, pending, or overdue"""
    
    # Check if completed today
    today_completion = next((comp for comp in today_completions if comp.item_id == item_id), None)
    if today_completion:
        return 'completed_today'
    
    # Check if overdue (if logic provided)
    if overdue_logic and overdue_logic():
        return 'overdue'
    
    return 'pending'