from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

# Import helper for Lambda environment
try:
    from ..models.family_member import FamilyMember
    from .base_repository import BaseRepository
except ImportError:
    # Lambda environment - use absolute imports
    from models.family_member import FamilyMember
    from dal.base_repository import BaseRepository

class FamilyMemberRepository(BaseRepository):
    def __init__(self):
        import os
        table_name = os.getenv('FAMILY_MEMBERS_TABLE', 'FamilyMembers')
        super().__init__(table_name)
    
    def create(self, family_member: FamilyMember) -> FamilyMember:
        """Create a new family member"""
        try:
            item = family_member.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(member_id)'
            )
            return family_member
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Family member with ID {family_member.member_id} already exists")
            raise e
    
    def get_by_id(self, member_id: str) -> Optional[FamilyMember]:
        """Get a family member by ID"""
        try:
            response = self.table.get_item(Key={'member_id': member_id})
            if 'Item' in response:
                return FamilyMember.from_dict(response['Item'])
            return None
        except ClientError as e:
            print(f"Error getting family member {member_id}: {e}")
            return None
    
    def get_by_household_id(self, household_id: str) -> List[FamilyMember]:
        """Get all family members for a household"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':is_active': True
                }
            )
            
            members = []
            for item in response.get('Items', []):
                members.append(FamilyMember.from_dict(item))
            
            # Sort by member type (people first, then pets) and then by name
            members.sort(key=lambda m: (m.member_type, m.name.lower()))
            return members
            
        except ClientError as e:
            print(f"Error getting family members for household {household_id}: {e}")
            return []
    
    def get_people_by_household_id(self, household_id: str) -> List[FamilyMember]:
        """Get only people (not pets) for a household"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND member_type = :member_type AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':member_type': 'person',
                    ':is_active': True
                }
            )
            
            members = []
            for item in response.get('Items', []):
                members.append(FamilyMember.from_dict(item))
            
            members.sort(key=lambda m: m.name.lower())
            return members
            
        except ClientError as e:
            print(f"Error getting people for household {household_id}: {e}")
            return []
    
    def get_pets_by_household_id(self, household_id: str) -> List[FamilyMember]:
        """Get only pets (not people) for a household"""
        try:
            response = self.table.scan(
                FilterExpression='household_id = :household_id AND member_type = :member_type AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':household_id': household_id,
                    ':member_type': 'pet',
                    ':is_active': True
                }
            )
            
            members = []
            for item in response.get('Items', []):
                members.append(FamilyMember.from_dict(item))
            
            members.sort(key=lambda m: m.name.lower())
            return members
            
        except ClientError as e:
            print(f"Error getting pets for household {household_id}: {e}")
            return []
    
    def update(self, family_member: FamilyMember) -> FamilyMember:
        """Update an existing family member"""
        try:
            item = family_member.to_dict()
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_exists(member_id)'
            )
            return family_member
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise ValueError(f"Family member with ID {family_member.member_id} does not exist")
            raise e
    
    def soft_delete(self, member_id: str) -> bool:
        """Soft delete a family member by setting is_active to False"""
        try:
            member = self.get_by_id(member_id)
            if not member:
                return False
            
            member.is_active = False
            self.update(member)
            return True
        except Exception as e:
            print(f"Error soft deleting family member {member_id}: {e}")
            return False