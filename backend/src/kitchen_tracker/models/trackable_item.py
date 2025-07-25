import uuid
from datetime import datetime, date
from typing import Optional

class TrackableItem:
    def __init__(
        self,
        name: str,
        category: str,  # 'health', 'task', 'pet', etc.
        user_id: str,
        person_id: str = None,  # Which person this item belongs to
        item_id: str = None
    ):
        self.item_id = item_id or str(uuid.uuid4())
        self.name = name  # "Morning Bupropion", "Afternoon Vitamins"
        self.category = category
        self.user_id = user_id
        self.person_id = person_id  # Sarah's vs John's medications
        self.created_at = datetime.utcnow().isoformat()
        self.is_active = True
    
    def to_dict(self) -> dict:
        return {
            'item_id': self.item_id,
            'name': self.name,
            'category': self.category,
            'user_id': self.user_id,
            'person_id': self.person_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TrackableItem':
        item = cls(
            name=data['name'],
            category=data['category'],
            user_id=data['user_id'],
            person_id=data.get('person_id'),
            item_id=data.get('item_id')
        )
        if 'created_at' in data:
            item.created_at = data['created_at']
        if 'is_active' in data:
            item.is_active = data['is_active']
        return item


class CompletionRecord:
    def __init__(
        self,
        item_id: str,
        user_id: str,
        completed_date: str = None,  # YYYY-MM-DD format
        completed_at: str = None,    # ISO timestamp
        record_id: str = None
    ):
        self.record_id = record_id or str(uuid.uuid4())
        self.item_id = item_id
        self.user_id = user_id
        self.completed_date = completed_date or date.today().isoformat()
        self.completed_at = completed_at or datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'record_id': self.record_id,
            'item_id': self.item_id,
            'user_id': self.user_id,
            'completed_date': self.completed_date,
            'completed_at': self.completed_at
        }
    
    @classmethod 
    def from_dict(cls, data: dict) -> 'CompletionRecord':
        return cls(
            item_id=data['item_id'],
            user_id=data['user_id'],
            completed_date=data.get('completed_date'),
            completed_at=data.get('completed_at'),
            record_id=data.get('record_id')
        )