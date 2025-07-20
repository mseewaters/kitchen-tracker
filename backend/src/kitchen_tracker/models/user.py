import uuid
from datetime import datetime
from typing import Optional

class User:
    def __init__(
        self,
        email: str,
        first_name: str,
        last_name: str,
        user_id: str = None
    ):
        self.user_id = user_id or str(uuid.uuid4())
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        user = cls(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_id=data.get('user_id')
        )
        if 'created_at' in data:
            user.created_at = data['created_at']
        return user