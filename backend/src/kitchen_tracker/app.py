import json
import os
from typing import Dict, Any
from datetime import date

from models.trackable_item import TrackableItem, CompletionRecord
from dal.trackable_item_repository import TrackableItemRepository
from models.pet import Pet, PetCareItem, PetCareRecord
from dal.pet_repository import PetRepository
from models.person import Person

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for kitchen-tracker API
    """
    
    # CORS headers
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
    }
    
    # Handle preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Extract path and method
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # Basic health check (no API key required)
        if path == '/' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'kitchen-tracker API is running!'})
            }
        
        # Health endpoints
        if path.startswith('/health'):
            return handle_health_endpoints(event, headers)
        
        # Person endpoints
        if path.startswith('/people'):
            return handle_person_endpoints(event, headers)
        
        # Pet endpoints
        if path.startswith('/pets'):
            return handle_pet_endpoints(event, headers)
        
        # Meal endpoints (future)
        if path.startswith('/meals'):
            return handle_meal_endpoints(event, headers)
        
        # Default response
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def handle_health_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle health-related API endpoints"""
    
    # Get household ID from environment (single household setup)
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    repo = TrackableItemRepository()
    
    try:
        # GET /health/items - Get all health trackable items
        if path == '/health/items' and method == 'GET':
            items = repo.get_user_trackable_items(household_id, 'health')
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([item.to_dict() for item in items])
            }
        
        # POST /health/items - Create new health trackable item
        elif path == '/health/items' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            item = TrackableItem(
                name=body['name'],
                category='health',
                user_id=household_id  # Using household_id as user_id for now
            )
            
            success = repo.create_trackable_item(item)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(item.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to create item'})
                }
        
        # POST /health/complete - Mark health item as completed
        elif path == '/health/complete' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            completion = CompletionRecord(
                item_id=body['item_id'],
                user_id=household_id
            )
            
            success = repo.create_completion_record(completion)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(completion.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to record completion'})
                }
        
        # GET /health/today - Get today's completions
        elif path == '/health/today' and method == 'GET':
            today = date.today().isoformat()
            completions = repo.get_user_completions_today(household_id, today)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([comp.to_dict() for comp in completions])
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Health endpoint not found'})
            }
            
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': f'Missing required field: {str(e)}'})
        }

def handle_pet_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle pet-related endpoints using proper Pet domain models"""
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    pet_repo = PetRepository()
    
    try:
        # GET /pets - Get all pets and their care items
        if path == '/pets' and method == 'GET':
            pets = pet_repo.get_household_pets(household_id)
            
            # Get care items for each pet
            pets_with_care = []
            for pet in pets:
                care_items = pet_repo.get_pet_care_items(household_id, pet.pet_id)
                pets_with_care.append({
                    'pet_id': pet.pet_id,
                    'name': pet.name,
                    'pet_type': pet.pet_type,
                    'care_items': [item.to_dict() for item in care_items]
                })
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(pets_with_care)
            }
        
        # POST /pets/setup - Create a pet and its standard care items
        elif path == '/pets/setup' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            pet_name = body['pet_name']
            pet_type = body.get('pet_type', 'dog')
            
            # Create the pet
            pet = Pet(
                name=pet_name,
                pet_type=pet_type,
                household_id=household_id
            )
            
            if not pet_repo.create_pet(pet):
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to create pet'})
                }
            
            # Create standard care items
            created_items = []
            
            # Daily care items for all pets
            daily_items = [
                ('feeding', 'daily'),
                ('treat', 'daily')
            ]
            
            for care_type, frequency in daily_items:
                care_item = PetCareItem(
                    pet_id=pet.pet_id,
                    care_type=care_type,
                    frequency=frequency,
                    household_id=household_id
                )
                if pet_repo.create_pet_care_item(care_item):
                    created_items.append(care_item.to_dict())
            
            # Monthly care items for all pets
            monthly_items = [('flea_treatment', 'monthly')]
            
            # Add dog-specific items
            if pet_type.lower() == 'dog':
                monthly_items.append(('heartworm', 'monthly'))
                # Bath is as-needed for dogs
                bath_item = PetCareItem(
                    pet_id=pet.pet_id,
                    care_type='bath',
                    frequency='as_needed',
                    household_id=household_id
                )
                if pet_repo.create_pet_care_item(bath_item):
                    created_items.append(bath_item.to_dict())
            
            for care_type, frequency in monthly_items:
                care_item = PetCareItem(
                    pet_id=pet.pet_id,
                    care_type=care_type,
                    frequency=frequency,
                    household_id=household_id
                )
                if pet_repo.create_pet_care_item(care_item):
                    created_items.append(care_item.to_dict())
            
            return {
                'statusCode': 201,
                'headers': headers,
                'body': json.dumps({
                    'pet': pet.to_dict(),
                    'care_items_created': len(created_items),
                    'care_items': created_items
                })
            }
        
        # POST /pets/complete - Mark pet care as completed
        elif path == '/pets/complete' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            care_record = PetCareRecord(
                item_id=body['item_id'],
                pet_id=body['pet_id'],
                household_id=household_id,
                notes=body.get('notes')  # Optional notes like "second treat"
            )
            
            success = pet_repo.create_pet_care_record(care_record)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(care_record.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to record pet care completion'})
                }
        
        # GET /pets/today - Get today's pet care completions
        elif path == '/pets/today' and method == 'GET':
            today = date.today().isoformat()
            records = pet_repo.get_pet_care_records_today(household_id, today)
            
            # Enrich with pet and care item details
            enriched_records = []
            for record in records:
                # Get pet info
                pet = pet_repo.get_pet(household_id, record.pet_id)
                pet_name = pet.name if pet else "Unknown Pet"
                
                record_dict = record.to_dict()
                record_dict['pet_name'] = pet_name
                enriched_records.append(record_dict)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(enriched_records)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Pet endpoint not found'})
            }
            
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': f'Missing required field: {str(e)}'})
        }

def handle_person_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle person-related endpoints"""
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    repo = TrackableItemRepository()
    
    try:
        # GET /people - Get all people in household
        if path == '/people' and method == 'GET':
            people = repo.get_household_people(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([person.to_dict() for person in people])
            }
        
        # POST /people - Create a new person
        elif path == '/people' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            person = Person(
                name=body['name'],
                household_id=household_id
            )
            
            success = repo.create_person(person)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(person.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to create person'})
                }
        
        # POST /people/{person_id}/health - Create health item for specific person
        elif path.startswith('/people/') and path.endswith('/health') and method == 'POST':
            # Extract person_id from path like "/people/abc123/health"
            path_parts = path.split('/')
            if len(path_parts) >= 4:
                person_id = path_parts[2]
                
                # Verify person exists
                person = repo.get_person(household_id, person_id)
                if not person:
                    return {
                        'statusCode': 404,
                        'headers': headers,
                        'body': json.dumps({'error': 'Person not found'})
                    }
                
                body = json.loads(event.get('body', '{}'))
                
                # Create health item for specific person
                item = TrackableItem(
                    name=body['name'],
                    category='health',
                    user_id=household_id,
                    person_id=person_id
                )
                
                success = repo.create_trackable_item(item)
                if success:
                    response_data = item.to_dict()
                    response_data['person_name'] = person.name
                    return {
                        'statusCode': 201,
                        'headers': headers,
                        'body': json.dumps(response_data)
                    }
                else:
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps({'error': 'Failed to create health item'})
                    }
        
        # GET /people/{person_id}/health - Get health items for specific person
        elif path.startswith('/people/') and path.endswith('/health') and method == 'GET':
            path_parts = path.split('/')
            if len(path_parts) >= 4:
                person_id = path_parts[2]
                
                # Get all health items and filter by person_id
                all_health_items = repo.get_household_trackable_items(household_id, 'health')
                person_health_items = [item for item in all_health_items if item.person_id == person_id]
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps([item.to_dict() for item in person_health_items])
                }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Person endpoint not found'})
            }
            
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': f'Missing required field: {str(e)}'})
        }

def handle_meal_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle meal-related endpoints (placeholder for now)"""
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'message': 'Meal endpoints coming soon!'})
    }