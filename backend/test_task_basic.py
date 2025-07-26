import requests
import json
import os

# Get API URL from environment or use your deployed URL
API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

def test_basic_task_creation():
    """Quick test to verify task API is working"""
    
    print("Testing task creation...")
    
    # Test creating a weekly task
    payload = {
        "name": "Take out trash",
        "frequency": "weekly",
        "day_of_week": 6  # Sunday
    }
    
    response = requests.post(
        f"{API_BASE_URL}/tasks/setup",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Task created successfully: {data['name']}")
        print(f"   Task ID: {data['task_id']}")
        print(f"   Frequency: {data['frequency']}")
        return data['task_id']
    else:
        print(f"❌ Failed to create task: {response.status_code}")
        return None

def test_get_tasks():
    """Test getting all tasks"""
    print("\nTesting get all tasks...")
    
    response = requests.get(f"{API_BASE_URL}/tasks")
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data)} tasks")
        for task in data:
            print(f"   - {task['name']} ({task['frequency']}) - Status: {task['status']}")
    else:
        print(f"❌ Failed to get tasks: {response.status_code}")

if __name__ == "__main__":
    # Basic smoke test
    task_id = test_basic_task_creation()
    test_get_tasks()
    
    if task_id:
        print(f"\n🎉 Task API basic functionality works!")
    else:
        print(f"\n❌ Task API has issues")