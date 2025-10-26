"""
Test script for tool functions
"""
import asyncio
from tools import query_listings, adjust_price, boost_listing, update_content, get_market_insights


async def test_tools():
    """Test all tool functions"""

    print("=" * 60)
    print("🧪 Testing Tool Functions")
    print("=" * 60)

    # Test 1: Query Listings
    print("\n1️⃣ Test query_listings (어제 등록된 매물)")
    result = await query_listings(time_filter="yesterday")
    print(f"   Result: {result['message']}")
    if result['success'] and result['count'] > 0:
        print(f"   Found: {result['listings'][0]['title']}")

    # Test 2: Query by category
    print("\n2️⃣ Test query_listings (전자기기 카테고리)")
    result = await query_listings(category="전자기기")
    print(f"   Result: {result['message']}")

    # Test 3: Adjust Price
    print("\n3️⃣ Test adjust_price (ID 2번 매물 10% 인하)")
    result = await adjust_price(listing_id=2, new_price=2520000)  # 2800000 * 0.9
    print(f"   Result: {result['message']}")
    if result['success']:
        print(f"   Change: {result['change_percent']}%")

    # Test 4: Boost Listing
    print("\n4️⃣ Test boost_listing (ID 3번 매물)")
    result = await boost_listing(listing_id=3)
    print(f"   Result: {result['message']}")
    if result['success']:
        print(f"   Boost count: {result['boost_count']}")

    # Test 5: Boost Cooldown (should fail)
    print("\n5️⃣ Test boost_listing again (24시간 제한 테스트)")
    result = await boost_listing(listing_id=3)
    print(f"   Result: {result['message']}")
    if not result['success']:
        print(f"   ✅ Cooldown working: {result.get('warning', '')}")

    # Test 6: Update Content
    print("\n6️⃣ Test update_content (제목 수정)")
    result = await update_content(
        listing_id=4,
        title="아이폰 14 Pro 256GB 딥퍼플 급매!! [가격 협상 가능]"
    )
    print(f"   Result: {result['message']}")
    if result['success']:
        print(f"   Old: {result['old_title']}")
        print(f"   New: {result['new_title']}")

    # Test 7: Get Market Insights
    print("\n7️⃣ Test get_market_insights (전자기기 - 강남구)")
    result = await get_market_insights(category="전자기기", region="강남구")
    print(f"   Result: {result['message']}")
    if result['success']:
        print(f"   평균가: {result['average_price']:,}원")
        print(f"   평균 판매기간: {result['avg_sell_days']}일")
        print(f"   트렌드: {result['trend']}")
        print(f"   추천: {result['recommendation']}")

    # Test 8: Market Insights (다른 지역)
    print("\n8️⃣ Test get_market_insights (가구 - 서초구)")
    result = await get_market_insights(category="가구", region="서초구")
    print(f"   Result: {result['message']}")
    if result['success']:
        print(f"   평균가: {result['average_price']:,}원")
        print(f"   트렌드: {result['trend']}")

    print("\n" + "=" * 60)
    print("✅ All tool tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tools())
