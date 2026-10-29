"""
Schedule Ready Videos Directly to Facebook Meta Cloud Scheduler
Uploads buffered videos with native Meta timer (scheduled_publish_time)
Facebook will automatically publish them at the scheduled time even if your PC is off!
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from accounts.account_manager import AccountManager
from brain.video_buffer import VideoBuffer
from publisher.facebook import FacebookPublisher
from auto_runner import get_timezone

console = Console()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fb_scheduler")


def get_next_slots(schedule_times: list[str], tz, count: int = 3, min_minutes_ahead: int = 15) -> list[datetime]:
    """Calculate upcoming datetime slots for the given schedule times"""
    now = datetime.now(tz)
    slots = []
    current_day = now.date()

    for day_offset in range(0, 14): # search up to 14 days ahead
        day = current_day + timedelta(days=day_offset)
        for t_str in schedule_times:
            h, m = map(int, t_str.split(":"))
            slot_dt = tz.localize(datetime(day.year, day.month, day.day, h, m))
            if slot_dt > now + timedelta(minutes=min_minutes_ahead):
                slots.append(slot_dt)
                if len(slots) >= count:
                    return slots
    return slots


async def schedule_account_videos(account_id: str = "psychology_mindset", count: int = 3):
    account_mgr = AccountManager()
    account = account_mgr.get(account_id)
    if not account:
        console.print(f"[red]❌ Account '{account_id}' not found[/red]")
        return

    tz = get_timezone()
    video_buffer = VideoBuffer()
    fb_pub = FacebookPublisher(account)

    if not fb_pub._is_configured():
        console.print(f"[red]❌ Facebook is not configured for {account.name}. Check your FB_PAGE_ID and FB_TOKEN in .env[/red]")
        return

    # Fetch ready videos from buffer
    ready_count = await video_buffer.get_ready_count(account.id, "short_reel")
    if ready_count == 0:
        console.print(f"[yellow]⚠️ No ready videos found in buffer for {account.name}.[/yellow]")
        return

    schedule_times = account.schedule.get("short_reel", ["09:00", "13:00", "19:00"])
    upcoming_slots = get_next_slots(schedule_times, tz, count=min(ready_count, count))

    table = Table(title=f"📅 Scheduling Videos to Meta Cloud for {account.name} ({tz.zone})", border_style="blue")
    table.add_column("Slot", style="cyan")
    table.add_column("Scheduled Time", style="green")
    table.add_column("Title", style="yellow")
    table.add_column("Video File", style="dim")
    table.add_column("Status", style="bold")

    for slot_dt in upcoming_slots:
        video_info = await video_buffer.pop_next_video(account.id, "short_reel")
        if not video_info:
            break

        title = video_info["title"]
        caption = video_info["caption"]
        video_path = video_info["video_path"]
        v_id = video_info["id"]

        epoch_timestamp = int(slot_dt.timestamp())
        formatted_time = slot_dt.strftime("%Y-%m-%d %I:%M %p %Z")

        console.print(f"[cyan]🚀 Uploading & Scheduling on Meta:[/cyan] [bold]{title}[/bold] -> [green]{formatted_time}[/green]")

        res = await fb_pub.post_reel(
            video_path=video_path,
            caption=caption,
            scheduled_publish_time=epoch_timestamp
        )

        if res.get("status") == "success":
            # Mark buffer status as scheduled
            import aiosqlite
            async with aiosqlite.connect("harness.db") as db:
                await db.execute(
                    "UPDATE video_buffer SET status='scheduled_meta', posted_at=? WHERE id=?",
                    (slot_dt.isoformat(), v_id)
                )
                await db.commit()

            table.add_row(
                slot_dt.strftime("%I:%M %p"),
                formatted_time,
                title[:35] + ("..." if len(title) > 35 else ""),
                Path(video_path).name,
                "✅ Scheduled on FB"
            )
        else:
            table.add_row(
                slot_dt.strftime("%I:%M %p"),
                formatted_time,
                title[:35],
                Path(video_path).name,
                f"❌ Failed: {res.get('reason', 'error')}"
            )

    console.print(table)
    console.print(Panel(
        "[bold green]✨ Meta Cloud Scheduling Complete![/bold green]\n"
        "Facebook will automatically publish these Reels at the exact scheduled timestamps.\n"
        "You do not need to keep your PC or script running for these scheduled posts.",
        border_style="green"
    ))


if __name__ == "__main__":
    import sys
    acc = sys.argv[1] if len(sys.argv) > 1 else "psychology_mindset"
    asyncio.run(schedule_account_videos(acc))
