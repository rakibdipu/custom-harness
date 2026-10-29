"""
Long Video Builder — Multi-Segment Chapter Rendering & Concat Pipeline
Constructs 5-10 minute long-form videos by:
1. Rendering individual chapter scenes (60-75s each) independently with consistent avatar/styling.
2. Concatenating all scenes into a seamless Master MP4 using FFmpeg concat demuxer.
3. Automatically extracting short reels via ReelCutter for multi-platform distribution.
"""
import asyncio
import logging
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

from media.tts_engine import TTSEngine
from media.broll_manager import BrollManager
from media.video_assembler import VideoAssembler
from content_types.reel_cutter import ReelCutter

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def _find_ffprobe() -> str:
    return shutil.which("ffprobe") or "ffprobe"


class LongVideoBuilder:
    def __init__(self):
        self.tts = TTSEngine()
        self.broll_mgr = BrollManager()
        self.assembler = VideoAssembler()
        self.reel_cutter = ReelCutter()

    async def get_duration(self, video_path: str) -> float:
        """Get duration of video in seconds using ffprobe"""
        ffprobe = _find_ffprobe()
        cmd = [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except Exception:
            return 0.0

    async def assemble_long_video(
        self,
        account,
        episode_spec: dict,
        output_path: str = None
    ) -> dict:
        """
        Takes an episode spec with a list of chapters, renders each chapter,
        and concatenates them into a master episode.
        """
        chapters = episode_spec.get("chapters", [])
        if not chapters:
            raise ValueError("Episode spec must contain at least 2 chapters.")

        title = episode_spec.get("title", "Untitled Episode")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = f"output/videos/{account.id}_long_{timestamp}.mp4"

        temp_dir = Path(f"output/videos/temp_long_{account.id}_{timestamp}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🎬 Starting Long Video Assembly: '{title}' ({len(chapters)} chapters)")

        scene_paths = []
        visual_style = getattr(account, "visual_style", "cinematic")
        subtitle_style = getattr(account, "subtitle_style", "hormozi_yellow")
        bgm_style = getattr(account, "bgm_style", "ambient_cinematic")
        self.tts.voice = account.tts_voice
        self.tts.rate = account.tts_rate

        try:
            for idx, ch in enumerate(chapters, 1):
                ch_title = ch.get("name") or ch.get("title", f"Chapter {idx}")
                voiceover = ch.get("voiceover") or ch.get("script", "")
                if not voiceover:
                    logger.warning(f"Chapter {idx} has no voiceover, skipping.")
                    continue

                logger.info(f"Rendering Chapter {idx}/{len(chapters)}: '{ch_title}'...")

                # 1. TTS for this chapter (unconstrained long-form mode)
                ch_tts_dir = temp_dir / f"tts_ch_{idx}"
                ch_tts_dir.mkdir(exist_ok=True)
                audio_path, subtitles = await self.tts.generate(voiceover, str(ch_tts_dir), is_long_form=True)

                ch_duration = await self.get_duration(audio_path)
                needed_clips = max(len(keywords if 'keywords' in locals() else []), int(ch_duration / 3.4), 12)

                # 2. Media sourcing for this chapter (3.5s micro-clip quota)
                keywords = ch.get("broll_prompts") or [ch_title, account.niche, "cinematic dramatic lighting", "high detail"]
                media_assets = await self.broll_mgr.get_clips_for_keywords(
                    keywords=keywords,
                    niche=account.niche,
                    count=needed_clips,
                    visual_style=visual_style
                )

                # 3. Assemble chapter scene clip with narrative beats
                ch_video_path = str(temp_dir / f"scene_{idx:02d}.mp4")
                is_final_ch = (idx == len(chapters))

                # Divide voiceover into 2-3 narrative beats so sections progress cleanly
                sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', voiceover) if s.strip()]
                if len(sentences) >= 3:
                    third = len(sentences) // 3
                    ch_sections = [
                        {"heading": ch_title[:35], "script": " ".join(sentences[:third])},
                        {"heading": f"{ch_title[:25]} (Analysis)", "script": " ".join(sentences[third:2*third])},
                        {"heading": f"{ch_title[:25]} (Outcome)", "script": " ".join(sentences[2*third:])}
                    ]
                elif len(sentences) == 2:
                    ch_sections = [
                        {"heading": ch_title[:35], "script": sentences[0]},
                        {"heading": f"{ch_title[:25]} (Cont.)", "script": sentences[1]}
                    ]
                else:
                    ch_sections = [{"heading": ch_title[:35], "script": voiceover}]

                chapter_script = {
                    "title": ch_title,
                    "title_card": f"CH {idx}: {ch_title[:20].upper()}",
                    "hook": sentences[0] if sentences else ch_title,
                    "sections": ch_sections,
                    "cta": (episode_spec.get("outro") or f"Follow @{account.name.upper()} for more daily insights!")
                }

                await self.assembler.assemble(
                    script=chapter_script,
                    audio_path=audio_path,
                    images=media_assets,
                    subtitle_segments=subtitles,
                    output_path=ch_video_path,
                    account_name=account.name,
                    subtitle_style=subtitle_style,
                    bgm_style=bgm_style,
                    is_chapter=True,
                    chapter_index=idx,
                    is_final_chapter=is_final_ch,
                    show_cta=is_final_ch
                )

                if Path(ch_video_path).exists():
                    scene_paths.append(ch_video_path)
                else:
                    logger.warning(f"Chapter {idx} render failed, skipping.")

            if not scene_paths:
                raise RuntimeError("Failed to render any chapter scenes.")

            # 4. Write concat manifest
            concat_manifest = temp_dir / "concat_list.txt"
            with open(concat_manifest, "w", encoding="utf-8") as f:
                for sp in scene_paths:
                    f.write(f"file '{Path(sp).resolve()}'\n")

            # 5. FFmpeg concat demuxer
            ffmpeg = _find_ffmpeg()
            concat_cmd = [
                ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_manifest.resolve()),
                "-c", "copy",
                str(Path(output_path).resolve())
            ]

            logger.info("Merging chapter clips into master episode with FFmpeg...")
            proc = await asyncio.create_subprocess_exec(
                *concat_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                # If stream copy fails (e.g. slight timestamp variance), re-encode merge
                logger.warning("Concat copy mode returned non-zero, trying re-encode merge...")
                reencode_cmd = [
                    ffmpeg, "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_manifest.resolve()),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    "-c:a", "aac", "-b:a", "192k",
                    str(Path(output_path).resolve())
                ]
                proc2 = await asyncio.create_subprocess_exec(
                    *reencode_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                _, stderr2 = await proc2.communicate()
                if proc2.returncode != 0:
                    raise Exception(f"FFmpeg concat failed: {stderr2.decode()[-400:]}")

            total_duration = await self.get_duration(output_path)
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Master Episode Ready: {output_path} ({total_duration:.1f}s, {size_mb:.1f} MB)")

            # 6. Auto-cut viral reels if enabled
            cut_reels = []
            if getattr(account, "auto_reel_from_long", False):
                try:
                    logger.info("✂️ Auto-cutting short reels from master video...")
                    cut_reels = await self.reel_cutter.cut_to_reels(output_path, account, max_reels=3)
                    logger.info(f"✅ Cut {len(cut_reels)} short reels from long video.")
                except Exception as e:
                    logger.warning(f"Could not auto-cut reels: {e}")

            return {
                "title": title,
                "output_path": output_path,
                "duration": total_duration,
                "chapters_count": len(scene_paths),
                "cut_reels": cut_reels,
                "description": episode_spec.get("description", ""),
                "hashtags": episode_spec.get("hashtags", ""),
                "tags": episode_spec.get("tags", [])
            }

        finally:
            # Clean up intermediate chapter segments to save disk space
            shutil.rmtree(temp_dir, ignore_errors=True)
