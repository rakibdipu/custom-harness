"""
Avatar Pipeline — main orchestrator.

Usage:
    pipeline = AvatarPipeline("my_project")
    await pipeline.load_character("character.png")
    video = await pipeline.generate_video(
        script="Hello everyone!",
        background="classroom",
        emotion="happy",
    )
"""
import asyncio
import json
import logging
from pathlib import Path

from avatar.character_engine import CharacterEngine
from avatar.animator import FastCartoonAnimator
from avatar.scene_composer import SceneComposer

logger = logging.getLogger(__name__)

# Reuse existing TTS engine
try:
    from media.tts_engine import TTSEngine
    _HAS_TTS = True
except ImportError:
    _HAS_TTS = False
    logger.warning("TTSEngine not found — audio must be provided manually")


class AvatarPipeline:
    """Full pipeline: character → animation → scene → video."""

    def __init__(self, project_name: str, output_dir: str = "output/avatar_projects"):
        self.project_name = project_name
        self.project_dir = Path(output_dir) / project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / "audio").mkdir(exist_ok=True)
        (self.project_dir / "final").mkdir(exist_ok=True)

        self.char_engine = CharacterEngine(self.project_dir)
        self.animator = FastCartoonAnimator()
        self.composer = SceneComposer()

        self._char_profile: dict = {}
        logger.info(f"AvatarPipeline ready: {self.project_dir}")

    # ─────────────────────────────────────────────────────────────
    async def load_character(self, image_path: str) -> dict:
        """Prepare character image for animation."""
        logger.info(f"Loading character: {image_path}")
        self._char_profile = await self.char_engine.load_character(image_path)
        logger.info(f"Character loaded: {self._char_profile['body_type']}")
        return self._char_profile

    # ─────────────────────────────────────────────────────────────
    async def generate_video(
        self,
        script: str,
        background: str = "studio",
        emotion: str = "neutral",
        gesture: str = "idle",
        voice: str = "en-US-GuyNeural",
        subtitle: bool = True,
        shot_type: str = "medium",
        output_filename: str = None,
        fps: int = 30,
        quality: str = "balanced",  # fast | balanced | quality
        audio_path: str = None,     # pre-existing audio (skip TTS)
    ) -> str:
        """Full pipeline → returns path to final MP4."""
        if not self._char_profile:
            raise RuntimeError("No character loaded. Call load_character() first.")

        if output_filename is None:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{self.project_name}_{ts}.mp4"

        final_path = str(self.project_dir / "final" / output_filename)

        # ── Quality → fps adjustment ──────────────────────────────
        quality_fps = {"fast": 15, "balanced": 24, "quality": 30}
        effective_fps = quality_fps.get(quality, fps)

        # ── 1. Generate TTS ───────────────────────────────────────
        if audio_path is None:
            audio_path = str(self.project_dir / "audio" / "voice.mp3")
            logger.info(f"Generating TTS: '{script[:60]}...'")
            await self._generate_tts(script, voice, audio_path)

        # ── 2. Get audio duration ─────────────────────────────────
        duration = await self._get_duration(audio_path)
        logger.info(f"Audio duration: {duration:.1f}s")

        # ── 3. Render background ──────────────────────────────────
        logger.info(f"Rendering background: {background}")
        bg_img = self.composer.render_background(background)

        # ── 4. Load character ─────────────────────────────────────
        char_png = self._char_profile.get("processed",
            str(self.project_dir / "character" / "character.png"))

        # ── 5. Animate ────────────────────────────────────────────
        logger.info(f"Animating ({emotion}, {gesture}, fps={effective_fps})...")
        raw_video = str(self.project_dir / "final" / f"_raw_{output_filename}")

        await self.animator.create_talking_clip(
            character_png=char_png,
            character_profile=self._char_profile,
            audio_path=audio_path,
            emotion=emotion,
            gesture=gesture,
            duration=duration,
            output_path=raw_video,
            background_img=bg_img,
            width=self.composer.width,
            height=self.composer.height,
            fps=effective_fps,
        )

        # ── 6. Add UI overlay (watermark + subtitle) ──────────────
        if subtitle:
            logger.info("Adding subtitle overlay...")
            await self._burn_subtitles(raw_video, script, duration, final_path)
        else:
            import shutil
            shutil.move(raw_video, final_path)

        # Cleanup raw
        try:
            Path(raw_video).unlink(missing_ok=True)
        except Exception:
            pass

        size_mb = Path(final_path).stat().st_size / 1024 / 1024
        logger.info(f"✅ Avatar video ready: {final_path} ({size_mb:.1f} MB)")
        return final_path

    # ─────────────────────────────────────────────────────────────
    async def generate_preview(
        self,
        script: str,
        preview_duration: float = 4.0,
        **kwargs,
    ) -> str:
        """Generate short preview clip (first N seconds)."""
        logger.info(f"Generating {preview_duration}s preview...")
        kwargs["output_filename"] = "preview.mp4"
        # Truncate script to ~preview_duration worth of text
        words = script.split()
        approx_words = int(preview_duration * 2.5)  # ~2.5 words/sec
        short_script = " ".join(words[:approx_words])
        return await self.generate_video(short_script, quality="fast", **kwargs)

    # ─────────────────────────────────────────────────────────────
    def get_project_info(self) -> dict:
        return {
            "name": self.project_name,
            "project_dir": str(self.project_dir),
            "character_loaded": bool(self._char_profile),
            "character_profile": self._char_profile,
        }

    # ─────────────────────────────────────────────────────────────
    async def _generate_tts(self, text: str, voice: str, output_path: str):
        """Generate TTS using existing TTSEngine."""
        if not _HAS_TTS:
            raise RuntimeError("TTSEngine not available. Provide audio_path manually.")

        tts = TTSEngine()
        # TTSEngine.generate(text, output_dir) → (audio_path, segments)
        out_dir = str(Path(output_path).parent)
        audio_p, _ = await tts.generate(text, output_dir=out_dir)

        if not Path(audio_p).exists():
            raise RuntimeError(f"TTS failed — no audio file at {audio_p}")

        # Move/rename to expected output_path if different
        if str(Path(audio_p).resolve()) != str(Path(output_path).resolve()):
            import shutil
            shutil.move(audio_p, output_path)


    async def _get_duration(self, audio_path: str) -> float:
        """Get audio duration via ffprobe."""
        import shutil
        ffprobe = shutil.which("ffprobe") or "ffprobe"
        proc = await asyncio.create_subprocess_exec(
            ffprobe, "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", audio_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except ValueError:
            return 30.0

    async def _burn_subtitles(
        self,
        input_video: str,
        script: str,
        duration: float,
        output_path: str,
    ):
        """Burn simple subtitle via FFmpeg drawtext."""
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

        # Split script into ~sentence chunks with timing
        words = script.split()
        wps = len(words) / max(duration, 1)  # words per second
        chunk_size = max(4, int(wps * 4))    # ~4 seconds per subtitle

        # Build ASS subtitle file
        ass_path = str(Path(input_video).parent / "_subs.ass")
        self._write_simple_ass(script, duration, ass_path)

        ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
        cmd = [
            ffmpeg, "-y",
            "-i", input_video,
            "-vf", f"ass={ass_escaped}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "copy",
            output_path,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            # Subtitle failed — just copy without subtitles
            logger.warning(f"Subtitle burn failed: {stderr.decode()[-200:]}")
            shutil.copy(input_video, output_path)

        try:
            Path(ass_path).unlink(missing_ok=True)
        except Exception:
            pass

    def _write_simple_ass(self, script: str, duration: float, path: str):
        """Write simple ASS subtitle file."""
        words = script.split()
        wps = max(len(words) / duration, 1.5)
        chunk_size = max(5, int(wps * 3.5))

        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))

        time_per_chunk = duration / max(len(chunks), 1)

        def fmt(s: float) -> str:
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            ss = s % 60
            return f"{h}:{m:02d}:{ss:05.2f}"

        lines = [
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
            "1,0,0,0,100,100,2,0,1,3,2,2,60,60,120,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        ]

        for i, chunk in enumerate(chunks):
            start = i * time_per_chunk
            end = min((i + 1) * time_per_chunk, duration)
            lines.append(f"Dialogue: 0,{fmt(start)},{fmt(end)},Default,,0,0,0,,{chunk}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
