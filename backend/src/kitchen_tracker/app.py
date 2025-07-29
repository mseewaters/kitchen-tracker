from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from typing import Optional, Dict, Any, List
from datetime import date, datetime
import json
import os

print("Starting app.py module...")  # Debug

# Import your existing models and services (works in both Lambda and test environments)
try:
    # Try absolute imports first (works in Lambda)
    print("Trying absolute imports...")
    from models.family_member import FamilyMember  
    from models.recurring_activity import RecurringActivity
    from models.activity_completion import ActivityCompletion
    from services.kitchen_service import KitchenService
    print("Absolute imports successful!")
except ImportError as e:
    # Fall back to relative imports (works in tests)
    print(f"Absolute imports failed: {e}")
    print("Trying relative imports...")
    from .models.family_member import FamilyMember  
    from .models.recurring_activity import RecurringActivity
    from .models.activity_completion import ActivityCompletion
    from .services.kitchen_service import KitchenService
    print("Relative imports successful!")

from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="Kitchen Tracker API",
    version="1.0.0",
    description="Family activity and task tracking system"
)

print("FastAPI app created!")

# Add CORS middleware - put this right after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "https://main.d2ku093eyfpjks.amplifyapp.com",
        "*"  # Allow all origins for now - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
kitchen_service = KitchenService()

# Pydantic models for request/response
class FamilyMemberCreate(BaseModel):
    name: str
    member_type: str
    pet_type: Optional[str] = None
    is_active: bool = True

class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    member_type: Optional[str] = None
    pet_type: Optional[str] = None
    is_active: Optional[bool] = None

class ActivityCreate(BaseModel):
    name: str
    assigned_to: str
    frequency: str
    frequency_config: Optional[Dict] = {}
    category: Optional[str] = None
    is_active: bool = True

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    assigned_to: Optional[str] = None
    frequency: Optional[str] = None
    frequency_config: Optional[Dict] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class ActivityCompletionRequest(BaseModel):
    completion_date: Optional[str] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Kitchen Tracker API is running!"}

# Family Members endpoints
@app.get("/family-members")
async def get_family_members(household_id: str = Query(default="default")):
    """Get all family members for a household"""
    try:
        members = kitchen_service.get_family_members(household_id)
        return [member.to_dict() for member in members]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/family-members")
async def create_family_member(
    member: FamilyMemberCreate,
    household_id: str = Query(default="default")
):
    """Create a new family member"""
    try:
        new_member = kitchen_service.create_family_member(
            name=member.name,
            member_type=member.member_type,
            household_id=household_id,
            pet_type=member.pet_type
        )
        return new_member.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/family-members/{member_id}")
async def get_family_member(member_id: str):
    """Get a specific family member"""
    try:
        member = kitchen_service.get_family_member(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Family member not found")
        return member.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/family-members/{member_id}")
async def update_family_member(member_id: str, member_update: FamilyMemberUpdate):
    """Update a family member"""
    try:
        # Get existing member
        existing_member = kitchen_service.get_family_member(member_id)
        if not existing_member:
            raise HTTPException(status_code=404, detail="Family member not found")
        
        # Update fields that were provided
        if member_update.name is not None:
            existing_member.name = member_update.name
        if member_update.member_type is not None:
            existing_member.member_type = member_update.member_type
        if member_update.pet_type is not None:
            existing_member.pet_type = member_update.pet_type
        if member_update.is_active is not None:
            existing_member.is_active = member_update.is_active
        
        updated_member = kitchen_service.update_family_member(existing_member)
        return updated_member.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/family-members/{member_id}")
async def delete_family_member(member_id: str):
    """Delete a family member"""
    try:
        success = kitchen_service.delete_family_member(member_id)
        if not success:
            raise HTTPException(status_code=404, detail="Family member not found")
        return {"message": "Family member deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activities endpoints
@app.get("/activities")
async def get_activities(household_id: str = Query(default="default")):
    """Get all activities with status for a household"""
    try:
        activities_with_status = kitchen_service.get_activities_with_status(household_id)
        return activities_with_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/activities")
async def create_activity(
    activity: ActivityCreate,
    household_id: str = Query(default="default")
):
    """Create a new recurring activity"""
    try:
        new_activity = kitchen_service.create_activity(
            name=activity.name,
            assigned_to=activity.assigned_to,
            frequency=activity.frequency,
            household_id=household_id,
            frequency_config=activity.frequency_config,
            category=activity.category
        )
        
        # Return with status information
        activity_status = kitchen_service.get_activity_status(new_activity.activity_id)
        return activity_status.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activities/{activity_id}")
async def get_activity(activity_id: str):
    """Get a specific activity with status"""
    try:
        activity_status = kitchen_service.get_activity_status(activity_id)
        if not activity_status:
            raise HTTPException(status_code=404, detail="Activity not found")
        return activity_status.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/activities/{activity_id}")
async def update_activity(activity_id: str, activity_update: ActivityUpdate):
    """Update a recurring activity"""
    try:
        # Get existing activity
        existing_activity = kitchen_service.get_activity(activity_id)
        if not existing_activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Update fields that were provided
        if activity_update.name is not None:
            existing_activity.name = activity_update.name
        if activity_update.assigned_to is not None:
            existing_activity.assigned_to = activity_update.assigned_to
        if activity_update.frequency is not None:
            existing_activity.frequency = activity_update.frequency
        if activity_update.frequency_config is not None:
            existing_activity.frequency_config = activity_update.frequency_config
        if activity_update.category is not None:
            existing_activity.category = activity_update.category
        if activity_update.is_active is not None:
            existing_activity.is_active = activity_update.is_active
        
        updated_activity = kitchen_service.update_activity(existing_activity)
        activity_status = kitchen_service.get_activity_status(updated_activity.activity_id)
        return activity_status.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/activities/{activity_id}")
async def delete_activity(activity_id: str):
    """Delete a recurring activity"""
    try:
        success = kitchen_service.delete_activity(activity_id)
        if not success:
            raise HTTPException(status_code=404, detail="Activity not found")
        return {"message": "Activity deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Activity completion endpoints
@app.post("/activities/{activity_id}/complete")
async def complete_activity(activity_id: str, completion: ActivityCompletionRequest):
    """Mark an activity as completed"""
    try:
        # Get the activity to find assigned member
        activity = kitchen_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        completion_record = kitchen_service.complete_activity(
            activity_id=activity_id,
            member_id=activity.assigned_to,
            household_id=activity.household_id,
            completion_date=completion.completion_date,
            completed_by=completion.completed_by,
            notes=completion.notes
        )
        return completion_record.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/activities/{activity_id}/undo")
async def undo_activity_completion(activity_id: str, completion: ActivityCompletionRequest):
    """Undo an activity completion"""
    try:
        success = kitchen_service.undo_activity_completion(
            activity_id, 
            completion.completion_date
        )
        if not success:
            raise HTTPException(status_code=404, detail="No completion found to undo")
        return {"message": "Activity completion undone successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Member-specific endpoints
@app.get("/family-members/{member_id}/activities")
async def get_member_activities(
    member_id: str, 
    household_id: str = Query(default="default")
):
    """Get all activities for a specific family member"""
    try:
        activities = kitchen_service.get_activities_for_member(member_id, household_id)
        activities_with_status = []
        for activity in activities:
            status = kitchen_service.get_activity_status(activity.activity_id)
            if status:
                activities_with_status.append(status.to_dict())
        return activities_with_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard and summary endpoints
@app.get("/dashboard")
async def get_dashboard(household_id: str = Query(default="default")):
    """Get complete dashboard data"""
    try:
        dashboard_data = kitchen_service.get_dashboard_data(household_id)
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary")
async def get_summary(household_id: str = Query(default="default")):
    """Get household summary"""
    try:
        summary = kitchen_service.get_household_summary(household_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activities/due-today")
async def get_activities_due_today(household_id: str = Query(default="default")):
    """Get activities due today"""
    try:
        due_today = kitchen_service.get_activities_due_today(household_id)
        return due_today
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activities/overdue")
async def get_overdue_activities(household_id: str = Query(default="default")):
    """Get overdue activities"""
    try:
        overdue = kitchen_service.get_overdue_activities(household_id)
        return overdue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activities/completed-today")
async def get_completed_activities_today(household_id: str = Query(default="default")):
    """Get activities completed today"""
    try:
        completed_today = kitchen_service.get_completed_activities_today(household_id)
        return completed_today
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lambda handler for AWS
def lambda_handler(event, context):
    """AWS Lambda handler"""
    print(f"Received event: {event}")  # Debug logging
    print(f"Path from API Gateway: {event.get('path', 'NO PATH')}")
    print(f"Raw path: {event.get('rawPath', 'NO RAW PATH')}")
    try:
        from mangum import Mangum
        
        # Configure Mangum to strip the API Gateway stage from the path
        handler = Mangum(app, api_gateway_base_path="/Prod")
        return handler(event, context)
    except Exception as e:
        print(f"Handler error: {e}")
        return {
            "statusCode": 500, 
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            },
            "body": json.dumps({"error": f"Handler error: {str(e)}"})
        }