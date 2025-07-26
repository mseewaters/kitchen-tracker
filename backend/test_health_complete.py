import requests
import json

API_BASE_URL = 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod'

def test_health_completion():
    print("Testing health item completion...")
    
    # First get a health item from dashboard
    dashboard_response = requests.get(f"{API_BASE_URL}/dashboard/today")
    
    if dashboard_response.status_code != 200:
        print("❌ Dashboard not available")
        return False
    
    dashboard_data = dashboard_response.json()
    health_items = [item for item in dashboard_data['items'] if item['type'] == 'health' and item['status'] == 'pending']
    
    if not health_items:
        print("ℹ️ No pending health items to test with")
        
        # Create a test health item
        print("Creating test health item...")
        create_response = requests.post(
            f"{API_BASE_URL}/health/items",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"name": "Test Health Item for Completion"})
        )
        
        if create_response.status_code == 201:
            health_item_id = create_response.json()['item_id']
            print(f"✅ Created test health item: {health_item_id}")
        else:
            print(f"❌ Failed to create test health item: {create_response.status_code}")
            return False
    else:
        health_item_id = health_items[0]['id']
        print(f"Using existing health item: {health_item_id}")
    
    # Test completing the health item
    complete_payload = {
        "id": health_item_id,
        "type": "health",
        "completed_by": "test_user",
        "notes": "Completed via health test"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps(complete_payload)
    )
    
    print(f"Complete Response Status: {response.status_code}")
    print(f"Complete Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Health completion successful!")
        print(f"   Record ID: {data.get('record_id')}")
        return True
    elif response.status_code == 502:
        print("❌ 502 error - Health completion logic has issues")
        return False
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        return False

def test_non_health_rejection():
    print("\nTesting non-health item rejection...")
    
    # Test with task type (should be rejected in test mode)
    complete_payload = {
        "id": "test-id",
        "type": "task",
        "completed_by": "test_user"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps(complete_payload)
    )
    
    print(f"Task Rejection Status: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Non-health items properly rejected")
        return True
    else:
        print("❌ Should have rejected non-health items")
        return False

if __name__ == "__main__":
    success1 = test_health_completion()
    success2 = test_non_health_rejection()
    
    if success1 and success2:
        print("\n🎉 Health completion works! Ready to add task and pet logic.")
    else:
        print("\n❌ Health completion has issues.")