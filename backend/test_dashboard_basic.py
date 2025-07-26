import requests
import json
import os

API_BASE_URL = os.environ.get('API_URL', 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod')

def test_dashboard_today():
    """Test the main dashboard endpoint"""
    print("🏠 Testing Dashboard Today...")
    
    response = requests.get(f"{API_BASE_URL}/dashboard/today")
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Dashboard loaded successfully!")
        print(f"📅 Date: {data['today']}")
        print(f"📊 Summary:")
        print(f"   Total Items: {data['summary']['total_items']}")
        print(f"   Completed: {data['summary']['completed_today']}")
        print(f"   Pending: {data['summary']['pending']}")
        print(f"   Overdue: {data['summary']['overdue']}")
        
        print(f"\n📋 Items ({len(data['items'])}):")
        for item in data['items'][:5]:  # Show first 5 items
            print(f"   - {item['name']} ({item['type']}) - {item['status']}")
            if item['person']:
                print(f"     👤 Person: {item['person']}")
            if item['pet']:
                print(f"     🐕 Pet: {item['pet']}")
        
        if len(data['items']) > 5:
            print(f"   ... and {len(data['items']) - 5} more items")
        
        print(f"\n🍽️ Meals:")
        print(f"   Available to cook: {data['meals']['available_to_cook']}")
        print(f"   Cooked this week: {data['meals']['cooked_this_week']}")
        
        if data['meals']['delivered']:
            print(f"   Delivered meals:")
            for meal in data['meals']['delivered'][:3]:
                print(f"     - {meal['name']}")
        
        return True
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Raw error: {response.text}")
        return False

def test_dashboard_overdue():
    """Test the overdue summary"""
    print(f"\n⏰ Testing Dashboard Overdue...")
    
    response = requests.get(f"{API_BASE_URL}/dashboard/overdue")
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Overdue summary: {data['total_overdue']} overdue items")
        
        if data['items']:
            print("Overdue items:")
            for item in data['items']:
                print(f"   - {item['name']} ({item['type']})")
    else:
        print(f"❌ Overdue endpoint failed: {response.status_code}")

def test_dashboard_trends():
    """Test the completion trends"""
    print(f"\n📈 Testing Dashboard Trends...")
    
    response = requests.get(f"{API_BASE_URL}/dashboard/trends?days=3")
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Trends for {data['period_days']} days:")
        
        for trend in data['trends']:
            print(f"   {trend['date']}: {trend['total_completions']} completions")
    else:
        print(f"❌ Trends endpoint failed: {response.status_code}")

if __name__ == "__main__":
    success = test_dashboard_today()
    test_dashboard_overdue()
    test_dashboard_trends()
    
    if success:
        print(f"\n🎉 Dashboard API is working! Ready for comprehensive testing.")
    else:
        print(f"\n❌ Dashboard API has issues that need fixing.")