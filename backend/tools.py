"""
Tool functions for LLM Agent
Each tool performs specific actions on listings
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from database import db
from config import BOOST_COOLDOWN_HOURS, INSIGHTS_DATA


# === Tool 1: Query Listings ===

async def query_listings(
    days_ago: Optional[int] = None,
    exact_day_ago: Optional[int] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    status: str = "active",
    sort_by: str = "created_at",
    sort_order: str = "DESC"
) -> Dict[str, Any]:
    """
    매물 조회 Tool

    Args:
        days_ago: 최근 N일 범위 (N일 전부터 지금까지)
        exact_day_ago: 특정일 당일만 (정확히 N일 전)
        category: 카테고리 필터
        region: 지역 필터
        status: 판매 상태
        sort_by: 정렬 기준 ("created_at", "updated_at", "last_boosted_at", "price", "boost_count")
        sort_order: 정렬 순서 ("ASC" - 오름차순, "DESC" - 내림차순)

    Returns:
        {
            "success": bool,
            "listings": List[Dict],
            "count": int,
            "message": str
        }
    """
    try:
        # 🔍 DEBUG: 조회 파라미터 로그
        print(f"🔎 query_listings called with filters:")
        print(f"   - days_ago: {days_ago}")
        print(f"   - exact_day_ago: {exact_day_ago}")
        print(f"   - category: {category}")
        print(f"   - region: {region}")
        print(f"   - status: {status}")
        print(f"   - sort_by: {sort_by}")
        print(f"   - sort_order: {sort_order}")

        listings = await db.query_listings(
            category=category,
            region=region,
            status=status,
            days_ago=days_ago,
            exact_day_ago=exact_day_ago,
            sort_by=sort_by,
            sort_order=sort_order
        )

        print(f"📊 Found {len(listings)} listings:")
        for listing in listings:
            print(f"   - ID {listing['id']}: {listing['title']}")

        return {
            "success": True,
            "listings": listings,
            "count": len(listings),
            "message": f"{len(listings)}개의 매물을 찾았습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "listings": [],
            "count": 0,
            "message": f"매물 조회 실패: {str(e)}"
        }


# === Tool 2: Adjust Price ===

async def adjust_price(listing_id: int, new_price: int) -> Dict[str, Any]:
    """
    가격 조정 Tool

    Args:
        listing_id: 매물 ID
        new_price: 새로운 가격 (원)

    Returns:
        {
            "success": bool,
            "listing_id": int,
            "old_price": int,
            "new_price": int,
            "change_amount": int,
            "change_percent": float,
            "message": str
        }
    """
    try:
        # Validate new price
        if new_price <= 0:
            return {
                "success": False,
                "message": "가격은 0원보다 커야 합니다."
            }

        # Get current listing
        listing = await db.get_listing_by_id(listing_id)
        if not listing:
            return {
                "success": False,
                "message": f"매물 ID {listing_id}를 찾을 수 없습니다."
            }

        old_price = listing["price"]

        # Same price check
        if old_price == new_price:
            return {
                "success": False,
                "message": "현재 가격과 동일합니다."
            }

        # Update price
        await db.update_price(listing_id, new_price)

        # Calculate changes
        change_amount = new_price - old_price
        change_percent = (change_amount / old_price) * 100

        return {
            "success": True,
            "listing_id": listing_id,
            "listing_title": listing["title"],
            "old_price": old_price,
            "new_price": new_price,
            "change_amount": change_amount,
            "change_percent": round(change_percent, 1),
            "message": f"가격을 {old_price:,}원에서 {new_price:,}원으로 변경했습니다."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"가격 조정 실패: {str(e)}"
        }


# === Tool 3: Boost Listing ===

async def boost_listing(listing_id: int) -> Dict[str, Any]:
    """
    끌어올리기 Tool

    Args:
        listing_id: 매물 ID

    Returns:
        {
            "success": bool,
            "listing_id": int,
            "boosted_at": str,
            "boost_count": int,
            "message": str,
            "warning": str (optional)
        }
    """
    try:
        # Get current listing
        listing = await db.get_listing_by_id(listing_id)
        if not listing:
            return {
                "success": False,
                "message": f"매물 ID {listing_id}를 찾을 수 없습니다."
            }

        # Check cooldown (24 hours)
        last_boosted = listing.get("last_boosted_at")
        if last_boosted:
            # Parse timestamp
            last_boosted_time = datetime.fromisoformat(last_boosted)
            time_since_boost = datetime.now() - last_boosted_time
            cooldown_hours = BOOST_COOLDOWN_HOURS

            if time_since_boost < timedelta(hours=cooldown_hours):
                hours_remaining = cooldown_hours - (time_since_boost.total_seconds() / 3600)
                return {
                    "success": False,
                    "message": f"끌어올리기는 24시간에 한 번만 가능합니다.",
                    "warning": f"다음 끌어올리기까지 {hours_remaining:.1f}시간 남았습니다.",
                    "hours_remaining": round(hours_remaining, 1)
                }

        # Perform boost
        await db.boost_listing(listing_id)

        return {
            "success": True,
            "listing_id": listing_id,
            "listing_title": listing["title"],
            "boosted_at": datetime.now().isoformat(),
            "boost_count": listing["boost_count"] + 1,
            "message": f"'{listing['title']}' 매물을 끌어올렸습니다.",
            "warning": "끌어올리기는 24시간에 한 번만 가능합니다."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"끌어올리기 실패: {str(e)}"
        }


# === Tool 4: Update Content ===

async def update_content(
    listing_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None
) -> Dict[str, Any]:
    """
    제목/내용 수정 Tool

    Args:
        listing_id: 매물 ID
        title: 새 제목 (선택)
        content: 새 내용 (선택)

    Returns:
        {
            "success": bool,
            "listing_id": int,
            "updated_fields": List[str],
            "message": str
        }
    """
    try:
        # Validate inputs
        if not title and not content:
            return {
                "success": False,
                "message": "수정할 제목 또는 내용을 제공해주세요."
            }

        # Get current listing
        listing = await db.get_listing_by_id(listing_id)
        if not listing:
            return {
                "success": False,
                "message": f"매물 ID {listing_id}를 찾을 수 없습니다."
            }

        # Update content
        await db.update_content(listing_id, title=title, content=content)

        updated_fields = []
        if title:
            updated_fields.append("제목")
        if content:
            updated_fields.append("내용")

        return {
            "success": True,
            "listing_id": listing_id,
            "listing_title": title or listing["title"],
            "updated_fields": updated_fields,
            "old_title": listing["title"] if title else None,
            "new_title": title,
            "message": f"{', '.join(updated_fields)}을(를) 수정했습니다."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"내용 수정 실패: {str(e)}"
        }


# === Tool 5: Get Market Insights ===

async def get_market_insights(
    category: str,
    region: str
) -> Dict[str, Any]:
    """
    시장 인사이트 Tool (고정값 반환)

    Args:
        category: 카테고리
        region: 지역

    Returns:
        {
            "success": bool,
            "category": str,
            "region": str,
            "average_price": int,
            "avg_sell_days": int,
            "trend": str,
            "sample_count": int,
            "recommendation": str,
            "message": str
        }
    """
    try:
        # Get insights from config (with fallback to default)
        key = (category, region)
        default_key = ("default", "default")

        insights = INSIGHTS_DATA.get(key, INSIGHTS_DATA.get(default_key))

        if not insights:
            return {
                "success": False,
                "message": f"{category} - {region} 지역의 시장 데이터를 찾을 수 없습니다."
            }

        return {
            "success": True,
            "category": category,
            "region": region,
            "average_price": insights["average_price"],
            "avg_sell_days": insights["avg_sell_days"],
            "trend": insights["trend"],
            "sample_count": insights["sample_count"],
            "recommendation": insights["recommendation"],
            "message": f"{region} {category} 카테고리의 시장 분석 결과입니다."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"시장 인사이트 조회 실패: {str(e)}"
        }


# === Tool Registry ===

TOOLS = {
    "query_listings": query_listings,
    "adjust_price": adjust_price,
    "boost_listing": boost_listing,
    "update_content": update_content,
    "get_market_insights": get_market_insights,
}


async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given parameters

    Args:
        tool_name: Tool function name
        params: Tool parameters

    Returns:
        Tool execution result
    """
    tool_func = TOOLS.get(tool_name)

    if not tool_func:
        return {
            "success": False,
            "message": f"알 수 없는 Tool: {tool_name}"
        }

    try:
        result = await tool_func(**params)
        return result
    except TypeError as e:
        return {
            "success": False,
            "message": f"Tool 파라미터 오류: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Tool 실행 오류: {str(e)}"
        }
