from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from datetime import date, datetime
import json
import os
import sys

print("Starting app.py module...")  # Debug

# For Lambda, we need to use absolute imports by fixing the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import your existing models and services with better error handling
try:
    print("Importing models and services...")
    from models.family_member import FamilyMember  
    from models.recurring_activity import RecurringActivity
    from models.activity_completion import ActivityCompletion
    from services.kitchen_service import KitchenService
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
    # Let's try a different approach - import each one individually
    try:
        print("Trying individual imports...")
        sys.path.insert(0, current_dir)
        from models.family_member import FamilyMember
        print("✓ FamilyMember imported")
        from models.recurring_activity import RecurringActivity
        print("✓ RecurringActivity imported") 
        from models.activity_completion import ActivityCompletion
        print("✓ ActivityCompletion imported")
        from services.kitchen_service import KitchenService
        print("✓ KitchenService imported")
        print("Individual imports successful!")
    except ImportError as e2:
        print(f"Individual imports also failed: {e2}")
        raise e2

from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="Kitchen Tracker API",
    version="1.0.0",
    description="Family activity and task tracking system"
)

print("FastAPI app created!")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
        "https://main.d2d1lfimravh2k.amplifyapp.com",
        "https://dev.d2d1lfimravh2k.amplifyapp.com",
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

# Lambda handler for AWS
def lambda_handler(event, context):
    """AWS Lambda handler"""
    print(f"Received event: {event}")  # Debug logging
    try:
        from mangum import Mangum
        
        # Create Mangum handler - don't specify api_gateway_base_path
        handler = Mangum(app)
        result = handler(event, context)
        print(f"Mangum result: {result}")  # Debug the response
        return result
    except Exception as e:
        print(f"Handler error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500, 
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Handler error: {str(e)}"})
        }