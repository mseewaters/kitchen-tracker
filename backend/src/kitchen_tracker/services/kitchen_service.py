from typing import List, Optional, Dict, Any
from datetime import date, datetime
from ..models.family_member import FamilyMember
from ..models.recurring_activity import RecurringActivity
from ..models.activity_completion import ActivityCompletion, ActivityStatus
from ..dal.family_member_repository import FamilyMemberRepository
from ..dal.recurring_activity_repository import RecurringActivityRepository
from ..dal.activity_completion_repository import ActivityCompletionRepository

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
                       household_id: str, frequency_config: Dict[str, Any] = None, 
                       category: str = None) -> RecurringActivity:
        """Create a new recurring activity"""
        activity = RecurringActivity(
            name=name,
            assigned_to=assigned_to,
            frequency=frequency,
            household_id=household_id,
            frequency_config=frequency_config,
            category=category
        )
        return self.activity_repo.create(activity)
    
    def get_activities(self, household_id: str) -> List[RecurringActivity]:
        """Get all activities for a household"""
        return self.activity_repo.get_by_household_id(household_id)
    
    def get_activities_for_member(self, member_id: str, household_id: str) -> List[RecurringActivity]:
        """Get all activities assigned to a specific member"""
        return self.activity_repo.get_by_member_id(member_id, household_id)
    
    def get_activity(self, activity_id: str) -> Optional[RecurringActivity]:
        """Get a specific activity"""
        return self.activity_repo.get_by_id(activity_id)
    
    def update_activity(self, activity: RecurringActivity) -> RecurringActivity:
        """Update an activity"""
        return self.activity_repo.update(activity)
    
    def delete_activity(self, activity_id: str) -> bool:
        """Soft delete an activity and its completion records"""
        # First delete completion records
        self.completion_repo.delete_completions_for_activity(activity_id)
        # Then soft delete the activity
        return self.activity_repo.soft_delete(activity_id)
    
    # Activity Completion Operations
    def complete_activity(self, activity_id: str, member_id: str, household_id: str, 
                         completion_date: str = None, completed_by: str = None, 
                         notes: str = None) -> ActivityCompletion:
        """Mark an activity as completed"""
        completion = ActivityCompletion(
            activity_id=activity_id,
            member_id=member_id,
            household_id=household_id,
            completion_date=completion_date or date.today().isoformat(),
            completed_by=completed_by,
            notes=notes
        )
        return self.completion_repo.create(completion)
    
    def undo_activity_completion(self, activity_id: str, completion_date: str = None) -> bool:
        """Remove a completion record for an activity"""
        target_date = completion_date or date.today().isoformat()
        completion = self.completion_repo.get_completion_for_activity_and_date(activity_id, target_date)
        
        if completion:
            return self.completion_repo.delete_completion(completion.completion_id)
        return False
    
    def get_activity_completions(self, activity_id: str, limit: int = 50) -> List[ActivityCompletion]:
        """Get completion history for an activity"""
        return self.completion_repo.get_by_activity_id(activity_id, limit)
    
    def get_member_completions(self, member_id: str, household_id: str, limit: int = 50) -> List[ActivityCompletion]:
        """Get completion history for a family member"""
        return self.completion_repo.get_by_member_id(member_id, household_id, limit)
    
    # Dashboard and Status Operations
    def get_dashboard_data(self, household_id: str) -> Dict[str, Any]:
        """Get complete dashboard data with family members and their activity statuses"""
        # Get all family members
        family_members = self.get_family_members(household_id)
        
        # Get all activities
        activities = self.get_activities(household_id)
        
        # Group activities by member
        member_activities = {}
        for activity in activities:
            if activity.assigned_to not in member_activities:
                member_activities[activity.assigned_to] = []
            member_activities[activity.assigned_to].append(activity)
        
        # Build dashboard data
        dashboard_data = {
            'family_members': [],
            'summary': {
                'total_members': len(family_members),
                'total_activities': len(activities),
                'people_count': len([m for m in family_members if m.member_type == 'person']),
                'pet_count': len([m for m in family_members if m.member_type == 'pet'])
            }
        }
        
        # Get activity statuses for each member
        for member in family_members:
            member_data = member.to_dict()
            member_data['activities'] = []
            
            if member.member_id in member_activities:
                for activity in member_activities[member.member_id]:
                    activity_status = self.get_activity_status(activity.activity_id)
                    member_data['activities'].append(activity_status.to_dict())
            
            dashboard_data['family_members'].append(member_data)
        
        return dashboard_data
    
    def get_activity_status(self, activity_id: str) -> Optional[ActivityStatus]:
        """Get the current status of an activity with completion context"""
        activity = self.get_activity(activity_id)
        if not activity:
            return None
        
        # Get the most recent completion
        latest_completion = self.completion_repo.get_latest_completion_for_activity(activity_id)
        
        # Get the member name
        member = self.get_family_member(activity.assigned_to)
        member_name = member.name if member else "Unknown"
        
        return ActivityStatus(activity, latest_completion, member_name)
    
    def get_activities_with_status(self, household_id: str) -> List[Dict[str, Any]]:
        """Get all activities with their current status"""
        activities = self.get_activities(household_id)
        activities_with_status = []
        
        for activity in activities:
            status = self.get_activity_status(activity.activity_id)
            if status:
                activities_with_status.append(status.to_dict())
        
        return activities_with_status
    
    def get_activities_due_today(self, household_id: str) -> List[Dict[str, Any]]:
        """Get all activities that are due today"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a['is_due_today']]
    
    def get_overdue_activities(self, household_id: str) -> List[Dict[str, Any]]:
        """Get all activities that are overdue"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a['is_overdue']]
    
    def get_completed_activities_today(self, household_id: str) -> List[Dict[str, Any]]:
        """Get all activities completed today"""
        activities_with_status = self.get_activities_with_status(household_id)
        return [a for a in activities_with_status if a['status'] == 'completed']
    
    # Utility Methods
    def get_household_summary(self, household_id: str) -> Dict[str, Any]:
        """Get summary statistics for a household"""
        activities_with_status = self.get_activities_with_status(household_id)
        
        summary = {
            'total_activities': len(activities_with_status),
            'completed_today': len([a for a in activities_with_status if a['status'] == 'completed']),
            'due_today': len([a for a in activities_with_status if a['is_due_today']]),
            'overdue': len([a for a in activities_with_status if a['is_overdue']]),
            'upcoming': len([a for a in activities_with_status if a['status'] == 'upcoming'])
        }
        
        # Calculate completion percentage
        if summary['total_activities'] > 0:
            summary['completion_percentage'] = round(
                (summary['completed_today'] / summary['total_activities']) * 100, 1
            )
        else:
            summary['completion_percentage'] = 0.0
        
        return summary