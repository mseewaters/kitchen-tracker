from typing import List, Optional
import boto3

# Import with fallback for Lambda environment
try:
    from ..models.recurring_activity import RecurringActivity
except ImportError:
    # Lambda environment - use absolute imports
    from models.recurring_activity import RecurringActivity
try:
    from .base_repository import BaseRepository
except ImportError:
    # Lambda environment - use absolute imports
    from dal.base_repository import BaseRepository
from botocore.exceptions import ClientError



class RecurringActivityRepository(BaseRepository):
    def __init__(self):
        import os
        table_name = os.getenv('RECURRING_ACTIVITIES_TABLE', 'RecurringActivities')
        super().__init__(table_name)
    
    def create(self, activity: RecurringActivity) -> RecurringActivity:
        """Create a new recurring activity"""
        try:
            item = activity.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(activity_id)'
            )
            return activity
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Activity with ID {activity.activity_id} already exists")
            raise e
    
    def get_by_id(self, activity_id: str) -> Optional[RecurringActivity]:
        """Get an activity by ID"""
        try:
            response = self.table.get_item(Key={'activity_id': activity_id})
            if 'Item' in response:
                return RecurringActivity.from_dict(response['Item'])
            return None
        except ClientError as e:
            print(f"Error getting activity {activity_id}: {e}")
            return None
    
    def get_by_household_id(self, household_id: str) -> List[RecurringActivity]:
        """Get all activities for a household"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            # Sort by name
            activities.sort(key=lambda a: a.name.lower())
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for household {household_id}: {e}")
            return []
    
    def get_by_member_id(self, member_id: str, household_id: str) -> List[RecurringActivity]:
        """Get all activities assigned to a specific family member"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND assigned_to = :member_id AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':member_id': member_id,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            # Sort by name
            activities.sort(key=lambda a: a.name.lower())
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for member {member_id}: {e}")
            return []
    
    def get_by_category(self, household_id: str, category: str) -> List[RecurringActivity]:
        """Get all activities in a specific category"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND category = :category AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':category': category,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            # Sort by assigned member, then by name
            activities.sort(key=lambda a: (a.assigned_to, a.name.lower()))
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for category {category}: {e}")
            return []
    
    def get_by_frequency(self, household_id: str, frequency: str) -> List[RecurringActivity]:
        """Get all activities with a specific frequency"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND frequency = :frequency AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':frequency': frequency,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            # Sort by assigned member, then by name
            activities.sort(key=lambda a: (a.assigned_to, a.name.lower()))
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for frequency {frequency}: {e}")
            return []
    
    def update(self, activity: RecurringActivity) -> RecurringActivity:
        """Update an existing activity"""
        try:
            item = activity.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(activity_id)'
            )
            return activity
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Activity with ID {activity.activity_id} does not exist")
            raise e
    
    def soft_delete(self, activity_id: str) -> bool:
        """Soft delete an activity by setting is_active to False"""
        try:
            self.table.update_item(
                Key={'activity_id': activity_id},
                UpdateExpression='SET is_active = :is_active',
                ExpressionAttributeValues={':is_active': False},
                ConditionExpression='attribute_exists(activity_id)'
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Activity with ID {activity_id} does not exist")
                return False
            print(f"Error soft deleting activity {activity_id}: {e}")
            return False
    
    def delete(self, activity_id: str) -> bool:
        """Hard delete an activity (use with caution)"""
        try:
            self.table.delete_item(
                Key={'activity_id': activity_id},
                ConditionExpression='attribute_exists(activity_id)'
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Activity with ID {activity_id} does not exist")
                return False
            print(f"Error deleting activity {activity_id}: {e}")
            return False
        
    def get_by_member_id(self, member_id: str, household_id: str) -> List[RecurringActivity]:
        """Get all activities assigned to a specific member"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND assigned_to = :member_id AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':member_id': member_id,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            # Sort by name
            activities.sort(key=lambda a: a.name.lower())
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for member {member_id}: {e}")
            return []
        
    def get_by_member_id(self, member_id: str, household_id: str) -> List[RecurringActivity]:
        """Get all activities assigned to a specific member"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND assigned_to = :member_id AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':member_id': member_id,
                    ':is_active': True
                }
            )
            
            activities = []
            for item in response.get('Items', []):
                activities.append(RecurringActivity.from_dict(item))
            
            activities.sort(key=lambda a: a.name.lower())
            return activities
            
        except ClientError as e:
            print(f"Error getting activities for member {member_id}: {e}")
            return []

    def update(self, activity: RecurringActivity) -> RecurringActivity:
        """Update an existing activity"""
        try:
            item = activity.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(activity_id)'
            )
            return activity
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Activity with ID {activity.activity_id} does not exist")
            raise e
        
    
    def soft_delete(self, activity_id: str) -> bool:
        """Soft delete an activity by setting is_active to False"""
        try:
            self.table.update_item(
                Key={'activity_id': activity_id},
                UpdateExpression='SET is_active = :is_active',
                ExpressionAttributeValues={':is_active': False},
                ConditionExpression='attribute_exists(activity_id)'
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"Activity with ID {activity_id} does not exist")
                return False
            print(f"Error soft deleting activity {activity_id}: {e}")
            return False