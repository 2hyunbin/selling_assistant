"""
Simple API test script
Run this after starting the server (python main.py)
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_get_listings():
    """Test get listings endpoint"""
    print("Testing GET /listings...")
    response = requests.get(f"{BASE_URL}/listings")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} listings")
    if data:
        print(f"First listing: {data[0]['title']}\n")


def test_chat():
    """Test chat endpoint"""
    test_messages = [
        "안녕",
        "내 매물 보여줘",
        "어제 올린 물건 가격 10% 낮춰줘"
    ]

    for message in test_messages:
        print(f"\nTesting POST /chat with: '{message}'...")
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message}
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data['response'][:100]}...")
            print(f"   Actions taken: {len(data['actions_taken'])}")
            if data['actions_taken']:
                for action in data['actions_taken']:
                    print(f"   - {action['tool']}: {action['result'].get('message', 'OK')}")
        else:
            print(f"❌ Error: {response.text}")
        print()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing API Endpoints")
    print("=" * 60)
    print("\nMake sure server is running: python main.py\n")

    try:
        test_health()
        test_get_listings()
        test_chat()  # Testing function calling

        print("✅ All API tests passed!")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("   Make sure server is running: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")
