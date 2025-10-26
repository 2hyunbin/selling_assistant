"""
Test chat context/history
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_context():
    """Test conversation context is maintained"""
    history = []

    # Message 1: "어제 올린 물건 보여줘"
    print("\n" + "="*60)
    print("📤 Message 1: 어제 올린 물건 보여줘")
    print("="*60)

    response1 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "어제 올린 물건 보여줘", "history": history}
    )
    result1 = response1.json()
    print(f"✅ Response: {result1['response'][:200]}...")

    # Update history
    history.append({"role": "user", "content": "어제 올린 물건 보여줘"})
    history.append({"role": "assistant", "content": result1['response']})

    # Message 2: "유니클로 니트가 잘 안팔리는데 어떻게 하지"
    print("\n" + "="*60)
    print("📤 Message 2: 유니클로 니트가 잘 안팔리는데 어떻게 하지")
    print("="*60)

    response2 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "유니클로 니트가 잘 안팔리는데 어떻게 하지", "history": history}
    )
    result2 = response2.json()
    print(f"✅ Response: {result2['response'][:200]}...")

    # Update history
    history.append({"role": "user", "content": "유니클로 니트가 잘 안팔리는데 어떻게 하지"})
    history.append({"role": "assistant", "content": result2['response']})

    # Message 3: "제목 수정할래 추천해줘"
    print("\n" + "="*60)
    print("📤 Message 3: 제목 수정할래 추천해줘")
    print("="*60)
    print(f"📝 History size: {len(history)} messages")

    response3 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "제목 수정할래 추천해줘", "history": history}
    )
    result3 = response3.json()
    print(f"✅ Response: {result3['response'][:300]}...")
    print(f"🔧 Actions taken: {len(result3['actions_taken'])}")

    if "유니클로" in result3['response'] or "니트" in result3['response'] or "ID 8" in result3['response']:
        print("\n🎉 SUCCESS! Context is maintained - agent remembers we're talking about 유니클로 니트!")
    else:
        print("\n⚠️  Context might not be fully maintained")

if __name__ == "__main__":
    try:
        test_context()
    except Exception as e:
        print(f"❌ Error: {e}")
