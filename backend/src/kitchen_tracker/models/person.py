import uuid
from datetime import datetime
from typing import Optional

class Person:
    def __init__(
        self,
        name: str,
        household_id: str,
        person_id: str = None
    ):
        self.person_id = person_id or str(uuid.uuid4())
        self.name = name  # "Sarah", "John"
        self.household_id = household_id
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def to_dict(self) -> dict:
        return {
            'person_id': self.person_id,
            'name': self.name,
            'household_id': self.household_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Person':
        person = cls(
            name=data['name'],
            household_id=data['household_id'],
            person_id=data.get('person_id')
        )
        if 'created_at' in data:
            person.created_at = data['created_at']
        if 'is_active' in data:
            person.is_active = data['is_active']
        return person