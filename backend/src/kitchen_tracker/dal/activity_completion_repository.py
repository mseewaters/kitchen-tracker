from typing import List, Optional
from datetime import date, datetime, timedelta
import boto3

# Import with fallback for Lambda environment
try:
    from ..models.activity_completion import ActivityCompletion
except ImportError:
    # Lambda environment - use absolute imports
    from models.activity_completion import ActivityCompletion
try:
    from .base_repository import BaseRepository
except ImportError:
    # Lambda environment - use absolute imports
    from dal.base_repository import BaseRepository
from botocore.exceptions import ClientError



class ActivityCompletionRepository(BaseRepository):
    def __init__(self):
        import os
        table_name = os.getenv('ACTIVITY_COMPLETIONS_TABLE', 'ActivityCompletions')
        super().__init__(table_name)
    
    def create(self, completion: ActivityCompletion) -> ActivityCompletion:
        """Create a new activity completion record"""
        try:
            item = completion.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(completion_id)'
            )
            return completion
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Completion with ID {completion.completion_id} already exists")
            raise e
    
    def get_by_id(self, completion_id: str) -> Optional[ActivityCompletion]:
        """Get a completion record by ID"""
        try:
            response = self.table.get_item(Key={'completion_id': completion_id})
            if 'Item' in response:
                return ActivityCompletion.from_dict(response['Item'])
            return None
        except ClientError as e:
            print(f"Error getting completion {completion_id}: {e}")
            return None
    
    def get_by_activity_id(self, activity_id: str, limit: int = 50) -> List[ActivityCompletion]:
        """Get completion records for a specific activity"""
        try:
            response = self.table.scan(
                FilterExpression='activity_id = :activity_id',
                ExpressionAttributeValues={
                    ':activity_id': activity_id
                },
                Limit=limit
            )
            
            completions = []
            for item in response.get('Items', []):
                completions.append(ActivityCompletion.from_dict(item))
            
            # Sort by completion date descending (most recent first)
            completions.sort(key=lambda c: c.completion_date, reverse=True)
            return completions
            
        except ClientError as e:
            print(f"Error getting completions for activity {activity_id}: {e}")
            return []
    
    def get_by_member_id(self, member_id: str, household_id: str, limit: int = 50) -> List[ActivityCompletion]:
        """Get completion records for a specific family member"""
        try:
            response = self.table.scan(
                FilterExpression='member_id = :member_id AND household_id = :household_id',
                ExpressionAttributeValues={
                    ':member_id': member_id,
                    ':household_id': household_id
                },
                Limit=limit
            )
            
            completions = []
            for item in response.get('Items', []):
                completions.append(ActivityCompletion.from_dict(item))
            
            # Sort by completion date descending (most recent first)
            completions.sort(key=lambda c: c.completion_date, reverse=True)
            return completions
            
        except ClientError as e:
            print(f"Error getting completions for member {member_id}: {e}")
            return []
    
    def get_by_household_id(self, household_id: str, days_back: int = 30) -> List[ActivityCompletion]:
        """Get completion records for a household within a date range"""
        try:
            start_date = (date.today() - timedelta(days=days_back)).isoformat()
            
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND completion_date >= :start_date',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':start_date': start_date
                }
            )
            
            completions = []
            for item in response.get('Items', []):
                completions.append(ActivityCompletion.from_dict(item))
            
            # Sort by completion date descending (most recent first)
            completions.sort(key=lambda c: c.completion_date, reverse=True)
            return completions
            
        except ClientError as e:
            print(f"Error getting completions for household {household_id}: {e}")
            return []
    
    def get_latest_completion_for_activity(self, activity_id: str) -> Optional[ActivityCompletion]:
        """Get the most recent completion for a specific activity"""
        completions = self.get_by_activity_id(activity_id, limit=1)
        return completions[0] if completions else None
    
    def get_completion_for_activity_and_date(self, activity_id: str, completion_date: str) -> Optional[ActivityCompletion]:
        """Get completion record for a specific activity on a specific date"""
        try:
            response = self.table.scan(
                FilterExpression='activity_id = :activity_id AND completion_date = :completion_date',
                ExpressionAttributeValues={
                    ':activity_id': activity_id,
                    ':completion_date': completion_date
                },
                Limit=1
            )
            
            items = response.get('Items', [])
            if items:
                return ActivityCompletion.from_dict(items[0])
            return None
            
        except ClientError as e:
            print(f"Error getting completion for activity {activity_id} on {completion_date}: {e}")
            return None
    
    def has_completion_for_period(self, activity_id: str, target_date: date, frequency: str, frequency_config: dict = None) -> bool:
        """Check if there's a completion for the given period (day/week/month)"""
        completions = self.get_by_activity_id(activity_id, limit=10)  # Get recent completions
        
        for completion in completions:
            if completion.is_same_period(target_date, frequency, frequency_config):
                return True
        
        return False
    
    def delete_completion(self, completion_id: str) -> bool:
        """Delete a completion record (hard delete)"""
        try:
            self.table.delete_item(
                Key={'completion_id': completion_id},
                ConditionExpression='attribute_exists(completion_id)'
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Completion with ID {completion_id} does not exist")
                return False
            print(f"Error deleting completion {completion_id}: {e}")
            return False
    
    def delete_completions_for_activity(self, activity_id: str) -> int:
        """Delete all completion records for an activity (used when deleting activity)"""
        completions = self.get_by_activity_id(activity_id, limit=1000)  # Get all completions
        deleted_count = 0
        
        for completion in completions:
            if self.delete_completion(completion.completion_id):
                deleted_count += 1
        
        return deleted_count
    
    def get_latest_completion(self, activity_id: str, target_date: date = None) -> Optional[ActivityCompletion]:
        """Get the most recent completion for a specific activity"""
        completions = self.get_by_activity_id(activity_id, limit=1)
        return completions[0] if completions else None
    
    def get_latest_completion_for_activity(self, activity_id: str) -> Optional[ActivityCompletion]:
        """Get the most recent completion for a specific activity (alias)"""
        return self.get_latest_completion(activity_id)