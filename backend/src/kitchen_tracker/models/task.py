import uuid
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
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

class TaskItem:
    """Represents a recurring household task"""
    
    def __init__(
        self,
        name: str,
        household_id: str,
        frequency: str,  # 'daily', 'weekly', 'monthly', 'custom'
        frequency_config: Dict[str, Any] = None,  # {day_of_week: 1, interval: 2}
        task_id: str = None
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name  # "Take out trash", "Clean bathrooms"
        self.household_id = household_id
        self.frequency = frequency
        self.frequency_config = frequency_config or {}
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def get_next_due_date(self, from_date: date = None) -> date:
        """Calculate when this task is next due"""
        if from_date is None:
            from_date = date.today()
        
        if self.frequency == 'daily':
            return from_date + timedelta(days=1)
        
        elif self.frequency == 'weekly':
            # Default to Sunday (6) if not specified
            target_day = self.frequency_config.get('day_of_week', 6)  # 0=Monday, 6=Sunday
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
            # Custom or unknown frequency - default to weekly
            return from_date + timedelta(days=7)
    
    def is_due_today(self, last_completed: date = None) -> bool:
        """Check if task is due today based on last completion"""
        today = date.today()
        
        if last_completed is None:
            return True  # Never completed, so due today
        
        next_due = self.get_next_due_date(last_completed)
        return today >= next_due
    
    def is_overdue(self, last_completed: date = None) -> bool:
        """Check if task is overdue"""
        if last_completed is None:
            # If never completed, consider overdue after 1 day
            return True
        
        today = date.today()
        next_due = self.get_next_due_date(last_completed)
        return today > next_due
    
    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'household_id': self.household_id,
            'frequency': self.frequency,
            'frequency_config': self.frequency_config,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskItem':
        # Convert any Decimal objects from DynamoDB
        clean_data = convert_decimals(data)
        
        task = cls(
            name=clean_data['name'],
            household_id=clean_data['household_id'],
            frequency=clean_data['frequency'],
            frequency_config=clean_data.get('frequency_config', {}),
            task_id=clean_data.get('task_id')
        )
        if 'created_at' in clean_data:
            task.created_at = clean_data['created_at']
        if 'is_active' in clean_data:
            task.is_active = clean_data['is_active']
        return task


class TaskCompletionRecord:
    """Records when a task was completed"""
    
    def __init__(
        self,
        task_id: str,
        household_id: str,
        completed_by: str = None,  # user/person who completed it
        completed_date: str = None,
        completed_at: str = None,
        notes: str = None,
        record_id: str = None
    ):
        self.record_id = record_id or str(uuid.uuid4())
        self.task_id = task_id
        self.household_id = household_id
        self.completed_by = completed_by
        self.completed_date = completed_date or date.today().isoformat()
        self.completed_at = completed_at or datetime.utcnow().isoformat()
        self.notes = notes
    
    def to_dict(self) -> dict:
        return {
            'record_id': self.record_id,
            'task_id': self.task_id,
            'household_id': self.household_id,
            'completed_by': self.completed_by,
            'completed_date': self.completed_date,
            'completed_at': self.completed_at,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskCompletionRecord':
        # Convert any Decimal objects from DynamoDB
        clean_data = convert_decimals(data)
        
        return cls(
            task_id=clean_data['task_id'],
            household_id=clean_data['household_id'],
            completed_by=clean_data.get('completed_by'),
            completed_date=clean_data.get('completed_date'),
            completed_at=clean_data.get('completed_at'),
            notes=clean_data.get('notes'),
            record_id=clean_data.get('record_id')
        )


class TaskStatus:
    """Helper class to represent task status with context"""
    
    def __init__(
        self,
        task: TaskItem,
        last_completed_date: date = None,
        last_completed_by: str = None
    ):
        self.task = task
        self.last_completed_date = last_completed_date
        self.last_completed_by = last_completed_by
    
    @property
    def is_due_today(self) -> bool:
        return self.task.is_due_today(self.last_completed_date)
    
    @property
    def is_overdue(self) -> bool:
        return self.task.is_overdue(self.last_completed_date)
    
    @property
    def next_due_date(self) -> date:
        if self.last_completed_date:
            return self.task.get_next_due_date(self.last_completed_date)
        else:
            return date.today()  # Due today if never completed
    
    @property
    def status(self) -> str:
        """Returns: 'overdue', 'due_today', 'upcoming', 'completed_today'"""
        today = date.today()
        
        if (self.last_completed_date and 
            self.last_completed_date == today):
            return 'completed_today'
        elif self.is_overdue:
            return 'overdue'
        elif self.is_due_today:
            return 'due_today'
        else:
            return 'upcoming'
    
    def to_dict(self) -> dict:
        result = self.task.to_dict()
        result.update({
            'last_completed_date': self.last_completed_date.isoformat() if self.last_completed_date else None,
            'last_completed_by': self.last_completed_by,
            'is_due_today': self.is_due_today,
            'is_overdue': self.is_overdue,
            'next_due_date': self.next_due_date.isoformat(),
            'status': self.status
        })
        return result