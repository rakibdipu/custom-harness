"""
Topic Selector - Picks viral topics per account niche, tracks what's been used
Each account gets topics from its own niche-matched bank to avoid cross-contamination.
"""
import random
import asyncio
import aiosqlite
import logging
from datetime import datetime, timedelta
from config import Config, TOPIC_BANK

logger = logging.getLogger(__name__)

# ─── Per-niche topic banks ────────────────────────────────────────────────────

STORY_TOPIC_BANK = [
    "the Japanese soldier who kept fighting until 1974 because nobody told him",
    "the man who lived in an airport for 18 years and inspired a masterpiece",
    "the woman who refused to leave her sinking ship and changed maritime law",
    "the emperor who gave away his entire fortune and became a beggar",
    "the prison librarian who educated 3 generations of inmates and freed them all",
    "the blind artist who could only see with his fingers and became world famous",
    "the boy who survived alone in the forest for 7 years and built his own society",
    "the general who lost every battle but won the war by running away",
    "the farmer who outsmarted an entire invading army with one idea",
    "the woman who memorized an entire library and survived to rebuild civilization",
    "the city that disappeared overnight and the single family who was left behind",
    "the monk who fasted for 66 days and what he saw at the end",
    "the letter written 100 years ago that was only opened last week",
    "the man who planted 37 million trees alone in a desert over 40 years",
    "the lighthouse keeper who kept the flame burning through the storm of the century",
    "the marathon runner who ran barefoot through the night to save his village",
    "the watchmaker who spent 50 years building a clock that ticks for 10000 years",
    "the codebreaker whose quiet mathematics ended a war two years early",
    "the doctor who stayed in the quarantined zone when everyone else fled",
    "the street musician whose anonymous symphonies were discovered 50 years later",
    "the sailor who crossed the Pacific Ocean on a wooden raft to prove ancient history",
    "the mountain climber who cut his own rope and miraculously survived",
    "the deep-sea diver who got trapped 100 meters underwater with 5 minutes of oxygen",
    "the forgotten explorer who walked across Antarctica completely alone",
    "the humble teacher whose students secretly bought him a home 40 years later",
]

COMIC_TOPIC_BANK = [
    "when your alarm says 5am but your brain says absolutely not",
    "every zoom call has that one person who never mutes",
    "the awkward moment when someone replies-all to an office email",
    "adulting is just googling things your parents definitely knew",
    "gym January vs gym February: a tale of two gyms",
    "that look you give when someone says 'quick meeting'",
    "why coffee hits different on Monday mornings",
    "when your phone dies at 1% right when you needed it most",
    "every group chat has these exact 5 types of people",
    "the universal experience of forgetting why you walked into a room",
    "when your boss says we're a family but cuts the pizza budget",
    "the 3am existential crisis starter pack",
    "when someone says 'we need to talk' and your brain fast-forwards to the worst scenario",
    "how people describe their jobs vs what they actually do",
    "the grocery store trap: going in for milk and leaving with everything else",
    "the 45-minute goodbye that happens at every party",
    "why does every DIY project end with a trip to the hardware store twice",
    "the internet rabbit hole that starts with a recipe and ends at flat earth",
    "ordering takeout when you have food in the fridge because cooking requires emotional labor",
    "rehearsing an entire argument in the shower that will literally never happen",
    "cleaning your entire house with sudden manic energy to avoid doing actual work",
    "saying 'no worries at all' while your entire week is actively collapsing",
    "the awkward hallway dance when two people try to dodge in the same direction",
    "looking at your bank account through squinted eyes like it's a horror movie",
    "putting your phone in your pocket and tapping it every 4 seconds to verify it exists",
]

# Map account IDs and niches to their topic banks
_ACCOUNT_TOPIC_MAP = {
    "comic_viral": COMIC_TOPIC_BANK,
    "storytelling": STORY_TOPIC_BANK,
    "psychology_mindset": TOPIC_BANK,  # from config.py
}

_NICHE_TOPIC_MAP = {
    "short stories": STORY_TOPIC_BANK,
    "life lessons": STORY_TOPIC_BANK,
    "comedy": COMIC_TOPIC_BANK,
    "comic": COMIC_TOPIC_BANK,
    "humor": COMIC_TOPIC_BANK,
    "relatable": COMIC_TOPIC_BANK,
}


def _get_topic_bank_for_account(account_id: str, niche: str = "") -> list:
    """Return the right topic bank for this account"""
    # Match by account ID first
    if account_id in _ACCOUNT_TOPIC_MAP:
        return _ACCOUNT_TOPIC_MAP[account_id]
    # Then by niche keyword
    niche_lower = niche.lower()
    for kw, bank in _NICHE_TOPIC_MAP.items():
        if kw in niche_lower:
            return bank
    # Default: psychology/mindset bank
    return TOPIC_BANK


class TopicSelector:
    def __init__(self):
        self.config = Config()
        self.db_path = str(self.config.DB_PATH)

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS used_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT DEFAULT 'default',
                    topic TEXT NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0
                )
            """)
            # Add account_id column if migrating from old schema
            try:
                await db.execute("ALTER TABLE used_topics ADD COLUMN account_id TEXT DEFAULT 'default'")
            except Exception:
                pass  # Column already exists
            await db.commit()

    async def _get_used_topics_last_30_days(self, account_id: str = "default") -> list:
        await self._init_db()
        cutoff = datetime.now() - timedelta(days=30)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT topic FROM used_topics WHERE account_id = ? AND used_at > ?",
                (account_id, cutoff.isoformat())
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def _mark_used(self, topic: str, account_id: str = "default"):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO used_topics (account_id, topic) VALUES (?, ?)",
                (account_id, topic)
            )
            await db.commit()

    async def get_topic(self, account_id: str = "default", niche: str = "") -> str:
        """Get next unused viral topic for this account's niche"""
        bank = _get_topic_bank_for_account(account_id, niche)
        used = await self._get_used_topics_last_30_days(account_id)
        available = [t for t in bank if t not in used]

        if not available:
            # All topics used, reset and start fresh
            logger.info(f"All topics used in last 30 days for [{account_id}] — resetting rotation")
            available = bank.copy()

        # Pick randomly from available (adds variety)
        topic = random.choice(available)
        await self._mark_used(topic, account_id)
        logger.info(f"[{account_id}] Selected topic: '{topic}' ({len(available)} remaining)")
        return topic

    async def update_performance(self, topic: str, views: int, likes: int, account_id: str = "default"):
        """Track which topics perform best"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE used_topics SET views=?, likes=?
                   WHERE account_id=? AND topic=? AND id=(
                       SELECT id FROM used_topics WHERE account_id=? AND topic=? ORDER BY id DESC LIMIT 1
                   )""",
                (views, likes, account_id, topic, account_id, topic)
            )
            await db.commit()
