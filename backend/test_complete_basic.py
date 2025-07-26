import requests
import json
import os

API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

def test_universal_complete():
    """Test the universal completion endpoint"""
    print("⚡ Testing Universal Complete API...")
    
    # First, get some items from the dashboard to complete
    dashboard_response = requests.get(f"{API_BASE_URL}/dashboard/today")
    
    if dashboard_response.status_code != 200:
        print("❌ Dashboard not available for testing")
        return False
    
    dashboard_data = dashboard_response.json()
    pending_items = [item for item in dashboard_data['items'] if item['status'] == 'pending']
    
    if not pending_items:
        print("ℹ️ No pending items found to complete")
        return True
    
    # Test completing different types of items
    test_item = pending_items[0]
    
    print(f"Testing completion of: {test_item['name']} ({test_item['type']})")
    
    # Complete the item using universal endpoint
    complete_payload = {
        "id": test_item['id'],
        "type": test_item['type'],
        "completed_by": "universal_test_user",
        "notes": "Completed via universal endpoint"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps(complete_payload)
    )
    
    print(f"Complete Response Status: {response.status_code}")
    print(f"Complete Response Body: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Universal completion successful!")
        print(f"   Item ID: {data['item_id']}")
        print(f"   Type: {data['type']}")
        print(f"   Completed By: {data['completed_by']}")
        print(f"   Record ID: {data.get('record_id')}")
        return True
    else:
        print(f"❌ Universal completion failed: {response.status_code}")
        return False

def test_completion_history():
    """Test the completion history endpoint"""
    print(f"\n📜 Testing Completion History...")
    
    response = requests.get(f"{API_BASE_URL}/complete/history")
    
    print(f"History Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ History loaded successfully!")
        print(f"   Period: {data['period_days']} days")
        print(f"   Total completions: {len(data['completions'])}")
        
        if data['completions']:
            print(f"   Recent completions:")
            for completion in data['completions'][:5]:  # Show first 5
                print(f"     - {completion['item_name']} ({completion['type']}) on {completion['date']}")
                if completion['completed_by']:
                    print(f"       by {completion['completed_by']}")
        
        return True
    else:
        print(f"❌ History failed: {response.status_code}")
        return False

def test_custom_history_period():
    """Test history with custom period"""
    print(f"\n📅 Testing Custom History Period...")
    
    response = requests.get(f"{API_BASE_URL}/complete/history?days=1")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Custom period works: {data['period_days']} day(s)")
        print(f"   Today's completions: {len(data['completions'])}")
        return True
    else:
        print(f"❌ Custom period failed: {response.status_code}")
        return False

def test_invalid_complete_request():
    """Test error handling"""
    print(f"\n❗ Testing Error Handling...")
    
    # Test with invalid type
    invalid_payload = {
        "id": "test-id",
        "type": "invalid_type"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps(invalid_payload)
    )
    
    if response.status_code == 400:
        print(f"✅ Invalid type properly rejected: {response.status_code}")
        error_data = response.json()
        print(f"   Error message: {error_data.get('error')}")
        return True
    else:
        print(f"❌ Error handling failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Quick Complete API")
    print("=" * 50)
    
    success1 = test_universal_complete()
    success2 = test_completion_history()
    success3 = test_custom_history_period()
    success4 = test_invalid_complete_request()
    
    if all([success1, success2, success3, success4]):
        print(f"\n🎉 Quick Complete API is working perfectly!")
        print(f"Your frontend now has:")
        print(f"  ✅ Universal 'tap to complete' endpoint")
        print(f"  ✅ Cross-domain completion history")
        print(f"  ✅ Proper error handling")
    else:
        print(f"\n❌ Some Quick Complete API features need fixing")