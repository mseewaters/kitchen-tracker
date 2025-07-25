import uuid
from datetime import datetime
from typing import List, Optional

class Pet:
    def __init__(
        self,
        name: str,
        pet_type: str,  # 'dog', 'cat', etc.
        household_id: str,
        pet_id: str = None
    ):
        self.pet_id = pet_id or str(uuid.uuid4())
        self.name = name  # "Fluffy", "Rex", "Whiskers"
        self.pet_type = pet_type.lower()
        self.household_id = household_id
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def to_dict(self) -> dict:
        return {
            'pet_id': self.pet_id,
            'name': self.name,
            'pet_type': self.pet_type,
            'household_id': self.household_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pet':
        pet = cls(
            name=data['name'],
            pet_type=data['pet_type'],
            household_id=data['household_id'],
            pet_id=data.get('pet_id')
        )
        if 'created_at' in data:
            pet.created_at = data['created_at']
        if 'is_active' in data:
            pet.is_active = data['is_active']
        return pet


class PetCareItem:
    """Extends TrackableItem concept for pet-specific care"""
    def __init__(
        self,
        pet_id: str,
        care_type: str,  # 'feeding', 'treat', 'flea_treatment', 'heartworm', 'bath'
        frequency: str,  # 'daily', 'monthly', 'as_needed'
        household_id: str,
        item_id: str = None
    ):
        self.item_id = item_id or str(uuid.uuid4())
        self.pet_id = pet_id
        self.care_type = care_type
        self.frequency = frequency
        self.household_id = household_id
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def to_dict(self) -> dict:
        return {
            'item_id': self.item_id,
            'pet_id': self.pet_id,
            'care_type': self.care_type,
            'frequency': self.frequency,
            'household_id': self.household_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PetCareItem':
        item = cls(
            pet_id=data['pet_id'],
            care_type=data['care_type'],
            frequency=data['frequency'],
            household_id=data['household_id'],
            item_id=data.get('item_id')
        )
        if 'created_at' in data:
            item.created_at = data['created_at']
        if 'is_active' in data:
            item.is_active = data['is_active']
        return item


class PetCareRecord:
    """Records when pet care was completed"""
    def __init__(
        self,
        item_id: str,
        pet_id: str,
        household_id: str,
        completed_date: str = None,
        completed_at: str = None,
        notes: str = None,  # Optional notes like "second treat"
        record_id: str = None
    ):
        self.record_id = record_id or str(uuid.uuid4())
        self.item_id = item_id
        self.pet_id = pet_id
        self.household_id = household_id
        self.completed_date = completed_date or datetime.utcnow().date().isoformat()
        self.completed_at = completed_at or datetime.utcnow().isoformat()
        self.notes = notes
    
    def to_dict(self) -> dict:
        return {
            'record_id': self.record_id,
            'item_id': self.item_id,
            'pet_id': self.pet_id,
            'household_id': self.household_id,
            'completed_date': self.completed_date,
            'completed_at': self.completed_at,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PetCareRecord':
        return cls(
            item_id=data['item_id'],
            pet_id=data['pet_id'],
            household_id=data['household_id'],
            completed_date=data.get('completed_date'),
            completed_at=data.get('completed_at'),
            notes=data.get('notes'),
            record_id=data.get('record_id')
        )