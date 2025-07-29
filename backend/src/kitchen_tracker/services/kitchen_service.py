from typing import List, Optional, Dict, Any
from datetime import date, datetime

# Import with fallback for Lambda environment
try:
    from ..models.family_member import FamilyMember
    from ..models.recurring_activity import RecurringActivity
    from ..models.activity_completion import ActivityCompletion, ActivityStatus
    from ..dal.family_member_repository import FamilyMemberRepository
    from ..dal.recurring_activity_repository import RecurringActivityRepository
    from ..dal.activity_completion_repository import ActivityCompletionRepository
except ImportError:
    # Lambda environment - use absolute imports
    from models.family_member import FamilyMember
    from models.recurring_activity import RecurringActivity
    from models.activity_completion import ActivityCompletion, ActivityStatus
    from dal.family_member_repository import FamilyMemberRepository
    from dal.recurring_activity_repository import RecurringActivityRepository
    from dal.activity_completion_repository import ActivityCompletionRepository

class KitchenService:
    """Service layer for kitchen tracker business logic"""
    
    def __init__(self):
        self.family_repo = FamilyMemberRepository()
        self.activity_repo = RecurringActivityRepository()
        self.completion_repo = ActivityCompletionRepository()
    
    # Family Member Operations
    def create_family_member(self, name: str, member_type: str, household_id: str, pet_type: str = None) -> FamilyMember:
        """Create a new family member"""
        member = FamilyMember(
            name=name,
            member_type=member_type,
            household_id=household_id,
            pet_type=pet_type
        )
        return self.family_repo.create(member)
    
    def get_family_members(self, household_id: str) -> List[FamilyMember]:
        """Get all family members for a household"""
        return self.family_repo.get_by_household_id(household_id)
    
    def get_family_member(self, member_id: str) -> Optional[FamilyMember]:
        """Get a specific family member"""
        return self.family_repo.get_by_id(member_id)
    
    def update_family_member(self, member: FamilyMember) -> FamilyMember:
        """Update a family member"""
        return self.family_repo.update(member)
    
    def delete_family_member(self, member_id: str) -> bool:
        """Soft delete a family member"""
        return self.family_repo.soft_delete(member_id)
    
    # Activity Operations
    def create_activity(self, name: str, assigned_to: str, frequency: str, 
                       household_id: str, frequency_config: Dict = None, 
                       category: str = None) -> RecurringActivity:
        """Create a new recurring activity"""
        activity = RecurringActivity(
            name=name,
            assigned_to=assigned_to,
            frequency=frequency,
            household_id=household_id,
            frequency_config=frequency_config or {},
            category=category
        )
        return self.activity_repo.create(activity)
    
    def get_activities(self, household_id: str) -> List[RecurringActivity]:
        """Get all activities for a household"""
        return self.activity_repo.get_by_household_id(household_id)
    
    def get_activity(self, activity_id: str) -> Optional[RecurringActivity]:
        """Get a specific activity"""
        return self.activity_repo.get_by_id(activity_id)
    
    def get_activities_with_status(self, household_id: str) -> List[Dict]:
        """Get all activities with their completion status"""
        activities = self.get_activities(household_id)
        result = []
        
        for activity in activities:
            status = self.get_activity_status(activity.activity_id)
            result.append(status.to_dict() if status else activity.to_dict())
        
        return result
    
    def get_activity_status(self, activity_id: str) -> Optional[ActivityStatus]:
        """Get activity with current status"""
        activity = self.get_activity(activity_id)
        if not activity:
            return None
        
        today = date.today()
        completion = self.completion_repo.get_latest_completion(activity_id, today)
        
        return ActivityStatus(
            activity=activity,
            last_completion=completion,
            target_date=today
        )
    
    def complete_activity(self, activity_id: str, completed_by: str = None, 
                         completion_date: date = None, notes: str = None) -> ActivityCompletion:
        """Mark an activity as completed"""
        completion_date = completion_date or date.today()
        
        completion = ActivityCompletion(
            activity_id=activity_id,
            completion_date=completion_date,
            completed_by=completed_by,
            notes=notes
        )
        
        return self.completion_repo.create(completion)
    
    def undo_activity_completion(self, activity_id: str, completion_date: date = None) -> bool:
        """Undo the most recent completion for an activity"""
        completion_date = completion_date or date.today()
        return self.completion_repo.delete_completion(activity_id, completion_date)
    
    # Dashboard and Summary Operations
    def get_dashboard_data(self, household_id: str) -> Dict[str, Any]:
        """Get dashboard data for a household"""
        activities_with_status = self.get_activities_with_status(household_id)
        
        # Categorize activities
        due_today = []
        overdue = []
        completed_today = []
        upcoming = []
        
        for activity_data in activities_with_status:
            status = activity_data.get('status', 'due')
            if status == 'completed':
                completed_today.append(activity_data)
            elif status == 'overdue':
                overdue.append(activity_data)
            elif status == 'due':
                due_today.append(activity_data)
            else:
                upcoming.append(activity_data)
        
        return {
            'household_id': household_id,
            'date': date.today().isoformat(),
            'summary': {
                'total_activities': len(activities_with_status),
                'due_today': len(due_today),
                'overdue': len(overdue), 
                'completed_today': len(completed_today),
                'upcoming': len(upcoming)
            },
            'due_today': due_today,
            'overdue': overdue,
            'completed_today': completed_today,
            'upcoming': upcoming
        }
    
    def get_household_summary(self, household_id: str) -> Dict[str, Any]:
        """Get household summary information"""
        family_members = self.get_family_members(household_id)
        activities = self.get_activities(household_id)
        
        people = [m for m in family_members if m.member_type == 'person']
        pets = [m for m in family_members if m.member_type == 'pet']
        
        return {
            'household_id': household_id,
            'family_members': {
                'total': len(family_members),
                'people': len(people),
                'pets': len(pets)
            },
            'activities': {
                'total': len(activities),
                'active': len([a for a in activities if a.is_active])
            }
        }
    
    def get_activities_due_today(self, household_id: str) -> List[Dict]:
        """Get activities due today"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a.get('status') == 'due']
    
    def get_overdue_activities(self, household_id: str) -> List[Dict]:
        """Get overdue activities"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a.get('status') == 'overdue']
    
    def get_completed_activities_today(self, household_id: str) -> List[Dict]:
        """Get activities completed today"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a.get('status') == 'completed']