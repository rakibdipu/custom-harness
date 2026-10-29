"""
CLI Dashboard - Control everything from one terminal
Usage: python3 cli.py
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Ensure root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from brain.topic_queue import TopicQueue
from accounts.account_manager import AccountManager

console = Console()
queue = TopicQueue()
account_mgr = AccountManager()


async def cmd_add_topic(args):
    """Add a user topic to the queue"""
    accounts = account_mgr.get_all()
    if not accounts:
        console.print("[red]No accounts configured[/red]")
        return

    # Show account list
    table = Table(title="Available Accounts")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Content Types")
    for acc in accounts:
        table.add_row(acc.id, acc.name, ", ".join(acc.content_types))
    console.print(table)

    if args.account:
        account_id = args.account
    else:
        account_id = Prompt.ask("Account ID")

    account = account_mgr.get(account_id)
    if not account:
        console.print(f"[red]Account '{account_id}' not found[/red]")
        return

    if args.topic:
        topic = args.topic
    else:
        topic = Prompt.ask("Topic")

    # Content type
    types = account.content_types
    if len(types) == 1:
        content_type = types[0]
    elif args.type:
        content_type = args.type
    else:
        console.print(f"Content types: {types}")
        content_type = Prompt.ask("Content type", default=types[0])

    await queue.push(topic=topic, account_id=account_id,
                     content_type=content_type, source="user")
    console.print(Panel(
        f"[green]✅ Topic queued![/green]\n"
        f"Account: {account.name}\n"
        f"Type: {content_type}\n"
        f"Topic: {topic}",
        border_style="green"
    ))


async def cmd_list_queue(args):
    """Show all pending topics"""
    topics = await queue.peek_all(args.account if args.account else None)
    if not topics:
        console.print("[yellow]No pending topics in queue[/yellow]")
        return

    table = Table(title=f"Pending Topics ({len(topics)} total)")
    table.add_column("#", width=4)
    table.add_column("Account", style="cyan")
    table.add_column("Topic")
    table.add_column("Type", style="magenta")
    table.add_column("Source", style="green")
    table.add_column("Added")

    for i, t in enumerate(topics, 1):
        source_style = "[bold yellow]USER[/bold yellow]" if t["source"] == "user" else "auto"
        table.add_row(
            str(i), t["account"], t["topic"][:60],
            t["type"], source_style, t["added"][:16]
        )
    console.print(table)


async def cmd_status(args):
    """Show harness status"""
    accounts = account_mgr.get_all(enabled_only=False)
    table = Table(title="Harness Status")
    table.add_column("Account", style="cyan")
    table.add_column("Name")
    table.add_column("Niche")
    table.add_column("Content Types")
    table.add_column("Schedule")
    table.add_column("Status")
    table.add_column("Pending Topics", justify="right")

    for acc in accounts:
        pending = await queue.pending_count(acc.id)
        status = "[green]✅ ON[/green]" if acc.enabled else "[red]⏸️ OFF[/red]"
        times = " / ".join([
            f"{ct}: {','.join(times)}"
            for ct, times in acc.schedule.items()
        ])
        table.add_row(
            acc.id, acc.name, acc.niche[:30],
            ", ".join(acc.content_types),
            times, status, str(pending)
        )
    console.print(table)


async def cmd_buffer(args):
    """Show all pre-generated ready videos waiting in buffer"""
    from brain.video_buffer import VideoBuffer
    vb = VideoBuffer()
    videos = await vb.list_ready_videos(args.account if args.account else None)
    if not videos:
        console.print("[yellow]📦 Video buffer is empty. Run: python3 main.py --prebake to generate ready videos![/yellow]")
        return

    table = Table(title=f"📦 Ready-Made Videos Waiting to be Posted ({len(videos)} total)")
    table.add_column("#", width=4)
    table.add_column("Account", style="cyan")
    table.add_column("Title")
    table.add_column("Video File", style="green")
    table.add_column("Generated At")

    for i, v in enumerate(videos, 1):
        vname = Path(v["video_path"]).name
        table.add_row(str(i), v["account_id"], v["title"][:45], vname, v["created_at"][:16])
    console.print(table)


async def cmd_run(args):
    """Manually trigger a harness cycle"""
    from main import MultiAccountHarness
    harness = MultiAccountHarness(test_mode=args.test)

    if args.account:
        account = account_mgr.get(args.account)
        if not account:
            console.print(f"[red]Account '{args.account}' not found[/red]")
            return
        await harness.post_scheduled_video(account, args.type or "short_reel")
    else:
        await harness.run_all_once()


async def cmd_cleanup(args):
    """Clean up disk space by removing already posted videos and temp frame folders"""
    from main import MultiAccountHarness
    harness = MultiAccountHarness()
    await harness.cleanup_disk_space()


def main():
    parser = argparse.ArgumentParser(
        description="Custom Harness CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  python3 cli.py status                          Show all accounts and queue
  python3 cli.py buffer                          View pre-generated videos in buffer
  python3 cli.py add -a psychology_mindset -t "dark psychology tricks"
  python3 cli.py add -a storytelling --type storytelling_video
  python3 cli.py queue                           List pending topics
  python3 cli.py run                             Post next ready video for all accounts
  python3 cli.py run -a comic_viral              Post next video for specific account
  python3 cli.py cleanup                         Delete posted videos & temp files to free disk space
        """
    )
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Show harness status")

    # buffer
    p_buf = sub.add_parser("buffer", help="View ready pre-generated videos")
    p_buf.add_argument("-a", "--account", help="Filter by account")

    # add
    p_add = sub.add_parser("add", help="Add a topic to the queue")
    p_add.add_argument("-a", "--account", help="Account ID")
    p_add.add_argument("-t", "--topic", help="Topic text")
    p_add.add_argument("--type", help="Content type")

    # queue
    p_q = sub.add_parser("queue", help="List pending topics")
    p_q.add_argument("-a", "--account", help="Filter by account")

    # run
    p_run = sub.add_parser("run", help="Trigger harness post manually")
    p_run.add_argument("-a", "--account", help="Specific account ID")
    p_run.add_argument("--type", help="Content type")
    p_run.add_argument("--test", action="store_true", help="Test mode (no publish)")

    # cleanup
    sub.add_parser("cleanup", help="Delete posted videos & temp files to free disk space")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    dispatch = {
        "status": cmd_status,
        "buffer": cmd_buffer,
        "add": cmd_add_topic,
        "queue": cmd_list_queue,
        "run": cmd_run,
        "cleanup": cmd_cleanup,
    }
    asyncio.run(dispatch[args.command](args))


if __name__ == "__main__":
    main()
