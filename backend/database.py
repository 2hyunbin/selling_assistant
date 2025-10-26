"""
Database operations for JOL AI Agent
SQLite with async support
"""
import aiosqlite
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from config import DATABASE_PATH


class Database:
    """Database manager for listings"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    region TEXT NOT NULL,
                    image_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_boosted_at TIMESTAMP NULL,
                    boost_count INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def get_connection(self):
        """Get database connection"""
        return await aiosqlite.connect(self.db_path)

    # === CREATE ===

    async def create_listing(
        self,
        title: str,
        content: str,
        price: int,
        category: str,
        region: str,
        image_url: str = None
    ) -> int:
        """Create new listing and return ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO listings (title, content, price, category, region, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, content, price, category, region, image_url))
            await db.commit()
            return cursor.lastrowid

    # === READ ===

    async def get_listing_by_id(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """Get single listing by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM listings WHERE id = ?
            """, (listing_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_listings(
        self,
        status: str = "active",
        sort_by: str = "created_at",
        sort_order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """Get all listings with given status

        Args:
            status: Filter by status (active, sold, deleted)
            sort_by: Field to sort by (created_at, updated_at, last_boosted_at, price, boost_count)
            sort_order: Sort order (ASC or DESC)
        """
        # Validate sort_by to prevent SQL injection
        allowed_sort_fields = ["created_at", "updated_at", "last_boosted_at", "price", "boost_count", "id"]
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        # Validate sort_order
        sort_order = sort_order.upper()
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        # Use COALESCE for last_boosted_at to fall back to created_at
        if sort_by == "last_boosted_at":
            order_clause = f"COALESCE(last_boosted_at, created_at) {sort_order}"
        else:
            order_clause = f"{sort_by} {sort_order}"

        query = f"SELECT * FROM listings WHERE status = ? ORDER BY {order_clause}"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, (status,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def query_listings(
        self,
        category: Optional[str] = None,
        region: Optional[str] = None,
        status: str = "active",
        days_ago: Optional[int] = None,
        exact_day_ago: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """Query listings with filters

        Args:
            category: Filter by category
            region: Filter by region
            status: Filter by status (active, sold, deleted)
            days_ago: Filter by range (N days ago until now)
            exact_day_ago: Filter by exact day (only N days ago)
            sort_by: Field to sort by (created_at, updated_at, last_boosted_at, price, boost_count)
            sort_order: Sort order (ASC or DESC)
        """
        query = "SELECT * FROM listings WHERE status = ?"
        params = [status]

        if category:
            query += " AND category = ?"
            params.append(category)

        if region:
            query += " AND region = ?"
            params.append(region)

        # 날짜 필터 처리 (둘 중 하나만 사용)
        if exact_day_ago is not None:
            # 특정일 당일만
            if exact_day_ago == 0:
                query += " AND date(created_at) = date('now')"
            else:
                query += f" AND date(created_at) = date('now', '-{exact_day_ago} days')"
        elif days_ago is not None:
            # 범위 (N일 전부터 지금까지)
            if days_ago > 0:
                query += f" AND date(created_at) >= date('now', '-{days_ago} days')"

        # Validate sort_by to prevent SQL injection
        allowed_sort_fields = ["created_at", "updated_at", "last_boosted_at", "price", "boost_count", "id"]
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        # Validate sort_order
        sort_order = sort_order.upper()
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        # Use COALESCE for last_boosted_at to fall back to created_at
        if sort_by == "last_boosted_at":
            order_clause = f"COALESCE(last_boosted_at, created_at) {sort_order}"
        else:
            order_clause = f"{sort_by} {sort_order}"

        query += f" ORDER BY {order_clause}"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # === UPDATE ===

    async def update_price(self, listing_id: int, new_price: int) -> bool:
        """Update listing price"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE listings
                SET price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_price, listing_id))
            await db.commit()
            return True

    async def update_content(
        self,
        listing_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> bool:
        """Update listing title or content"""
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE listings SET {', '.join(updates)} WHERE id = ?"
        params.append(listing_id)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()
            return True

    async def boost_listing(self, listing_id: int) -> bool:
        """Boost listing (update timestamp)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE listings
                SET last_boosted_at = CURRENT_TIMESTAMP,
                    boost_count = boost_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (listing_id,))
            await db.commit()
            return True

    async def update_status(self, listing_id: int, status: str) -> bool:
        """Update listing status (active/sold)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE listings
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, listing_id))
            await db.commit()
            return True

    # === DELETE ===

    async def delete_listing(self, listing_id: int) -> bool:
        """Delete listing (soft delete by setting status)"""
        return await self.update_status(listing_id, "deleted")

    # === UTILITY ===

    async def clear_all_listings(self):
        """Clear all listings and reset ID counter (for testing)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM listings")
            # Reset autoincrement counter
            await db.execute("DELETE FROM sqlite_sequence WHERE name='listings'")
            await db.commit()


# Global database instance
db = Database()
