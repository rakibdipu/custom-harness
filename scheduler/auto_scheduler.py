"""
Auto Scheduler - Posts 3x per day at optimal US times
Best times for US audience: 9am, 1pm, 7pm EST

NOTE: This legacy class is kept for backward compatibility.
      The primary scheduler is daemon_mode() inside main.py which supports
      per-account schedules and the video buffer system.
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from config import Config

logger = logging.getLogger(__name__)


class AutoScheduler:
    def __init__(self, harness):
        self.config = Config()
        self.harness = harness
        self.tz = pytz.timezone(self.config.TIMEZONE)
        self.scheduler = AsyncIOScheduler(timezone=self.tz)

    def start(self):
        """Set up scheduled posts and start scheduler"""
        for time_str in self.config.POST_TIMES:
            hour, minute = map(int, time_str.strip().split(":"))
            self.scheduler.add_job(
                self._run_harness_cycle,
                CronTrigger(hour=hour, minute=minute, timezone=self.tz),
                name=f"post_{hour:02d}{minute:02d}",
                max_instances=1,
                misfire_grace_time=300   # 5 min grace if system was busy
            )
            logger.info(
                f"Scheduled post at {hour:02d}:{minute:02d} {self.config.TIMEZONE}"
            )

        self.scheduler.start()
        logger.info(
            f"Scheduler active — {len(self.config.POST_TIMES)} posts/day"
        )

        # Show next run times
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            logger.info(f"  Next '{job.name}': {next_run.strftime('%Y-%m-%d %H:%M %Z')}")

    async def _run_harness_cycle(self):
        """Wrapper for scheduled execution — supports both multi-account and legacy harness API"""
        now = datetime.now(self.tz)
        logger.info(f"⏰ Scheduled trigger fired at {now.strftime('%H:%M %Z')}")
        try:
            # New multi-account harness API (MultiAccountHarness)
            if hasattr(self.harness, "run_all_once"):
                await self.harness.run_all_once()
            # Legacy single-account harness fallback
            elif hasattr(self.harness, "run_once"):
                await self.harness.run_once()
            else:
                logger.error("Harness has no run_all_once() or run_once() method")
        except Exception as e:
            logger.error(f"Scheduled cycle failed: {e}", exc_info=True)

    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
