#!/usr/bin/env python3
"""
Comprehensive test for all kitchen-tracker API endpoints
"""

import requests
import json

API_BASE_URL = "https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod"

def test_family_members():
    print("🏠 Testing Family Members API")
    
    # Create a person
    person_data = {
        "name": "John Doe",
        "member_type": "person",
        "is_active": True
    }
    response = requests.post(f"{API_BASE_URL}/family-members", json=person_data)
    print(f"CREATE Person: {response.status_code}")
    if response.status_code == 200:
        person = response.json()
        person_id = person["member_id"]
        print(f"✅ Created person: {person['name']}")
        
        # Update person
        update_data = {"name": "John Updated"}
        response = requests.put(f"{API_BASE_URL}/family-members/{person_id}", json=update_data)
        print(f"UPDATE Person: {response.status_code}")
        
        # Get person
        response = requests.get(f"{API_BASE_URL}/family-members/{person_id}")
        print(f"GET Person: {response.status_code}")
        
        return person_id
    return None

def test_activities(person_id):
    print("\n📋 Testing Activities API")
    
    if not person_id:
        print("❌ Skipping activities - no person created")
        return None
    
    # Create activity
    activity_data = {
        "name": "Take morning medication",
        "assigned_to": person_id,
        "frequency": "daily",
        "category": "health",
        "is_active": True
    }
    response = requests.post(f"{API_BASE_URL}/activities", json=activity_data)
    print(f"CREATE Activity: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return None
    
    activity = response.json()
    activity_id = activity.get("activity_id")
    print(f"✅ Created activity: {activity.get('name')}")
    
    # Get activities
    response = requests.get(f"{API_BASE_URL}/activities")
    print(f"GET Activities: {response.status_code}")
    
    # Get specific activity
    response = requests.get(f"{API_BASE_URL}/activities/{activity_id}")
    print(f"GET Activity: {response.status_code}")
    
    # Complete activity
    completion_data = {
        "completed_by": "John",
        "notes": "Completed successfully"
    }
    response = requests.post(f"{API_BASE_URL}/activities/{activity_id}/complete", json=completion_data)
    print(f"COMPLETE Activity: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
    
    return activity_id

def test_dashboard():
    print("\n📊 Testing Dashboard Endpoints")
    
    # Dashboard
    response = requests.get(f"{API_BASE_URL}/dashboard")
    print(f"GET Dashboard: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
    
    # Summary
    response = requests.get(f"{API_BASE_URL}/summary")
    print(f"GET Summary: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
    
    # Due today
    response = requests.get(f"{API_BASE_URL}/activities/due-today")
    print(f"GET Due Today: {response.status_code}")
    
    # Overdue
    response = requests.get(f"{API_BASE_URL}/activities/overdue")
    print(f"GET Overdue: {response.status_code}")
    
    # Completed today
    response = requests.get(f"{API_BASE_URL}/activities/completed-today")
    print(f"GET Completed Today: {response.status_code}")

def test_cleanup(person_id, activity_id):
    print("\n🧹 Testing Cleanup")
    
    if activity_id:
        response = requests.delete(f"{API_BASE_URL}/activities/{activity_id}")
        print(f"DELETE Activity: {response.status_code}")
    
    if person_id:
        response = requests.delete(f"{API_BASE_URL}/family-members/{person_id}")
        print(f"DELETE Person: {response.status_code}")

def main():
    print("🧪 Comprehensive API Test")
    print("=" * 50)
    
    # Test root
    response = requests.get(f"{API_BASE_URL}/")
    print(f"ROOT: {response.status_code}")
    
    # Test all endpoints
    person_id = test_family_members()
    activity_id = test_activities(person_id)
    test_dashboard()
    test_cleanup(person_id, activity_id)
    
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    main()