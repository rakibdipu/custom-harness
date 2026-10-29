"""
Queue all 90-day topics for all 3 accounts into topic_queue table in harness.db
"""
import json
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = "harness.db"

PLANS = [
    {
        "account_id": "psychology_mindset",
        "file": "accounts/mindedge_90_plan.json",
        "content_type": "short_reel"
    },
    {
        "account_id": "comic_viral",
        "file": "accounts/tooreal_90_plan.json",
        "content_type": "short_reel"
    },
    {
        "account_id": "storytelling",
        "file": "accounts/storyvault_90_plan.json",
        "content_type": "short_reel"
    }
]


async def populate_queue(clear_existing: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topic_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                source TEXT DEFAULT 'plan_90',
                content_type TEXT DEFAULT 'short_reel',
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP
            )
        """)

        if clear_existing:
            await db.execute("DELETE FROM topic_queue WHERE source = 'plan_90' OR source = 'user' OR source = 'auto'")
            await db.commit()
            print("Cleared existing queued topics.")

        total_inserted = 0

        for plan_info in PLANS:
            account_id = plan_info["account_id"]
            file_path = plan_info["file"]
            content_type = plan_info["content_type"]

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            days = data.get("days", [])
            print(f"\n📂 Loading {account_id} from {file_path} ({len(days)} days)...")

            seq = 0
            for day_obj in days:
                day_num = day_obj.get("day", 1)
                day_theme = day_obj.get("theme", "")
                videos = day_obj.get("videos", [])

                for v in videos:
                    v_id = v.get("id", "")
                    title = v.get("title", "")
                    hook = v.get("hook", "")
                    
                    # Construct rich topic prompt
                    if hook:
                        topic_str = f"{title} (Hook: {hook})"
                    else:
                        topic_str = title

                    # Priority: Higher for earlier days so Day 1 is popped before Day 2, etc.
                    # Total 90 videos: priority = 1000 - seq (Day 1 Morning = 1000, Day 30 Evening = 911)
                    priority = 1000 - seq

                    # Check if already in queue
                    async with db.execute(
                        "SELECT id FROM topic_queue WHERE account_id = ? AND topic = ?",
                        (account_id, topic_str)
                    ) as cursor:
                        exists = await cursor.fetchone()

                    if not exists:
                        await db.execute("""
                            INSERT INTO topic_queue (account_id, topic, source, content_type, priority, status)
                            VALUES (?, ?, 'plan_90', ?, ?, 'pending')
                        """, (account_id, topic_str, content_type, priority))
                        total_inserted += 1
                        seq += 1

            print(f"✅ Queued {seq} topics for {account_id}")

        await db.commit()
        print(f"\n🎉 Successfully loaded {total_inserted} topics into topic_queue in {DB_PATH}")


if __name__ == "__main__":
    asyncio.run(populate_queue(clear_existing=True))
