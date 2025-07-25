import boto3
import os
from typing import Dict, List, Optional, Any
from boto3.dynamodb.conditions import Key

class BaseRepository:
    def __init__(self, table_name: str = None):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name or os.environ.get('ITEMS_TABLE')
        self.table = self.dynamodb.Table(self.table_name)
    
    def put_item(self, item: Dict[str, Any]) -> bool:
        """Create or update an item"""
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error putting item: {e}")
            return False
    
    def get_item(self, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single item by user_id and item_id"""
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'item_id': item_id
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"Error getting item: {e}")
            return None
    
    def query_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all items for a user"""
        try:
            response = self.table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error querying items: {e}")
            return []
    
    def delete_item(self, user_id: str, item_id: str) -> bool:
        """Delete an item"""
        try:
            self.table.delete_item(
                Key={
                    'user_id': user_id,
                    'item_id': item_id
                }
            )
            return True
        except Exception as e:
            print(f"Error deleting item: {e}")
            return False