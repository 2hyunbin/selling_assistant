"""
Test script for LLM Agent
Requires Gemini API key in config.py
"""
import asyncio
from agent import agent
from config import GEMINI_API_KEY


async def test_agent():
    """Test agent with various scenarios"""

    # Check API key
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("❌ Error: Please set your Gemini API key in backend/config.py")
        print("   Edit line 9: GEMINI_API_KEY = 'your_actual_api_key'")
        return

    print("=" * 60)
    print("🤖 Testing LLM Agent")
    print("=" * 60)

    test_cases = [
        "어제 올린 물건 보여줘",
        "전자기기 시세 알려줘",
        "맥북 가격 10% 낮춰줘",
        "가장 오래된 매물 끌어올려줘",
        "안녕! 뭘 도와줄 수 있어?",
    ]

    for idx, message in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {idx}: {message}")
        print(f"{'='*60}")

        try:
            result = await agent.process_message(message)

            print(f"\n🎯 Intent: {result['intent']}")
            print(f"\n💭 Reasoning:\n{result['reasoning']}")
            print(f"\n🤖 Response:\n{result['response']}")

            if result['actions_taken']:
                print(f"\n⚙️ Actions Taken:")
                for action in result['actions_taken']:
                    print(f"   - {action['tool']}: {action['result'].get('message', 'Done')}")

            if result['suggested_actions']:
                print(f"\n💡 Suggested Actions:")
                for action in result['suggested_actions']:
                    print(f"   - [{action['label']}]")

            if result['updated_listings']:
                print(f"\n📝 Updated Listings: {result['updated_listings']}")

        except Exception as e:
            print(f"\n❌ Error: {e}")

        # Wait between requests to avoid rate limiting
        if idx < len(test_cases):
            print("\n⏳ Waiting 2 seconds...")
            await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("✅ All agent tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent())
