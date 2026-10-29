"""
Custom Harness — Lightweight Smart Scheduler (Auto Runner)
Monitors scheduled post times for all enabled accounts.
Exactly 30 minutes before each post time:
  1. Triggers AI video generation pipeline (script -> TTS -> AI visual -> assembly).
  2. Saves finished video into buffer.
At exact scheduled post time:
  1. Instantly posts the pre-generated video to Facebook / YouTube (0s delay).
  2. Verifies 3x on platform.
  3. Cleans up local video file to free disk space.
Between events:
  Sleeps quietly in the background using minimal CPU & RAM.
"""
import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to sys.path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from main import MultiAccountHarness
from accounts.account_manager import AccountManager
from config import Config

console = Console()
logger = logging.getLogger("auto_runner")


def setup_logging():
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_dir / "auto_runner.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def calculate_lead_time(hour: int, minute: int, lead_minutes: int = 30) -> tuple[int, int]:
    """Calculate the trigger time that is lead_minutes before (hour, minute)"""
    total_minutes = (hour * 60 + minute - lead_minutes) % 1440
    return total_minutes // 60, total_minutes % 60


def get_timezone(tz_name: str | None = None):
    """Resolve timezone from argument, env variable, config, or local system"""
    if tz_name and tz_name.lower() != "local":
        try:
            return pytz.timezone(tz_name)
        except Exception:
            pass

    env_tz = os.getenv("SCHEDULE_TIMEZONE")
    if env_tz:
        try:
            return pytz.timezone(env_tz)
        except Exception:
            pass

    # Try local system timezone
    try:
        import time
        local_tz_name = time.tzname[0]
        if local_tz_name and local_tz_name in pytz.all_timezones:
            return pytz.timezone(local_tz_name)
    except Exception:
        pass

    # Fallback: Asia/Dhaka (+06:00) or US/Eastern
    return pytz.timezone("Asia/Dhaka")


async def build_scheduler(
    harness: MultiAccountHarness,
    tz,
    lead_minutes: int = 30,
    test_mode: bool = False
) -> tuple[AsyncIOScheduler, list]:
    """Sets up prebake triggers (30m before) and publish triggers (exact time)"""
    scheduler = AsyncIOScheduler(timezone=tz)
    jobs_summary = []
    accounts = harness.account_mgr.get_all()

    for account in accounts:
        for content_type, times in account.schedule.items():
            for time_str in times:
                post_h, post_m = map(int, time_str.split(":"))
                pre_h, pre_m = calculate_lead_time(post_h, post_m, lead_minutes)

                # ── 1. PREBAKE TRIGGER (30m before post) ──────────────────────
                def make_prebake_job(acc=account, ct=content_type, p_time=time_str):
                    async def prebake():
                        logger.info(f"⏳ [TRIGGER -30m] Pre-generating video for {acc.name} ({ct}) scheduled for {p_time}...")
                        try:
                            ready_count = await harness.video_buffer.get_ready_count(acc.id, ct)
                            if ready_count >= 1:
                                logger.info(f"📦 [Buffer OK] {acc.name} already has {ready_count} ready video(s) in buffer.")
                            else:
                                await harness._generate_video_pipeline(acc, ct, save_to_buffer=True)
                                logger.info(f"✅ [Prebake Complete] Video ready in buffer for {acc.name} ({ct}) at {p_time}")
                        except Exception as e:
                            logger.error(f"❌ Prebake failed for {acc.id}: {e}", exc_info=True)
                    return prebake

                pre_job_id = f"pre_{account.id}_{content_type}_{pre_h:02d}{pre_m:02d}"
                scheduler.add_job(
                    make_prebake_job(),
                    CronTrigger(hour=pre_h, minute=pre_m, timezone=tz),
                    id=pre_job_id,
                    name=f"Prebake: {account.name} @ {pre_h:02d}:{pre_m:02d} (for {time_str})",
                    replace_existing=True,
                    misfire_grace_time=600
                )

                # ── 2. PUBLISH TRIGGER (exact scheduled time) ─────────────────
                def make_post_job(acc=account, ct=content_type, p_time=time_str):
                    async def post_video():
                        logger.info(f"⏰ [POST TRIGGER] Posting scheduled video for {acc.name} ({ct}) @ {p_time}...")
                        try:
                            await harness.post_scheduled_video(acc, ct)
                        except Exception as e:
                            logger.error(f"❌ Post failed for {acc.id}: {e}", exc_info=True)
                    return post_video

                post_job_id = f"post_{account.id}_{content_type}_{post_h:02d}{post_m:02d}"
                scheduler.add_job(
                    make_post_job(),
                    CronTrigger(hour=post_h, minute=post_m, timezone=tz),
                    id=post_job_id,
                    name=f"Post: {account.name} @ {time_str}",
                    replace_existing=True,
                    misfire_grace_time=300
                )

                jobs_summary.append({
                    "account": account.name,
                    "content_type": content_type,
                    "prebake_time": f"{pre_h:02d}:{pre_m:02d}",
                    "post_time": time_str
                })

    return scheduler, jobs_summary


async def run_daemon(lead_minutes: int = 30, tz_name: str | None = None, test_mode: bool = False):
    """Main loop: runs lightweight scheduler in background"""
    setup_logging()
    tz = get_timezone(tz_name)
    harness = MultiAccountHarness(test_mode=test_mode)

    console.print(Panel(
        f"[bold cyan]⚡ LIGHTWEIGHT AUTO-RUNNER (30-MIN LEAD TIME)[/bold cyan]\n"
        f"• Lead Time: Triggers [bold yellow]{lead_minutes} minutes[/bold yellow] before each post\n"
        f"• Timezone: [bold green]{tz.zone}[/bold green] (Current time: {datetime.now(tz).strftime('%I:%M:%S %p')})\n"
        f"• Resource: Minimal idle footprint — wakes up only when needed\n"
        f"• Test Mode: {'ON (no live publishing)' if test_mode else 'OFF (live Facebook/YouTube)'}",
        border_style="cyan"
    ))

    scheduler, jobs_summary = await build_scheduler(harness, tz, lead_minutes, test_mode)

    # Display schedule table
    table = Table(title=f"📅 Active Automation Schedule ({tz.zone})", border_style="dim")
    table.add_column("Account", style="bold white")
    table.add_column("Content Type", style="cyan")
    table.add_column("🛠️ Gen Triggers (-30m)", style="yellow")
    table.add_column("📤 Uploads Live", style="green")

    for j in sorted(jobs_summary, key=lambda x: x["post_time"]):
        table.add_row(j["account"], j["content_type"], j["prebake_time"], j["post_time"])

    console.print(table)

    scheduler.start()
    logger.info(f"Auto-runner started with {len(scheduler.get_jobs())} jobs across {len(harness.account_mgr.get_all())} accounts.")
    console.print(f"[green]✔ Auto-runner is active in background. Press Ctrl+C to exit.[/green]\n")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Auto-runner stopped cleanly.")
        console.print("[yellow]Auto-runner stopped.[/yellow]")


def list_schedule(tz_name: str | None = None, lead_minutes: int = 30):
    """CLI utility to view all scheduled triggers without running"""
    tz = get_timezone(tz_name)
    mgr = AccountManager()
    accounts = mgr.get_all()

    table = Table(title=f"📅 Scheduled Trigger Times ({tz.zone})", border_style="cyan")
    table.add_column("Account", style="bold white")
    table.add_column("Niche", style="magenta")
    table.add_column("Content Type", style="cyan")
    table.add_column("🛠️ Video Gen (-30m)", style="yellow")
    table.add_column("📤 Live Post", style="green")

    for account in accounts:
        for ct, times in account.schedule.items():
            for t_str in times:
                h, m = map(int, t_str.split(":"))
                pre_h, pre_m = calculate_lead_time(h, m, lead_minutes)
                table.add_row(
                    account.name,
                    account.niche,
                    ct,
                    f"{pre_h:02d}:{pre_m:02d}",
                    t_str
                )

    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightweight 30-min Lead-Time Auto Runner")
    parser.add_argument("--tz", default=None, help="Timezone (e.g. Asia/Dhaka, US/Eastern, or local)")
    parser.add_argument("--lead", type=int, default=30, help="Lead time in minutes before post (default: 30)")
    parser.add_argument("--test", action="store_true", help="Test mode (no publishing)")
    parser.add_argument("--list", action="store_true", help="Print schedule table and exit")
    args = parser.parse_args()

    if args.list:
        list_schedule(args.tz, args.lead)
    else:
        asyncio.run(run_daemon(lead_minutes=args.lead, tz_name=args.tz, test_mode=args.test))
