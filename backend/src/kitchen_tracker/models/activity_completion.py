import uuid
from datetime import datetime, date
from typing import Optional

class ActivityCompletion:
    """Records when a recurring activity was completed"""
    
    def __init__(
        self,
        activity_id: str,
        member_id: str,      # who the activity is assigned to
        household_id: str,
        completion_date: str = None,  # YYYY-MM-DD format
        completed_at: str = None,     # ISO timestamp
        completed_by: str = None,     # who marked it complete (could be different from assigned)
        notes: str = None,
        completion_id: str = None
    ):
        self.completion_id = completion_id or str(uuid.uuid4())
        self.activity_id = activity_id
        self.member_id = member_id  # who the activity is assigned to
        self.household_id = household_id
        self.completion_date = completion_date or date.today().isoformat()
        self.completed_at = completed_at or datetime.utcnow().isoformat()
        self.completed_by = completed_by or member_id  # defaults to assigned person
        self.notes = notes
    
    @property
    def completion_date_obj(self) -> date:
        """Return completion_date as a date object"""
        return date.fromisoformat(self.completion_date)
    
    @property
    def completed_at_obj(self) -> datetime:
        """Return completed_at as a datetime object"""
        return datetime.fromisoformat(self.completed_at.replace('Z', '+00:00'))
    
    def to_dict(self) -> dict:
        result = {
            'completion_id': self.completion_id,
            'activity_id': self.activity_id,
            'member_id': self.member_id,
            'household_id': self.household_id,
            'completion_date': self.completion_date,
            'completed_at': self.completed_at,
            'completed_by': self.completed_by
        }
        
        # Only include notes if present
        if self.notes:
            result['notes'] = self.notes
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ActivityCompletion':
        return cls(
            activity_id=data['activity_id'],
            member_id=data['member_id'],
            household_id=data['household_id'],
            completion_date=data.get('completion_date'),
            completed_at=data.get('completed_at'),
            completed_by=data.get('completed_by'),
            notes=data.get('notes'),
            completion_id=data.get('completion_id')
        )
    
    def is_same_period(self, other_date: date, frequency: str, frequency_config: dict = None) -> bool:
        """Check if this completion is in the same period as other_date for given frequency"""
        from datetime import timedelta  # Import here to avoid circular imports
        
        completion_date = self.completion_date_obj
        frequency_config = frequency_config or {}
        
        if frequency == 'daily':
            return completion_date == other_date
        
        elif frequency == 'weekly':
            # Check if both dates are in the same week
            def get_week_start(d: date) -> date:
                return d - timedelta(days=d.weekday())
            
            return get_week_start(completion_date) == get_week_start(other_date)
        
        elif frequency == 'monthly':
            # Check if both dates are in the same month
            return (completion_date.year == other_date.year and 
                   completion_date.month == other_date.month)
        
        return False
    
    def __str__(self) -> str:
        return f"Completion on {self.completion_date}"
    
    def __repr__(self) -> str:
        return f"ActivityCompletion(id={self.completion_id}, activity={self.activity_id}, date={self.completion_date})"


class ActivityStatus:
    """Helper class to represent activity status with completion context"""
    
    def __init__(
        self,
        activity: 'RecurringActivity',  # Import will be handled at runtime
        last_completion: ActivityCompletion = None,
        member_name: str = None
    ):
        self.activity = activity
        self.last_completion = last_completion
        self.member_name = member_name
    
    @property
    def last_completed_date(self) -> Optional[date]:
        """Get the last completion date as a date object"""
        if self.last_completion:
            return self.last_completion.completion_date_obj
        return None
    
    @property
    def is_due_today(self) -> bool:
        """Check if activity is due today"""
        return self.activity.is_due_today(self.last_completed_date)
    
    @property
    def is_overdue(self) -> bool:
        """Check if activity is overdue"""
        return self.activity.is_overdue(self.last_completed_date)
    
    @property
    def status(self) -> str:
        """Get current status: 'completed', 'due', 'overdue', 'upcoming'"""
        return self.activity.get_current_period_status(self.last_completed_date)
    
    @property
    def next_due_date(self) -> date:
        """Get the next due date"""
        if self.last_completed_date:
            return self.activity.get_next_due_date(self.last_completed_date)
        else:
            return date.today()  # Due today if never completed
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        result = self.activity.to_dict()
        result.update({
            'member_name': self.member_name,
            'last_completed_date': self.last_completed_date.isoformat() if self.last_completed_date else None,
            'last_completed_by': self.last_completion.completed_by if self.last_completion else None,
            'is_due_today': self.is_due_today,
            'is_overdue': self.is_overdue,
            'status': self.status,
            'next_due_date': self.next_due_date.isoformat(),
            'completed': self.status == 'completed'  # For frontend compatibility
        })
        
        if self.last_completion and self.last_completion.notes:
            result['last_completion_notes'] = self.last_completion.notes
            
        return result