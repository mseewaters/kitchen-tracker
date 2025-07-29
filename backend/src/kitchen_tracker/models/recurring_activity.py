import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

def convert_decimals(obj):
    """Convert DynamoDB Decimal objects to int/float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

class RecurringActivity:
    """Represents a recurring activity assigned to a family member"""
    
    def __init__(
        self,
        name: str,
        assigned_to: str,  # member_id
        frequency: str,    # "daily", "weekly", "monthly"
        household_id: str,
        frequency_config: Dict[str, Any] = None,
        category: str = None,  # "medication", "feeding", "chore", "health", etc.
        activity_id: str = None
    ):
        self.activity_id = activity_id or str(uuid.uuid4())
        self.name = name  # "Morning Pills", "Dog Dinner", "Take Out Trash"
        self.assigned_to = assigned_to  # member_id of who should do this
        self.frequency = frequency.lower()
        self.frequency_config = frequency_config or {}
        self.category = category
        self.household_id = household_id
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
        
        # Validate frequency
        if self.frequency not in ['daily', 'weekly', 'monthly']:
            raise ValueError("frequency must be 'daily', 'weekly', or 'monthly'")
    
    def get_next_due_date(self, from_date: date = None) -> date:
        """Calculate when this activity is next due"""
        if from_date is None:
            from_date = date.today()
        
        if self.frequency == 'daily':
            return from_date + timedelta(days=1)
        
        elif self.frequency == 'weekly':
            # Default to Sunday (6) if not specified, 0=Monday, 6=Sunday
            target_day = self.frequency_config.get('day_of_week', 6)
            days_ahead = target_day - from_date.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return from_date + timedelta(days=days_ahead)
        
        elif self.frequency == 'monthly':
            # Default to 1st of month if not specified
            target_day = self.frequency_config.get('day_of_month', 1)
            next_month = from_date.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)  # First day of next month
            try:
                return next_month.replace(day=min(target_day, 28))  # Safe day
            except ValueError:
                return next_month.replace(day=28)  # Fallback for invalid dates
        
        else:
            # Fallback - default to daily
            return from_date + timedelta(days=1)
    
    def is_due_today(self, last_completed_date: date = None) -> bool:
        """Check if activity is due today based on last completion"""
        today = date.today()
        
        if last_completed_date is None:
            return True  # Never completed, so due today
        
        if self.frequency == 'daily':
            # Due if not completed today
            return last_completed_date < today
        
        elif self.frequency == 'weekly':
            # Due if it's the target day and hasn't been completed this week
            target_day = self.frequency_config.get('day_of_week', 6)
            if today.weekday() != target_day:
                return False  # Not the right day
            
            # Check if completed this week
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            return last_completed_date < week_start
        
        elif self.frequency == 'monthly':
            # Due if it's the target day and hasn't been completed this month
            target_day = self.frequency_config.get('day_of_month', 1)
            if today.day != target_day:
                return False  # Not the right day
            
            # Check if completed this month
            month_start = today.replace(day=1)
            return last_completed_date < month_start
        
        return False
    
    def is_overdue(self, last_completed_date: date = None) -> bool:
        """Check if activity is overdue"""
        if last_completed_date is None:
            # If never completed, consider overdue after 1 day
            return True
        
        today = date.today()
        next_due = self.get_next_due_date(last_completed_date)
        return today > next_due
    
    def get_current_period_status(self, last_completed_date: date = None) -> str:
        """Get status for current period: 'completed', 'due', 'overdue', 'upcoming'"""
        today = date.today()
        
        if self.frequency == 'daily':
            if last_completed_date == today:
                return 'completed'
            elif last_completed_date is None or last_completed_date < today:
                return 'overdue' if last_completed_date and (today - last_completed_date).days > 1 else 'due'
            else:
                return 'upcoming'
        
        elif self.frequency == 'weekly':
            target_day = self.frequency_config.get('day_of_week', 6)
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            
            if last_completed_date and last_completed_date >= week_start:
                return 'completed'
            elif today.weekday() == target_day:
                return 'due'
            elif today.weekday() > target_day:
                return 'overdue'
            else:
                return 'upcoming'
        
        elif self.frequency == 'monthly':
            target_day = self.frequency_config.get('day_of_month', 1)
            month_start = today.replace(day=1)
            
            if last_completed_date and last_completed_date >= month_start:
                return 'completed'
            elif today.day == target_day:
                return 'due'
            elif today.day > target_day:
                return 'overdue'
            else:
                return 'upcoming'
        
        return 'due'
    
    def to_dict(self) -> dict:
        return {
            'activity_id': self.activity_id,
            'name': self.name,
            'assigned_to': self.assigned_to,
            'frequency': self.frequency,
            'frequency_config': self.frequency_config,
            'category': self.category,
            'household_id': self.household_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecurringActivity':
        # Convert any Decimal objects from DynamoDB
        clean_data = convert_decimals(data)
        
        activity = cls(
            name=clean_data['name'],
            assigned_to=clean_data['assigned_to'],
            frequency=clean_data['frequency'],
            household_id=clean_data['household_id'],
            frequency_config=clean_data.get('frequency_config', {}),
            category=clean_data.get('category'),
            activity_id=clean_data.get('activity_id')
        )
        
        if 'created_at' in clean_data:
            activity.created_at = clean_data['created_at']
        if 'is_active' in clean_data:
            activity.is_active = clean_data['is_active']
            
        return activity
    
    def __str__(self) -> str:
        return f"{self.name} ({self.frequency})"
    
    def __repr__(self) -> str:
        return f"RecurringActivity(id={self.activity_id}, name='{self.name}', frequency='{self.frequency}')"
    
