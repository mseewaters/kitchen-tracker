import json
import os
from typing import Dict, Any
from datetime import date, datetime, timedelta
import boto3
import email
from email.mime.multipart import MIMEMultipart
import re
import requests

from models.trackable_item import TrackableItem, CompletionRecord
from dal.trackable_item_repository import TrackableItemRepository
from models.pet import Pet, PetCareItem, PetCareRecord
from dal.pet_repository import PetRepository
from models.person import Person
from models.task import TaskItem, TaskCompletionRecord
from dal.task_repository import TaskRepository

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
        
        # Meal endpoints
        if path.startswith('/meals'):
            return handle_meal_endpoints(event, headers)
        
        # Task endpoints
        if path.startswith('/tasks'):
            return handle_task_endpoints(event, headers)
        
        # Dashboard endpoints
        if path.startswith('/dashboard'):
            return handle_dashboard_endpoints(event, headers)
        
        
        # Quick complete endpoints
        if path.startswith('/complete'):
            return handle_complete_endpoints(event, headers)
        

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
    """Handle meal-related endpoints using MealRepository"""
    from models.meal import Meal
    from dal.meal_repository import MealRepository
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    meal_repo = MealRepository()  # Use dedicated repository
    
    try:
        # POST /meals/setup - Create new meal
        if path == '/meals/setup' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            # Calculate week_of from delivery_date
            delivery_date = body.get('delivery_date')
            week_of = calculate_week_of(delivery_date) if delivery_date else None
            
            meal = Meal(
                name=body['name'],
                household_id=household_id,
                week_of=week_of,
                recipe_url=body.get('recipe_link'),
                delivery_date=delivery_date
            )
            
            # Mark as delivered if we have a delivery date
            if delivery_date:
                meal.mark_delivered(delivery_date)
            
            success = meal_repo.create_meal(meal)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(meal.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to create meal'})
                }
        
        # GET /meals - Get all meals (optionally by week)
        elif path == '/meals' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            week_of = query_params.get('week_of')
            
            meals = meal_repo.get_household_meals(household_id, week_of)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([meal.to_dict() for meal in meals])
            }

        # POST /meals/cook - Record cooking a meal
        elif path == '/meals/cook' and method == 'POST':
            from models.meal import MealRecord
            
            body = json.loads(event.get('body', '{}'))
            
            # Create cooking record
            meal_record = MealRecord(
                meal_id=body['meal_id'],
                household_id=household_id,
                cooked_by=body.get('cooked_by'),
                notes=body.get('notes')
            )
            
            success = meal_repo.create_meal_record(meal_record)
            if success:
                # Also update the meal status to "cooked"
                meal_repo.update_meal_status(household_id, body['meal_id'], 'cooked')
                
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(meal_record.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to record meal cooking'})
                }
        
        # GET /meals/records - Get cooking records for all meals or specific meal
        elif path == '/meals/records' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            meal_id = query_params.get('meal_id')
            
            records = meal_repo.get_meal_records(household_id, meal_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([record.to_dict() for record in records])
            }
        
        # GET /meals/{meal_id} - Get specific meal by ID
        elif path.startswith('/meals/') and method == 'GET' and path != '/meals/setup' and path != '/meals/cook' and path != '/meals/records':
            meal_id = path.split('/meals/')[1]
            
            meal = meal_repo.get_meal(household_id, meal_id)
            if meal:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(meal.to_dict())
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Meal not found'})
                }
        
        # PUT /meals/{meal_id}/status - Update meal status
        elif path.startswith('/meals/') and path.endswith('/status') and method == 'PUT':
            meal_id = path.split('/meals/')[1].split('/status')[0]
            body = json.loads(event.get('body', '{}'))
            
            success = meal_repo.update_meal_status(household_id, meal_id, body['status'])
            if success:
                updated_meal = meal_repo.get_meal(household_id, meal_id)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(updated_meal.to_dict())
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Meal not found or update failed'})
                }
           
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Meal endpoint not found'})
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

# Add this function to app.py, after the other handle_*_endpoints functions

def handle_task_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle household task-related endpoints"""
    from models.task import TaskItem, TaskCompletionRecord
    from dal.task_repository import TaskRepository
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    task_repo = TaskRepository()
    
    try:
        # POST /tasks/setup - Create new recurring task
        if path == '/tasks/setup' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            # Parse frequency configuration
            frequency_config = {}
            if body['frequency'] == 'weekly' and 'day_of_week' in body:
                frequency_config['day_of_week'] = body['day_of_week']
            elif body['frequency'] == 'monthly' and 'day_of_month' in body:
                frequency_config['day_of_month'] = body['day_of_month']
            
            task = TaskItem(
                name=body['name'],
                household_id=household_id,
                frequency=body['frequency'],
                frequency_config=frequency_config
            )
            
            success = task_repo.create_task(task)
            if success:
                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps(task.to_dict())
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to create task'})
                }
        
        # GET /tasks - Get all household tasks with status
        elif path == '/tasks' and method == 'GET':
            statuses = task_repo.get_task_statuses(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([status.to_dict() for status in statuses])
            }
        
        # POST /tasks/complete - Mark task as completed
        elif path == '/tasks/complete' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            completion = TaskCompletionRecord(
                task_id=body['task_id'],
                household_id=household_id,
                completed_by=body.get('completed_by'),
                notes=body.get('notes')
            )
            
            success = task_repo.create_task_completion(completion)
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
                    'body': json.dumps({'error': 'Failed to record task completion'})
                }
        
        # GET /tasks/today - Get tasks due today
        elif path == '/tasks/today' and method == 'GET':
            due_today = task_repo.get_due_today_tasks(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([status.to_dict() for status in due_today])
            }
        
        # GET /tasks/overdue - Get overdue tasks
        elif path == '/tasks/overdue' and method == 'GET':
            overdue = task_repo.get_overdue_tasks(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps([status.to_dict() for status in overdue])
            }
        
        # GET /tasks/completed - Get tasks completed today
        elif path == '/tasks/completed' and method == 'GET':
            completed = task_repo.get_completed_today_tasks(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(completed)
            }
        
        # GET /tasks/{task_id} - Get specific task with status
        elif path.startswith('/tasks/') and method == 'GET' and len(path.split('/')) == 3:
            task_id = path.split('/tasks/')[1]
            
            task = task_repo.get_task(household_id, task_id)
            if task:
                # Get task with status info
                statuses = task_repo.get_task_statuses(household_id)
                task_status = next((s for s in statuses if s.task.task_id == task_id), None)
                
                if task_status:
                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps(task_status.to_dict())
                    }
                else:
                    return {
                        'statusCode': 200,
                        'headers': headers,
                        'body': json.dumps(task.to_dict())
                    }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Task not found'})
                }
        
        # PUT /tasks/{task_id}/status - Activate/deactivate task
        elif path.startswith('/tasks/') and path.endswith('/status') and method == 'PUT':
            task_id = path.split('/tasks/')[1].split('/status')[0]
            body = json.loads(event.get('body', '{}'))
            
            success = task_repo.update_task_status(household_id, task_id, body['is_active'])
            if success:
                updated_task = task_repo.get_task(household_id, task_id)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(updated_task.to_dict())
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Task not found or update failed'})
                }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Task endpoint not found'})
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

# Add this function to app.py, after the other handle_*_endpoints functions

def handle_dashboard_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle unified dashboard endpoints"""
    from services.dashboard_service import DashboardService
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    dashboard_service = DashboardService()
    
    try:
        # GET /dashboard/today - Main dashboard with all items due today
        if path == '/dashboard/today' and method == 'GET':
            dashboard = dashboard_service.get_today_dashboard(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(dashboard.to_dict())
            }
        
        # GET /dashboard/overdue - Summary of overdue items
        elif path == '/dashboard/overdue' and method == 'GET':
            overdue_summary = dashboard_service.get_overdue_summary(household_id)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(overdue_summary)
            }
        
        # GET /dashboard/trends - Completion trends over time
        elif path == '/dashboard/trends' and method == 'GET':
            query_params = event.get('queryStringParameters') or {}
            days = int(query_params.get('days', 7))  # Default to 7 days
            
            trends = dashboard_service.get_completion_trends(household_id, days)
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(trends)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Dashboard endpoint not found'})
            }
            
    except Exception as e:
        # Enhanced error handling for debugging
        error_message = str(e)
        print(f"Dashboard endpoint error: {error_message}")
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Dashboard service error: {error_message}'})
        }

# Add this function to app.py, after the other handle_*_endpoints functions
def handle_complete_endpoints(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Handle simple tablet completion - tap to complete anything"""
    
    household_id = os.environ.get('HOUSEHOLD_ID')
    if not household_id:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Household ID not configured'})
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    try:
        # POST /complete - Simple universal completion
        if path == '/complete' and method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            item_id = body['id']
            item_type = body['type']
            
            # Route to appropriate completion endpoint (simple versions)
            if item_type == 'health':
                success = _simple_complete_health(item_id, household_id)
            elif item_type == 'task':
                success = _simple_complete_task(item_id, household_id)
            elif item_type == 'pet_care':
                success = _simple_complete_pet_care(item_id, household_id)
            else:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid type'})
                }
            
            if success:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'success': True, 'item_id': item_id})
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'item_id': item_id})
                }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def _simple_complete_health(item_id: str, household_id: str) -> bool:
    """Simple health completion - just mark it done"""
    try:
        from models.trackable_item import CompletionRecord
        from dal.trackable_item_repository import TrackableItemRepository
        
        repo = TrackableItemRepository()
        completion = CompletionRecord(item_id=item_id, user_id=household_id)
        return repo.create_completion_record(completion)
    except:
        return False


def _simple_complete_task(item_id: str, household_id: str) -> bool:
    """Simple task completion - just mark it done"""
    try:
        from models.task import TaskCompletionRecord
        from dal.task_repository import TaskRepository
        
        repo = TaskRepository()
        completion = TaskCompletionRecord(task_id=item_id, household_id=household_id)
        return repo.create_task_completion(completion)
    except:
        return False


def _simple_complete_pet_care(item_id: str, household_id: str) -> bool:
    """Simple pet care completion - just mark it done"""
    try:
        from models.pet import PetCareRecord
        from dal.pet_repository import PetRepository
        
        repo = PetRepository()
        
        # Find the pet for this care item
        pets = repo.get_household_pets(household_id)
        for pet in pets:
            care_items = repo.get_pet_care_items(household_id, pet.pet_id)
            if any(item.item_id == item_id for item in care_items):
                completion = PetCareRecord(item_id=item_id, pet_id=pet.pet_id, household_id=household_id)
                return repo.create_pet_care_record(completion)
        return False
    except:
        return False
        
def email_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle SES email events - parse Home Chef emails and extract meal data
    """
    print(f"SES event received: {json.dumps(event)}")
    
    try:
        # Get S3 details from the SES event
        for record in event['Records']:
            if record['eventSource'] == 'aws:ses':
                bucket = os.environ['EMAIL_BUCKET'] 
                key = record['ses']['mail']['messageId']
                
                # Read email from S3
                s3 = boto3.client('s3')
                response = s3.get_object(Bucket=bucket, Key=key)
                raw_email = response['Body'].read().decode('utf-8')
                
                print(f"Email content length: {len(raw_email)}")
                
                # Parse the email for Home Chef meals
                meals = parse_homechef_email(raw_email)
                print(f"Extracted {len(meals)} meals: {meals}")

                # After parsing the email, add this:
                if meals:
                    api_url = os.environ['API_URL']
                    success = store_meals_via_api(meals, api_url)
                    print(f"Meals storage {'successful' if success else 'failed'}")
                
    except Exception as e:
        print(f"Error processing email: {str(e)}")
    
    return {'statusCode': 200}

def parse_homechef_email(raw_email: str) -> list:
    """Parse Home Chef email and extract meal information with links"""
    meals = []
    
    # Parse the email to get HTML content
    email_msg = email.message_from_string(raw_email)
    html_content = ""
    
    # Find HTML part and decode properly
    if email_msg.is_multipart():
        for part in email_msg.walk():
            if part.get_content_type() == "text/html":
                # Get the payload and decode it
                payload = part.get_payload(decode=True)
                if payload:
                    html_content = payload.decode('utf-8', errors='ignore')
                    break
    
    if not html_content:
        print("No HTML content found in email")
        return meals
    
    print(f"HTML content found, length: {len(html_content)}")
    
    # Extract delivery date from the actual email pattern
    delivery_date = None
    # Pattern from your actual email: "scheduled to arrive by end of the day on <strong>Thursday, July 3</strong>"
    date_pattern = r'scheduled to arrive by end of the day on\s*<strong>([^<]+)</strong>'
    date_match = re.search(date_pattern, html_content, re.IGNORECASE)
    if date_match:
        delivery_date = date_match.group(1).strip()
        print(f"Found delivery date: {delivery_date}")
    
    # Extract meals using the actual Home Chef link pattern
    # Pattern: <a href="link" target="_blank" style="color:#4a4a4a; font-weight:bold; text-decoration:none;">Meal Name</a>
    meal_pattern = r'<a\s+href="([^"]*)"[^>]*style="[^"]*color:\s*#4a4a4a[^"]*font-weight:\s*bold[^"]*"[^>]*>([^<]+)</a>'
    meal_matches = re.findall(meal_pattern, html_content, re.IGNORECASE | re.DOTALL)
    
    for link, meal_name in meal_matches:
        # Clean up meal name
        meal_name = meal_name.strip().replace('\r\n', ' ').replace('\n', ' ').replace('  ', ' ')
        
        # Skip obviously non-meal links
        # Common navigation/non-meal terms to exclude
        excluded_terms = {
            'menu', 'account', 'recipe', 'contact', 'help', 'support', 
            'unsubscribe', 'view', 'browse', 'shop', 'order', 'delivery',
            'preferences', 'settings', 'login', 'sign', 'facebook', 'twitter',
            'instagram', 'app', 'download'
        }
        
        meal_name_lower = meal_name.lower().strip()
        is_excluded = any(term in meal_name_lower for term in excluded_terms)
        
        if len(meal_name) > 3 and not is_excluded:
            meals.append({
                'name': meal_name,
                'delivery_date': delivery_date,
                'recipe_link': link,
                'is_tracking_link': 'click.e.homechef.com' in link
            })
            print(f"Found meal: {meal_name}")
            print(f"  Link: {link}")
        else:
            print(f"Filtered out non-meal link: {meal_name}")
    
    print(f"Total meals extracted: {len(meals)}")
    return meals

def store_meals_via_api(meals: list, api_url: str) -> bool:
    """Store parsed meals using our own API"""
    try:
        # For now, store each meal individually
        # You could batch this later
        for meal in meals:
            payload = {
                'name': meal['name'],
                'delivery_date': meal['delivery_date'],
                'recipe_link': meal['recipe_link'],
                'source': 'home_chef_email'
            }
            
            response = requests.post(f"{api_url}/meals/setup", 
                                   json=payload, 
                                   timeout=30)
            
            if response.status_code not in [200, 201]:
                print(f"Failed to store meal {meal['name']}: {response.status_code}")
                return False
            else:
                print(f"Successfully stored meal: {meal['name']}")
        
        return True
        
    except Exception as e:
        print(f"Error storing meals via API: {str(e)}")
        return False
    
def calculate_week_of(delivery_date_str: str) -> str:
    """Calculate the Monday of the delivery week from delivery date string"""
    try:
        # Parse "Thursday, July 3" format - need to add year
        current_year = datetime.now().year
        
        # Handle different date formats
        if ',' in delivery_date_str:
            # "Thursday, July 3" format
            date_part = delivery_date_str.split(', ')[1]  # "July 3"
            date_obj = datetime.strptime(f"{date_part} {current_year}", "%B %d %Y")
        else:
            # Fallback for other formats
            date_obj = datetime.strptime(f"{delivery_date_str} {current_year}", "%B %d %Y")
        
        # Calculate Monday of that week
        monday = date_obj - timedelta(days=date_obj.weekday())
        return monday.strftime("%Y-%m-%d")
        
    except Exception as e:
        print(f"Error calculating week_of from {delivery_date_str}: {e}")
        # Fallback to current week's Monday
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        return monday.strftime("%Y-%m-%d")
    