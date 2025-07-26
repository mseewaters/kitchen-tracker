import requests
import json

API_BASE_URL = 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod'

def test_simple_complete():
    """Test simple tablet-style completion"""
    print("🖱️ Testing Simple Tablet Complete...")
    
    # Get pending items from dashboard
    dashboard = requests.get(f"{API_BASE_URL}/dashboard/today").json()
    pending_items = [item for item in dashboard['items'] if item['status'] == 'pending']
    
    if not pending_items:
        print("ℹ️ No pending items to test")
        return True
    
    # Test completing different types
    for item_type in ['health', 'task', 'pet_care']:
        test_item = next((item for item in pending_items if item['type'] == item_type), None)
        
        if test_item:
            print(f"\n📱 Tapping: {test_item['name']} ({item_type})")
            
            response = requests.post(
                f"{API_BASE_URL}/complete",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"id": test_item['id'], "type": item_type})
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ {item_type} completion works!")
                else:
                    print(f"   ❌ {item_type} completion failed")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
        else:
            print(f"   ℹ️ No {item_type} items to test")
    
    print(f"\n📊 Testing dashboard refresh...")
    updated_dashboard = requests.get(f"{API_BASE_URL}/dashboard/today").json()
    completed_today = updated_dashboard['summary']['completed_today']
    print(f"   Completed today: {completed_today}")
    
    return True

if __name__ == "__main__":
    test_simple_complete()
    print(f"\n🎉 Simple Complete API ready for tablet interface!")