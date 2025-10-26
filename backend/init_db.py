"""
Initialize database with sample data
Run this script to create the database and populate with test listings
"""
import asyncio
import sys
from datetime import datetime, timedelta
from database import db


# Sample listings data (10 realistic items)
SAMPLE_LISTINGS = [
    {
        "title": "맥북 프로 16인치 2023 M3 Pro 팝니다",
        "content": "작년 11월에 구매했고 거의 사용하지 않아서 급매로 내놓습니다. 상태 최상이며 애플케어 2026년까지 남아있습니다. 배터리 사이클 12회, 스크래치 전혀 없습니다. 원박스, 충전기 모두 포함입니다.",
        "price": 2800000,
        "category": "전자기기",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&h=600",
        "boost_count": 0,
        "days_ago": 1  # 어제 등록
    },
    {
        "title": "삼성 27인치 모니터 QHD 판매",
        "content": "삼성 S27A600 모니터입니다. 2022년 구매, 재택근무용으로 사용했습니다. QHD 해상도에 75Hz 지원합니다. 약간의 사용감 있으나 화면 이상 없고 정상 작동합니다. 스탠드, 전원 케이블 포함.",
        "price": 180000,
        "category": "전자기기",
        "region": "서초구",
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800&h=600",
        "boost_count": 0,
        "days_ago": 3
    },
    {
        "title": "아이폰 14 Pro 256GB 딥퍼플 급매",
        "content": "아이폰 15로 기기변경해서 팝니다. 256GB 딥퍼플 색상이고 액정 필름, 케이스 항상 끼고 사용해서 스크래치 없습니다. 배터리 성능 91%, KT 공기계입니다. 직거래 선호합니다.",
        "price": 850000,
        "category": "전자기기",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1678685888221-cda773a3dcdb?w=800&h=600&fit=crop",
        "boost_count": 0,
        "days_ago": 0  # 오늘 등록
    },
    {
        "title": "이케아 HEMNES 책상 화이트 (1년 사용)",
        "content": "이케아 헴네스 책장이 딸린 책상입니다. 화이트 색상, 폭 155cm. 이사 가면서 급하게 처분합니다. 사용감 있으나 튼튼하고 수납공간 많습니다. 분해 후 직거래만 가능합니다.",
        "price": 120000,
        "category": "가구",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800&h=600",
        "boost_count": 0,
        "days_ago": 5
    },
    {
        "title": "한샘 3인용 패브릭 소파 베이지",
        "content": "한샘에서 구매한 3인용 소파입니다. 베이지 색상 패브릭 재질이고 2021년 구매했습니다. 반려동물 없고 담배 안 피웁니다. 약간의 사용감은 있으나 깨끗하게 관리했습니다. 착불 배송 가능합니다.",
        "price": 280000,
        "category": "가구",
        "region": "서초구",
        "image_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&h=600",
        "boost_count": 0,
        "days_ago": 7
    },
    {
        "title": "노스페이스 눕시 패딩 블랙 M 사이즈",
        "content": "노스페이스 정품 눕시 다운 재킷입니다. 블랙 색상 M 사이즈, 작년 겨울에 구매해서 5회 정도만 착용했습니다. 오리털 충전재 700필 다운으로 따뜻합니다. 세탁 한 번 했고 상태 아주 좋습니다.",
        "price": 180000,
        "category": "의류",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=600",
        "boost_count": 0,
        "days_ago": 2
    },
    {
        "title": "유니클로 캐시미어 니트 그레이 L",
        "content": "유니클로 100% 캐시미어 니트 스웨터입니다. 그레이 색상 L 사이즈. 올 초에 구매했는데 사이즈가 안 맞아서 판매합니다. 실착 1회라 거의 새 제품입니다. 정가 79,000원인데 저렴하게 내놓습니다.",
        "price": 35000,
        "category": "의류",
        "region": "서초구",
        "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&h=600",
        "boost_count": 0,
        "days_ago": 1
    },
    {
        "title": "로지텍 MX Master 3S 무선 마우스",
        "content": "로지텍 MX Master 3S 마우스 블랙입니다. 3개월 전 구매했고 거의 새 제품 수준입니다. USB-C 충전 케이블, 리시버 모두 포함되어 있습니다. 정품 영수증 있습니다. 맥북용으로 샀는데 손에 안 맞아서 팝니다.",
        "price": 95000,
        "category": "전자기기",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=800&h=600",
        "boost_count": 0,
        "days_ago": 4
    },
    {
        "title": "LG 스탠바이미 27인치 (2023년형)",
        "content": "LG 스탠바이미 27인치 무선 TV입니다. 2023년형 최신 모델이고 6개월 사용했습니다. 배터리 성능 좋고 화질 선명합니다. 거치대, 리모컨, 충전기 모두 포함입니다. 이사 가면서 급매로 처분합니다.",
        "price": 650000,
        "category": "전자기기",
        "region": "서초구",
        "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800&h=600",
        "boost_count": 0,
        "days_ago": 6
    },
    {
        "title": "시디즈 T50 의자 블랙 (허리받침)",
        "content": "시디즈 T50 메쉬 사무용 의자입니다. 블랙 색상, 허리받침 기능 있습니다. 재택근무용으로 2년 사용했고 상태 양호합니다. 팔걸이 약간의 마모 있으나 기능 이상 없습니다. 직거래만 가능합니다.",
        "price": 220000,
        "category": "가구",
        "region": "강남구",
        "image_url": "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800&h=600",
        "boost_count": 0,
        "days_ago": 8
    }
]


async def init_database():
    """Initialize database and insert sample data"""
    print("🔧 Initializing database...")

    # Create schema
    await db.init_db()
    print("✅ Database schema created")

    # Clear existing data (for clean start)
    await db.clear_all_listings()
    print("✅ Cleared existing listings")

    # Insert sample listings
    print(f"\n📦 Inserting {len(SAMPLE_LISTINGS)} sample listings...")

    for idx, listing in enumerate(SAMPLE_LISTINGS, 1):
        # Extract timing information
        days_ago = listing.pop("days_ago", 0)
        boost_count = listing.pop("boost_count", 0)

        listing_id = await db.create_listing(
            title=listing["title"],
            content=listing["content"],
            price=listing["price"],
            category=listing["category"],
            region=listing["region"],
            image_url=listing.get("image_url")
        )

        # Update created_at to simulate different dates
        # last_boosted_at is left as NULL (never boosted)
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as conn:
            if days_ago > 0:
                created_date = datetime.now() - timedelta(days=days_ago)
                await conn.execute("""
                    UPDATE listings
                    SET created_at = ?, updated_at = ?, boost_count = ?
                    WHERE id = ?
                """, (created_date.isoformat(), created_date.isoformat(), boost_count, listing_id))
            else:
                await conn.execute("""
                    UPDATE listings
                    SET boost_count = ?
                    WHERE id = ?
                """, (boost_count, listing_id))
            await conn.commit()

        print(f"  {idx}. {listing['title'][:30]}... (ID: {listing_id}, {days_ago}일 전)")

    print("\n✅ Sample data inserted successfully!")

    # Verify data
    all_listings = await db.get_all_listings()
    print(f"\n📊 Total listings in database: {len(all_listings)}")

    # Show summary by category
    categories = {}
    for listing in all_listings:
        cat = listing["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📈 Summary by category:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}개")

    print("\n🎉 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_database())
