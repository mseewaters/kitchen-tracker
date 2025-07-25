from typing import List, Optional
from .base_repository import BaseRepository
from models.pet import Pet, PetCareItem, PetCareRecord

class PetRepository(BaseRepository):
    def __init__(self):
        super().__init__()
    
    def create_pet(self, pet: Pet) -> bool:
        """Create a new pet"""
        data = pet.to_dict()
        data['record_type'] = 'pet'
        data['user_id'] = pet.household_id  # Use household_id as user_id for DynamoDB
        data['item_id'] = pet.pet_id
        return self.put_item(data)
    
    def get_pet(self, household_id: str, pet_id: str) -> Optional[Pet]:
        """Get a pet by ID"""
        data = self.get_item(household_id, pet_id)
        if data and data.get('record_type') == 'pet':
            return Pet.from_dict(data)
        return None
    
    def get_household_pets(self, household_id: str) -> List[Pet]:
        """Get all pets for a household"""
        items = self.query_by_user(household_id)
        pets = []
        
        for item_data in items:
            if item_data.get('record_type') == 'pet':
                pets.append(Pet.from_dict(item_data))
        
        return pets
    
    def create_pet_care_item(self, care_item: PetCareItem) -> bool:
        """Create a pet care item"""
        data = care_item.to_dict()
        data['record_type'] = 'pet_care_item'
        data['user_id'] = care_item.household_id
        return self.put_item(data)
    
    def get_pet_care_items(self, household_id: str, pet_id: str = None) -> List[PetCareItem]:
        """Get pet care items for household, optionally filtered by pet"""
        items = self.query_by_user(household_id)
        care_items = []
        
        for item_data in items:
            if item_data.get('record_type') == 'pet_care_item':
                if pet_id is None or item_data.get('pet_id') == pet_id:
                    care_items.append(PetCareItem.from_dict(item_data))
        
        return care_items
    
    def create_pet_care_record(self, record: PetCareRecord) -> bool:
        """Create a pet care completion record"""
        data = record.to_dict()
        data['record_type'] = 'pet_care_record'
        data['user_id'] = record.household_id
        # Preserve original item_id and use record_id as DynamoDB key
        data['original_item_id'] = data['item_id']
        data['item_id'] = record.record_id  # Use record_id as DynamoDB item_id
        return self.put_item(data)
    
    def get_pet_care_records_today(self, household_id: str, date_str: str) -> List[PetCareRecord]:
        """Get pet care records for a specific date"""
        items = self.query_by_user(household_id)
        records = []
        
        for item_data in items:
            if (item_data.get('record_type') == 'pet_care_record' and 
                item_data.get('completed_date') == date_str):
                # Restore original structure for PetCareRecord
                record_data = item_data.copy()
                record_data['item_id'] = record_data.get('original_item_id', record_data['item_id'])
                records.append(PetCareRecord.from_dict(record_data))
        
        return records