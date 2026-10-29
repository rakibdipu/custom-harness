"""
Topic Queue - User can push topics any time, system uses them first
Priority: User topics > Auto-generated topics
"""
import asyncio
import aiosqlite
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = "harness.db"


class TopicQueue:
    """
    Manages topic priority queue per account.
    User topics always come first, then auto-generated.
    """

    async def _init_db(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS topic_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    source TEXT DEFAULT 'auto',   -- 'user' or 'auto' or 'comic'
                    content_type TEXT DEFAULT 'short_reel',
                    priority INTEGER DEFAULT 0,    -- higher = sooner
                    status TEXT DEFAULT 'pending', -- pending, used, skipped
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used_at TIMESTAMP
                )
            """)
            await db.commit()

    async def push(
        self,
        topic: str,
        account_id: str,
        content_type: str = "short_reel",
        source: str = "user"
    ):
        """Push a topic to the queue (user-submitted topics get priority=10)"""
        await self._init_db()
        priority = 10 if source == "user" else 0
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO topic_queue (account_id, topic, source, content_type, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, topic, source, content_type, priority))
            await db.commit()
        logger.info(f"Topic queued [{account_id}] [{source}]: {topic}")

    async def pop(self, account_id: str, content_type: str = None) -> dict | None:
        """Get the next pending topic (user topics first, then auto)"""
        await self._init_db()
        query = """
            SELECT id, topic, source, content_type
            FROM topic_queue
            WHERE account_id = ? AND status = 'pending'
        """
        params = [account_id]
        if content_type:
            query += " AND content_type = ?"
            params.append(content_type)
        query += " ORDER BY priority DESC, added_at ASC LIMIT 1"

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                row_id, topic, source, ct = row
                # Mark as used
                await db.execute(
                    "UPDATE topic_queue SET status='used', used_at=? WHERE id=?",
                    (datetime.now().isoformat(), row_id)
                )
                await db.commit()
                return {"id": row_id, "topic": topic, "source": source, "content_type": ct}

    async def peek_all(self, account_id: str = None) -> list:
        """View all pending topics (for dashboard)"""
        await self._init_db()
        query = "SELECT id, account_id, topic, source, content_type, priority, added_at FROM topic_queue WHERE status='pending'"
        params = []
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        query += " ORDER BY priority DESC, added_at ASC"

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {"id": r[0], "account": r[1], "topic": r[2],
                     "source": r[3], "type": r[4], "priority": r[5], "added": r[6]}
                    for r in rows
                ]

    async def pending_count(self, account_id: str) -> int:
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM topic_queue WHERE account_id=? AND status='pending'",
                (account_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
