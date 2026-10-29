"""
Video Buffer Manager - Pre-generates videos in advance
Keeps a queue of ready-made videos on disk.
When schedule triggers, it posts instantly (zero delay)!
After upload & verification, local video files are safely deleted to save disk space.
"""
import aiosqlite
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = "harness.db"


class VideoBuffer:
    def __init__(self, target_buffer_per_account: int = 3):
        self.target_buffer = target_buffer_per_account

    async def _init_db(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS video_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    video_path TEXT NOT NULL,
                    status TEXT DEFAULT 'ready', -- ready, posted, posted_deleted, failed, missing
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP
                )
            """)
            await db.commit()

    async def add_ready_video(
        self,
        account_id: str,
        content_type: str,
        topic: str,
        title: str,
        caption: str,
        video_path: str
    ):
        """Add a newly generated video into the ready buffer"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO video_buffer (account_id, content_type, topic, title, caption, video_path, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ready')
            """, (account_id, content_type, topic, title, caption, video_path))
            await db.commit()
        logger.info(f"📦 Stored in buffer [{account_id}]: {title[:40]} -> {Path(video_path).name}")

    async def get_ready_count(self, account_id: str, content_type: str = None) -> int:
        """Count how many pre-made videos are waiting on disk for an account"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            if content_type:
                query = "SELECT id, video_path FROM video_buffer WHERE account_id = ? AND content_type = ? AND status = 'ready'"
                params = (account_id, content_type)
            else:
                query = "SELECT id, video_path FROM video_buffer WHERE account_id = ? AND status = 'ready'"
                params = (account_id,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                # Verify that files actually exist on disk
                valid_count = 0
                for row_id, vpath in rows:
                    if Path(vpath).exists():
                        valid_count += 1
                    else:
                        await db.execute("UPDATE video_buffer SET status='missing' WHERE id=?", (row_id,))
                await db.commit()
                return valid_count

    async def pop_next_video(self, account_id: str, content_type: str = None) -> dict | None:
        """Get the oldest verified ready video for immediate posting, optionally filtered by content_type"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            while True:
                if content_type:
                    query = """
                        SELECT id, content_type, topic, title, caption, video_path
                        FROM video_buffer
                        WHERE account_id = ? AND content_type = ? AND status = 'ready'
                        ORDER BY created_at ASC LIMIT 1
                    """
                    params = (account_id, content_type)
                else:
                    query = """
                        SELECT id, content_type, topic, title, caption, video_path
                        FROM video_buffer
                        WHERE account_id = ? AND status = 'ready'
                        ORDER BY created_at ASC LIMIT 1
                    """
                    params = (account_id,)

                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return None
                    
                    vid_id, ct, topic, title, caption, vpath = row
                    
                    # Ensure file actually exists on disk
                    if not Path(vpath).exists():
                        logger.warning(f"Buffer video {vpath} missing from disk, marking missing")
                        await db.execute("UPDATE video_buffer SET status='missing' WHERE id=?", (vid_id,))
                        await db.commit()
                        continue

                    await db.execute(
                        "UPDATE video_buffer SET status='posted', posted_at=? WHERE id=?",
                        (datetime.now().isoformat(), vid_id)
                    )
                    await db.commit()
                    return {
                        "id": vid_id,
                        "content_type": ct,
                        "topic": topic,
                        "title": title,
                        "caption": caption,
                        "video_path": vpath
                    }

    async def mark_posted_and_deleted(self, video_path: str):
        """Mark video as posted and cleaned up from disk to save space"""
        await self._init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                UPDATE video_buffer 
                SET status='posted_deleted', posted_at=COALESCE(posted_at, ?)
                WHERE video_path = ?
            """, (datetime.now().isoformat(), video_path))
            await db.commit()
        logger.info(f"💾 Buffer record updated to 'posted_deleted' for {Path(video_path).name}")

    async def list_ready_videos(self, account_id: str = None) -> list[dict]:
        """List all videos waiting in buffer that exist on disk"""
        await self._init_db()
        query = "SELECT id, account_id, title, topic, video_path, created_at FROM video_buffer WHERE status='ready'"
        params = []
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        query += " ORDER BY created_at ASC"

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    if Path(r[4]).exists():
                        results.append({
                            "id": r[0], "account_id": r[1], "title": r[2],
                            "topic": r[3], "video_path": r[4], "created_at": r[5]
                        })
                return results
