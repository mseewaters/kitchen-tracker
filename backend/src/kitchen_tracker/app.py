import json
import os
from typing import Dict, Any, Optional
from datetime import date, datetime
import boto3

from models.family_member import FamilyMember  
from models.recurring_activity import RecurringActivity
from models.activity_completion import ActivityCompletion
from services.kitchen_service import KitchenService

# Initialize service
kitchen_service = KitchenService()

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
        
        # Parse body if present
        body = None
        if event.get('body'):
            body = json.loads(event['body'])
        
        # Extract household_id from query parameters or use default
        query_params = event.get('queryStringParameters') or {}
        household_id = query_params.get('household_id', 'default')
        
        # Basic health check
        if path == '/' and method == 'GET':
            return create_response(200, {'message': 'kitchen-tracker API is running!'}, headers)
        
        # Dashboard endpoint - returns complete dashboard data
        elif path == '/dashboard' and method == 'GET':
            dashboard_data = kitchen_service.get_dashboard_data(household_id)
            return create_response(200, dashboard_data, headers)
        
        # Family Members endpoints
        elif path == '/family-members' and method == 'GET':
            members = kitchen_service.get_family_members(household_id)
            return create_response(200, [m.to_dict() for m in members], headers)
        
        elif path == '/family-members' and method == 'POST':
            if not body:
                return create_response(400, {'error': 'Request body required'}, headers)
            
            member = kitchen_service.create_family_member(
                name=body['name'],
                member_type=body['member_type'],
                household_id=household_id,
                pet_type=body.get('pet_type')
            )
            return create_response(201, member.to_dict(), headers)
        
        elif path.startswith('/family-members/') and method == 'GET':
            member_id = path.split('/')[-1]
            member = kitchen_service.get_family_member(member_id)
            if not member:
                return create_response(404, {'error': 'Family member not found'}, headers)
            return create_response(200, member.to_dict(), headers)
        
        elif path.startswith('/family-members/') and method == 'PUT':
            member_id = path.split('/')[-1]
            if not body:
                return create_response(400, {'error': 'Request body required'}, headers)
            
            # Get existing member
            existing_member = kitchen_service.get_family_member(member_id)
            if not existing_member:
                return create_response(404, {'error': 'Family member not found'}, headers)
            
            # Update fields
            existing_member.name = body.get('name', existing_member.name)
            existing_member.member_type = body.get('member_type', existing_member.member_type)
            existing_member.pet_type = body.get('pet_type', existing_member.pet_type)
            existing_member.is_active = body.get('is_active', existing_member.is_active)
            
            updated_member = kitchen_service.update_family_member(existing_member)
            return create_response(200, updated_member.to_dict(), headers)
        
        elif path.startswith('/family-members/') and method == 'DELETE':
            member_id = path.split('/')[-1]
            success = kitchen_service.delete_family_member(member_id)
            if not success:
                return create_response(404, {'error': 'Family member not found'}, headers)
            return create_response(204, {}, headers)
        
        # Activities endpoints
        elif path == '/activities' and method == 'GET':
            activities_with_status = kitchen_service.get_activities_with_status(household_id)
            return create_response(200, activities_with_status, headers)
        
        elif path == '/activities' and method == 'POST':
            if not body:
                return create_response(400, {'error': 'Request body required'}, headers)
            
            activity = kitchen_service.create_activity(
                name=body['name'],
                assigned_to=body['assigned_to'],
                frequency=body['frequency'],
                household_id=household_id,
                frequency_config=body.get('frequency_config', {}),
                category=body.get('category')
            )
            
            # Return with status information
            activity_status = kitchen_service.get_activity_status(activity.activity_id)
            return create_response(201, activity_status.to_dict(), headers)
        
        elif path.startswith('/activities/') and method == 'GET':
            activity_id = path.split('/')[-1]
            activity_status = kitchen_service.get_activity_status(activity_id)
            if not activity_status:
                return create_response(404, {'error': 'Activity not found'}, headers)
            return create_response(200, activity_status.to_dict(), headers)
        
        elif path.startswith('/activities/') and method == 'PUT':
            activity_id = path.split('/')[-1]
            if not body:
                return create_response(400, {'error': 'Request body required'}, headers)
            
            # Get existing activity
            existing_activity = kitchen_service.get_activity(activity_id)
            if not existing_activity:
                return create_response(404, {'error': 'Activity not found'}, headers)
            
            # Update fields
            existing_activity.name = body.get('name', existing_activity.name)
            existing_activity.assigned_to = body.get('assigned_to', existing_activity.assigned_to)
            existing_activity.frequency = body.get('frequency', existing_activity.frequency)
            existing_activity.frequency_config = body.get('frequency_config', existing_activity.frequency_config)
            existing_activity.category = body.get('category', existing_activity.category)
            existing_activity.is_active = body.get('is_active', existing_activity.is_active)
            
            updated_activity = kitchen_service.update_activity(existing_activity)
            activity_status = kitchen_service.get_activity_status(updated_activity.activity_id)
            return create_response(200, activity_status.to_dict(), headers)
        
        elif path.startswith('/activities/') and method == 'DELETE':
            activity_id = path.split('/')[-1]
            success = kitchen_service.delete_activity(activity_id)
            if not success:
                return create_response(404, {'error': 'Activity not found'}, headers)
            return create_response(204, {}, headers)
        
        # Activity completion endpoints
        elif path.startswith('/activities/') and path.endswith('/complete') and method == 'POST':
            activity_id = path.split('/')[-2]  # Extract from /activities/{id}/complete
            
            # Get the activity to find assigned member
            activity = kitchen_service.get_activity(activity_id)
            if not activity:
                return create_response(404, {'error': 'Activity not found'}, headers)
            
            completion = kitchen_service.complete_activity(
                activity_id=activity_id,
                member_id=activity.assigned_to,
                household_id=household_id,
                completion_date=body.get('completion_date') if body else None,
                completed_by=body.get('completed_by') if body else None,
                notes=body.get('notes') if body else None
            )
            return create_response(201, completion.to_dict(), headers)
        
        elif path.startswith('/activities/') and path.endswith('/undo') and method == 'POST':
            activity_id = path.split('/')[-2]  # Extract from /activities/{id}/undo
            completion_date = body.get('completion_date') if body else None
            
            success = kitchen_service.undo_activity_completion(activity_id, completion_date)
            if not success:
                return create_response(404, {'error': 'No completion found to undo'}, headers)
            return create_response(204, {}, headers)
        
        # Member-specific endpoints
        elif path.startswith('/family-members/') and '/activities' in path and method == 'GET':
            member_id = path.split('/')[-2]  # Extract from /family-members/{id}/activities
            activities = kitchen_service.get_activities_for_member(member_id, household_id)
            activities_with_status = []
            for activity in activities:
                status = kitchen_service.get_activity_status(activity.activity_id)
                if status:
                    activities_with_status.append(status.to_dict())
            return create_response(200, activities_with_status, headers)
        
        # Summary endpoints
        elif path == '/summary' and method == 'GET':
            summary = kitchen_service.get_household_summary(household_id)
            return create_response(200, summary, headers)
        
        elif path == '/activities/due-today' and method == 'GET':
            due_today = kitchen_service.get_activities_due_today(household_id)
            return create_response(200, due_today, headers)
        
        elif path == '/activities/overdue' and method == 'GET':
            overdue = kitchen_service.get_overdue_activities(household_id)
            return create_response(200, overdue, headers)
        
        elif path == '/activities/completed-today' and method == 'GET':
            completed_today = kitchen_service.get_completed_activities_today(household_id)
            return create_response(200, completed_today, headers)
        
        # If no route matches
        else:
            return create_response(404, {'error': 'Endpoint not found'}, headers)
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_response(500, {'error': 'Internal server error'}, headers)

def create_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Helper to create consistent API responses"""
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, default=str)  # default=str handles date serialization
    }