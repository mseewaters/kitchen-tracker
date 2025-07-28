import uuid
from datetime import datetime
from typing import Optional

class FamilyMember:
    """Represents a person or pet in the household"""
    
    def __init__(
        self,
        name: str,
        member_type: str,  # "person" or "pet"
        household_id: str,
        pet_type: str = None,  # "dog", "cat", etc. (only for pets)
        member_id: str = None
    ):
        self.member_id = member_id or str(uuid.uuid4())
        self.name = name  # "Bob", "Marjorie", "Layla", "Lucy", "Sadie"
        self.member_type = member_type.lower()  # "person" or "pet"
        self.pet_type = pet_type.lower() if pet_type else None
        self.household_id = household_id
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
        
        # Validate member type
        if self.member_type not in ['person', 'pet']:
            raise ValueError("member_type must be 'person' or 'pet'")
        
        # Validate pet_type is provided for pets
        if self.member_type == 'pet' and not self.pet_type:
            raise ValueError("pet_type is required when member_type is 'pet'")
    
    def to_dict(self) -> dict:
        result = {
            'member_id': self.member_id,
            'name': self.name,
            'member_type': self.member_type,
            'household_id': self.household_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
        
        # Only include pet_type if it's a pet
        if self.member_type == 'pet' and self.pet_type:
            result['pet_type'] = self.pet_type
            
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FamilyMember':
        member = cls(
            name=data['name'],
            member_type=data['member_type'],
            household_id=data['household_id'],
            pet_type=data.get('pet_type'),
            member_id=data.get('member_id')
        )
        
        if 'created_at' in data:
            member.created_at = data['created_at']
        if 'is_active' in data:
            member.is_active = data['is_active']
            
        return member
    
    def __str__(self) -> str:
        if self.member_type == 'pet':
            return f"{self.name} ({self.pet_type})"
        return self.name
    
    def __repr__(self) -> str:
        return f"FamilyMember(id={self.member_id}, name='{self.name}', type='{self.member_type}')"