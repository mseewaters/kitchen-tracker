import requests
import json

API_BASE_URL = 'https://pww22u41ud.execute-api.us-east-1.amazonaws.com/Prod'

def test_minimal_complete():
    print("Testing minimal complete endpoint...")
    
    response = requests.post(
        f"{API_BASE_URL}/complete",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"test": "data"})
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        print("✅ Minimal complete endpoint works!")
        return True
    elif response.status_code == 502:
        print("❌ 502 error - Lambda function broken")
        return False
    elif response.status_code == 403:
        print("❌ 403 error - Endpoint not in SAM template")
        return False
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        return False

def test_minimal_history():
    print("\nTesting minimal history endpoint...")
    
    response = requests.get(f"{API_BASE_URL}/complete/history")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    success1 = test_minimal_complete()
    success2 = test_minimal_history()
    
    if success1 and success2:
        print("\n🎉 Minimal Complete API works! Ready to add real logic.")
    else:
        print("\n❌ Still have issues to debug.")