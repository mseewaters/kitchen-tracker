from typing import List, Optional
from .base_repository import BaseRepository
from models.trackable_item import TrackableItem, CompletionRecord
from models.person import Person

class TrackableItemRepository(BaseRepository):
    def __init__(self):
        super().__init__()
    
    def create_trackable_item(self, item: TrackableItem) -> bool:
        """Create a new trackable item"""
        data = item.to_dict()
        data['record_type'] = 'trackable_item'  # Distinguish from completion records
        return self.put_item(data)
    
    def get_trackable_item(self, user_id: str, item_id: str) -> Optional[TrackableItem]:
        """Get a trackable item by ID"""
        data = self.get_item(user_id, item_id)
        if data and data.get('record_type') == 'trackable_item':
            return TrackableItem.from_dict(data)
        return None
    
    def get_user_trackable_items(self, user_id: str, category: str = None) -> List[TrackableItem]:
        """Get all trackable items for a user, optionally filtered by category"""
        items = self.query_by_user(user_id)
        trackable_items = []
        
        for item_data in items:
            if item_data.get('record_type') == 'trackable_item':
                if category is None or item_data.get('category') == category:
                    trackable_items.append(TrackableItem.from_dict(item_data))
        
        return trackable_items
    
    def get_household_trackable_items(self, household_id: str, category: str = None) -> List[TrackableItem]:
        """Get all trackable items for a household, optionally filtered by category"""
        # For now, using household_id as user_id since we're single-household
        return self.get_user_trackable_items(household_id, category)
    
    def update_trackable_item(self, item: TrackableItem) -> bool:
        """Update an existing trackable item"""
        data = item.to_dict()
        data['record_type'] = 'trackable_item'
        return self.put_item(data)
    
    def delete_trackable_item(self, user_id: str, item_id: str) -> bool:
        """Delete a trackable item"""
        return self.delete_item(user_id, item_id)
    
    def create_completion_record(self, record: CompletionRecord) -> bool:
        """Create a completion record"""
        data = record.to_dict()
        data['record_type'] = 'completion_record'
        # Preserve original item_id and use record_id as DynamoDB key
        data['original_item_id'] = data['item_id']
        data['item_id'] = data['record_id']
        return self.put_item(data)
    
    def get_user_completions_today(self, user_id: str, date_str: str) -> List[CompletionRecord]:
        """Get all completion records for a user on a specific date"""
        items = self.query_by_user(user_id)
        completions = []
        
        for item_data in items:
            if (item_data.get('record_type') == 'completion_record' and 
                item_data.get('completed_date') == date_str):
                # Restore original structure for CompletionRecord
                completion_data = item_data.copy()
                completion_data['item_id'] = completion_data.get('original_item_id', completion_data['item_id'])
                completions.append(CompletionRecord.from_dict(completion_data))
        
        return completions
    
    # Person methods
    def create_person(self, person: Person) -> bool:
        """Create a new person"""
        data = person.to_dict()
        data['record_type'] = 'person'
        data['user_id'] = person.household_id  # Use household_id as user_id for DynamoDB
        data['item_id'] = person.person_id
        return self.put_item(data)
    
    def get_person(self, household_id: str, person_id: str) -> Optional[Person]:
        """Get a person by ID"""
        data = self.get_item(household_id, person_id)
        if data and data.get('record_type') == 'person':
            return Person.from_dict(data)
        return None
    
    def get_household_people(self, household_id: str) -> List[Person]:
        """Get all people in a household"""
        items = self.query_by_user(household_id)
        people = []
        
        for item_data in items:
            if item_data.get('record_type') == 'person':
                people.append(Person.from_dict(item_data))
        
        return people