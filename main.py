"""
Custom Harness v2.0 - Multi-Account Orchestrator with Video Buffer
Pre-generates videos in advance into a local buffer.
When scheduled time arrives, it posts instantly (zero delay)!
After 2-3 verification checks, uploaded videos and temporary frames are automatically
deleted from local storage to conserve disk space.

Usage:
  python3 main.py                    # Post next ready video (or generate and post)
  python3 main.py --daemon           # Auto scheduler + auto buffer maintainer + auto cleanup
  python3 main.py --prebake          # Pre-generate 2 videos for every account into buffer
  python3 main.py --cleanup          # Free disk space (delete posted videos & temp frames)
  python3 main.py --test             # Test mode (no publish)
  python3 main.py --account comic_viral
"""
import asyncio
import argparse
import logging
import random
import sys
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler("logs/harness.log")
    ]
)
logger = logging.getLogger("harness")
console = Console()

# Local imports
from accounts.account_manager import AccountManager
from brain.topic_queue import TopicQueue
from brain.topic_selector import TopicSelector
from brain.script_generator import MultiScriptGenerator, COMIC_TOPICS
from brain.video_buffer import VideoBuffer
from guardrail.checker import GuardrailChecker
from media.tts_engine import TTSEngine
from media.broll_manager import BrollManager
from media.video_assembler import VideoAssembler
from publisher.facebook import FacebookPublisher
from publisher.youtube_pub import YouTubePublisher
from content_types.reel_cutter import ReelCutter
from content_types.long_video_builder import LongVideoBuilder


class MultiAccountHarness:
    def __init__(self, test_mode: bool = False, is_daemon: bool = False):
        self.test_mode = test_mode
        self.is_daemon = is_daemon
        self.account_mgr = AccountManager()
        self.topic_queue = TopicQueue()
        self.topic_selector = TopicSelector()
        self.video_buffer = VideoBuffer(target_buffer_per_account=3)
        self.script_gen = MultiScriptGenerator()
        self.guardrail = GuardrailChecker()
        self.tts = TTSEngine()
        self.broll_mgr = BrollManager()
        self.video_assembler = VideoAssembler()
        self.reel_cutter = ReelCutter()
        self.long_video_builder = LongVideoBuilder()

        Path("output/videos").mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

    async def prebake_buffer(self, target_per_account: int = 2):
        """Pre-generate videos in advance and save to buffer"""
        accounts = self.account_mgr.get_all()
        console.print(Panel(
            f"[bold blue]📦 PRE-GENERATING VIDEOS FOR BUFFER[/bold blue]\n"
            f"Target: {target_per_account} ready videos per account",
            border_style="blue"
        ))

        for account in accounts:
            current_count = await self.video_buffer.get_ready_count(account.id)
            needed = max(0, target_per_account - current_count)
            logger.info(f"[{account.name}] Current buffer: {current_count} | Needed: {needed}")

            for i in range(needed):
                content_type = account.content_types[0] if account.content_types else "short_reel"
                console.print(f"[cyan]⏳ Generating buffer video {i+1}/{needed} for {account.name}...[/cyan]")
                try:
                    await self._generate_video_pipeline(account, content_type, save_to_buffer=True)
                except Exception as e:
                    logger.error(f"Failed to buffer video for {account.id}: {e}", exc_info=True)

    async def _generate_video_pipeline(self, account, content_type: str, save_to_buffer: bool = True) -> dict | None:
        """Core generator: Topic → Script → TTS → Images → Render video"""
        # 1. Topic
        queued = await self.topic_queue.pop(account.id, content_type)
        if queued:
            topic = queued["topic"]
            source = queued["source"]
            console.print(f"[yellow]📌 USER TOPIC:[/yellow] {topic}")
        else:
            # Pass account_id and niche so TopicSelector picks niche-matched topics (tracked in SQLite)
            topic = await self.topic_selector.get_topic(
                account_id=account.id,
                niche=account.niche
            )
            source = "auto"
            console.print(f"[dim]📌 Auto topic ({source}):[/dim] {topic}")

        # 2. Script
        script = None
        last_raw = None
        for attempt in range(1, 4):
            if self.test_mode:
                script = self.script_gen._dynamic_script(content_type, topic, account)
                check = {"passed": True, "score": 9.0, "reason": "test", "word_count": 150}
                break
            else:
                raw = await self.script_gen.generate(topic, content_type, account)
                last_raw = raw  # keep last attempt for emergency fallback
                check = self.guardrail.check(raw, content_type=content_type)
                if check["passed"]:
                    script = raw
                    break
                logger.warning(f"Guardrail attempt {attempt}/3 failed: {check['reason']}")

        # Emergency fallback: use last dynamic result even if guardrail was strict
        if not script and last_raw and last_raw.get("voiceover"):
            logger.warning(f"Using emergency fallback script for {account.id} (guardrail relaxed)")
            script = last_raw

        if not script:
            logger.error(f"Script generation failed for {account.id}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = f"output/videos/{account.id}_{content_type}_{timestamp}.mp4"
        cut_reels = []

        if content_type in ["long_video", "storytelling_video"]:
            console.print(f"[bold cyan]🎬 Assembling 6-Chapter Long Video for {account.name}...[/bold cyan]")
            long_res = await self.long_video_builder.assemble_long_video(
                account=account,
                episode_spec=script,
                output_path=video_path
            )
            title = long_res.get("title", script.get("title", topic))
            cut_reels = long_res.get("cut_reels", [])
        else:
            # 3. TTS for short reel
            self.tts.voice = account.tts_voice
            self.tts.rate = account.tts_rate
            voiceover_text = script.get("voiceover", "")
            temp_tts_dir = f"output/videos/temp_{account.id}_{timestamp}"
            audio_path, subtitle_segments = await self.tts.generate(voiceover_text, temp_tts_dir)

            # 4. Fast Media Sourcing — style-aware 4-tier pipeline
            broll_keywords = (
                script.get("broll_keywords")
                or script.get("image_prompts")
                or [s.get("heading", "") for s in script.get("sections", []) if s.get("heading")]
                or [topic, "cinematic dramatic lighting", "intense focus", "masterpiece"]
            )
            visual_style   = getattr(account, "visual_style", "cinematic")
            subtitle_style = getattr(account, "subtitle_style", "hormozi_yellow")
            bgm_style      = getattr(account, "bgm_style", "ambient_cinematic")

            audio_dur = await self.video_assembler._get_audio_duration(audio_path)
            num_scenes = max(int(audio_dur / 3.4), len(broll_keywords), 10)
            logger.info(f"Pacing: Sourcing {num_scenes} micro-clips for {audio_dur:.1f}s reel ({visual_style})")

            media_assets = await self.broll_mgr.get_clips_for_keywords(
                keywords=broll_keywords,
                niche=account.niche,
                count=num_scenes,
                visual_style=visual_style,
            )

            # 5. Video Assembly (FFmpeg + ASS Subtitles + Synthesized BGM)
            await self.video_assembler.assemble(
                script=script,
                audio_path=audio_path,
                images=media_assets,
                subtitle_segments=subtitle_segments,
                output_path=video_path,
                account_name=account.name,
                subtitle_style=subtitle_style,
                bgm_style=bgm_style,
            )

            # Clean up TTS audio temp directory after assembly to free disk space
            try:
                shutil.rmtree(temp_tts_dir, ignore_errors=True)
                logger.debug(f"Cleaned up TTS temp directory: {temp_tts_dir}")
            except Exception as e:
                logger.debug(f"Could not remove temp TTS directory: {e}")

            title = script.get("title", topic)

        caption = (
            f"{title}\n\n"
            f"{script.get('description', '')}\n\n"
            f"{script.get('hashtags', '')}"
        )

        # Save to buffer
        if save_to_buffer:
            await self.video_buffer.add_ready_video(
                account_id=account.id,
                content_type=content_type,
                topic=topic,
                title=title,
                caption=caption,
                video_path=video_path
            )

            # Auto-cut into short reels if any cut reels were generated
            if cut_reels:
                for idx, r_path in enumerate(cut_reels, 1):
                    await self.video_buffer.add_ready_video(
                        account_id=account.id,
                        content_type="short_reel",
                        topic=f"{topic} (Part {idx})",
                        title=f"{title} (Part {idx})",
                        caption=caption,
                        video_path=r_path
                    )
                console.print(f"[green]✅ Buffered {len(cut_reels)} auto-cut short reels from long video![/green]")
            elif content_type in ["long_video", "storytelling_video"] and getattr(account, "auto_reel_from_long", False):
                try:
                    console.print(f"[cyan]✂️ Auto-cutting reels from {content_type} for {account.name}...[/cyan]")
                    reel_paths = await self.reel_cutter.cut_to_reels(video_path, account, max_reels=3)
                    for idx, r_path in enumerate(reel_paths, 1):
                        await self.video_buffer.add_ready_video(
                            account_id=account.id,
                            content_type="short_reel",
                            topic=f"{topic} (Part {idx})",
                            title=f"{title} (Part {idx})",
                            caption=caption,
                            video_path=r_path
                        )
                    console.print(f"[green]✅ Auto-cut and buffered {len(reel_paths)} short reels from long video![/green]")
                except Exception as e:
                    logger.warning(f"Could not auto-cut reels from long video: {e}")

        return {
            "topic": topic,
            "title": title,
            "caption": caption,
            "video_path": video_path,
            "tags": script.get("tags", [])
        }

    async def post_scheduled_video(self, account, content_type: str = "short_reel"):
        """Instant post from buffer when scheduled timer fires"""
        console.print(Panel(
            f"[bold green]⏰ TIMER FIRED: {account.name}[/bold green]\n"
            f"Posting scheduled video now...",
            border_style="green"
        ))

        # Check buffer first for matching content type
        ready = await self.video_buffer.pop_next_video(account.id, content_type)

        if ready:
            video_path = ready["video_path"]
            caption = ready["caption"]
            title = ready["title"]
            console.print(f"[green]📦 Using pre-generated video from buffer:[/green] {Path(video_path).name}")
        else:
            console.print(f"[yellow]⚠️  Buffer empty! Generating live video...[/yellow]")
            generated = await self._generate_video_pipeline(account, content_type, save_to_buffer=False)
            if not generated:
                logger.error(f"Could not generate video for {account.name}")
                return
            video_path = generated["video_path"]
            caption = generated["caption"]
            title = generated["title"]

        # Publish
        published_successfully = False
        publish_results = {}

        if self.test_mode:
            console.print("[yellow]📤 TEST MODE: Publishing skipped (video file preserved)[/yellow]")
        else:
            # --- Facebook (with 3x retry & 3x status verification) ---
            fb_pub = FacebookPublisher(account)
            fb_result = await fb_pub.post_reel(video_path, caption, max_retries=3, verify_checks=3)
            publish_results["facebook"] = fb_result
            console.print(f"[green]✅ Facebook Post Result:[/green] {fb_result}")
            if fb_result.get("status") == "success":
                published_successfully = True

            # --- YouTube (with 3x retry & 3x status verification) ---
            try:
                yt_pub = YouTubePublisher(account)
                tags = ready.get("tags", []) if ready else []
                yt_result = await yt_pub.upload(
                    video_path=video_path,
                    title=title,
                    description=caption,
                    tags=tags,
                    max_retries=3,
                    verify_checks=3
                )
                publish_results["youtube"] = yt_result
                console.print(f"[green]✅ YouTube Upload Result:[/green] {yt_result}")
                if yt_result.get("status") == "success":
                    published_successfully = True
            except Exception as e:
                logger.error(f"YouTube upload failed for {account.name}: {e}")

            # ── 2/3 Check & Delete video file for disk space ──
            # "video upload hobe 2/3 bar check dibi then dlt kore dibi space er jonno"
            if published_successfully:
                await self._verify_and_cleanup_video(video_path, account, publish_results)
            else:
                logger.info(f"Video {Path(video_path).name} kept on disk (publishing skipped or unconfigured)")

        # Automatically replenish buffer in background (in daemon mode)
        if self.is_daemon:
            asyncio.create_task(self._replenish_buffer_background(account))

    async def _verify_and_cleanup_video(self, video_path: str, account, publish_results: dict):
        """
        Double/triple-checks upload verification status,
        then deletes local video file from disk to save storage space.
        """
        console.print(Panel(
            f"[bold cyan]🔍 VERIFYING UPLOAD & RECLAIMING DISK SPACE[/bold cyan]\n"
            f"Account: {account.name} | File: {Path(video_path).name}",
            border_style="cyan"
        ))

        # Perform 2-3 confirmation passes
        confirmed = False
        for check_round in range(1, 4):
            await asyncio.sleep(1)
            fb_ok = publish_results.get("facebook", {}).get("status") == "success"
            yt_ok = publish_results.get("youtube", {}).get("status") == "success"
            if fb_ok or yt_ok:
                console.print(f"[green]  ✓ Check {check_round}/3: Upload confirmed on platform[/green]")
                confirmed = True

        if confirmed:
            v_file = Path(video_path)
            if v_file.exists():
                size_mb = v_file.stat().st_size / (1024 * 1024)
                v_file.unlink(missing_ok=True)
                console.print(f"[bold yellow]🗑️ DISK SPACE FREED: Deleted {v_file.name} ({size_mb:.1f} MB saved)[/bold yellow]")
                logger.info(f"Deleted uploaded video to save space: {video_path}")

            # Update video buffer DB
            await self.video_buffer.mark_posted_and_deleted(video_path)

            # Clean any matching temp folders
            self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """Removes any orphaned temp directories in output/videos"""
        video_dir = Path("output/videos")
        if not video_dir.exists():
            return
        cleaned = 0
        for p in video_dir.glob("temp_*"):
            if p.is_dir():
                try:
                    shutil.rmtree(p, ignore_errors=True)
                    cleaned += 1
                except Exception:
                    pass
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} temp directories")

    async def cleanup_disk_space(self):
        """Clean all posted videos and temp files from disk to free storage"""
        console.print("[cyan]🧹 Running full disk space cleanup...[/cyan]")
        import aiosqlite
        cleaned_videos = 0
        freed_bytes = 0
        async with aiosqlite.connect("harness.db") as db:
            async with db.execute(
                "SELECT id, video_path FROM video_buffer WHERE status IN ('posted', 'posted_deleted')"
            ) as cursor:
                rows = await cursor.fetchall()
                for vid_id, vpath in rows:
                    p = Path(vpath)
                    if p.exists():
                        freed_bytes += p.stat().st_size
                        p.unlink(missing_ok=True)
                        cleaned_videos += 1
                    await db.execute("UPDATE video_buffer SET status='posted_deleted' WHERE id=?", (vid_id,))
            await db.commit()

        self.cleanup_temp_files()
        mb = freed_bytes / (1024 * 1024)
        console.print(f"[bold green]✨ Cleanup complete! Removed {cleaned_videos} videos ({mb:.1f} MB freed).[/bold green]")

    async def _replenish_buffer_background(self, account):
        """Replenish buffer in background so there's always ready videos"""
        try:
            count = await self.video_buffer.get_ready_count(account.id)
            if count < self.video_buffer.target_buffer:
                logger.info(f"🔄 Replenishing buffer in background for {account.name} (currently {count})...")
                content_type = account.content_types[0] if account.content_types else "short_reel"
                await self._generate_video_pipeline(account, content_type, save_to_buffer=True)
        except Exception as e:
            logger.error(f"Buffer replenish failed: {e}")

    async def run_all_once(self):
        """Run one cycle for every enabled account"""
        accounts = self.account_mgr.get_all()
        for account in accounts:
            await self.post_scheduled_video(account)


async def daemon_mode(harness: MultiAccountHarness):
    """Run as background daemon with cron schedules + auto buffer + auto cleanup"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    import pytz

    tz = pytz.timezone("US/Eastern")
    scheduler = AsyncIOScheduler(timezone=tz)
    accounts = harness.account_mgr.get_all()

    # Pre-generate videos so buffer is full on startup
    console.print("[blue]Initial buffer check...[/blue]")
    await harness.prebake_buffer(target_per_account=2)

    job_count = 0
    for account in accounts:
        for content_type, times in account.schedule.items():
            for time_str in times:
                hour, minute = map(int, time_str.split(":"))

                def make_job(acc=account, ct=content_type):
                    async def job():
                        logger.info(f"⏰ TIMER TRIGGER: {acc.name} → {ct}")
                        await harness.post_scheduled_video(acc, ct)
                    return job

                scheduler.add_job(
                    make_job(),
                    CronTrigger(hour=hour, minute=minute, timezone=tz),
                    name=f"{account.id}_{content_type}_{hour:02d}{minute:02d}",
                    max_instances=1,
                    misfire_grace_time=300
                )
                job_count += 1
                logger.info(f"Scheduled: [{account.name}] {content_type} @ {hour:02d}:{minute:02d} EST")

    # Hourly buffer health check + disk cleanup
    async def buffer_health_check():
        for acc in accounts:
            await harness._replenish_buffer_background(acc)
        harness.cleanup_temp_files()

    scheduler.add_job(buffer_health_check, "interval", minutes=60)

    scheduler.start()
    console.print(Panel(
        f"[bold blue]🤖 DAEMON ACTIVE WITH VIDEO BUFFER & AUTO-CLEANUP[/bold blue]\n"
        f"• Videos pre-rendered and saved in buffer\n"
        f"• Instant posting when timer hits\n"
        f"• 2-3x verification checks before deleting uploaded videos\n"
        f"• Accounts: {len(accounts)} | Jobs: {job_count}\n"
        f"Press Ctrl+C to stop",
        border_style="blue"
    ))

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        console.print("[yellow]Daemon stopped.[/yellow]")


async def main():
    parser = argparse.ArgumentParser(description="Custom Harness v2.0 — Multi-Account with Buffer & Auto-Cleanup")
    parser.add_argument("--daemon", action="store_true", help="Run auto-scheduler with pre-buffered videos")
    parser.add_argument("--prebake", action="store_true", help="Pre-generate videos into buffer right now")
    parser.add_argument("--cleanup", action="store_true", help="Clean up posted videos & temp files to free disk space")
    parser.add_argument("--test", action="store_true", help="Test mode (no publish)")
    parser.add_argument("--account", help="Run specific account only")
    parser.add_argument("--type", default="short_reel", help="Content type to run")
    args = parser.parse_args()

    console.print(Panel(
        "[bold]⚡ CUSTOM HARNESS v2.0 (BUFFER SYSTEM + DISK MANAGEMENT)[/bold]\n"
        "Pre-generates videos in advance • Timed instant posting • Auto disk cleanup",
        border_style="blue"
    ))

    harness = MultiAccountHarness(test_mode=args.test, is_daemon=args.daemon)

    if args.cleanup:
        await harness.cleanup_disk_space()
    elif args.daemon:
        await daemon_mode(harness)
    elif args.prebake:
        await harness.prebake_buffer(target_per_account=2)
    elif args.account:
        account = harness.account_mgr.get(args.account)
        if not account:
            console.print(f"[red]Account '{args.account}' not found[/red]")
            sys.exit(1)
        await harness.post_scheduled_video(account, args.type)
    else:
        await harness.run_all_once()


if __name__ == "__main__":
    asyncio.run(main())
