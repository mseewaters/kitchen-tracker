import jwt
from datetime import datetime

def extract_user_id_from_token(token: str, secret: str) -> str:
    """Extract user ID from JWT token"""
    try:
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        return decoded.get('sub')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def validate_auth_header(event: dict, secret: str) -> str:
    """Validate Authorization header and return user ID"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    return extract_user_id_from_token(token, secret)