"""
Auto Reel Cutter
Takes a long video and automatically cuts it into 45-60s Reels
Uses FFmpeg silence detection to find natural cut points
"""
import asyncio
import logging
import re
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str:
    """Find ffmpeg binary — honours ~/.local/bin set in config.py PATH patch"""
    return shutil.which("ffmpeg") or "ffmpeg"


def _find_ffprobe() -> str:
    """Find ffprobe binary — honours ~/.local/bin set in config.py PATH patch"""
    return shutil.which("ffprobe") or "ffprobe"


class ReelCutter:
    """Cuts long videos into platform-ready reels"""

    REEL_MIN = 40    # seconds
    REEL_MAX = 60    # seconds
    SILENCE_DB = -35  # dB threshold for silence detection

    async def cut_to_reels(
        self,
        video_path: str,
        account,
        max_reels: int = 5,
        output_dir: str = "output/videos"
    ) -> list[str]:
        """
        Auto-cut a long video into multiple reels.
        Returns list of reel file paths.
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        duration = await self._get_duration(video_path)
        logger.info(f"Source video: {duration:.0f}s — cutting into reels...")

        # Find natural cut points via silence detection
        cut_points = await self._find_cut_points(video_path, duration)
        logger.info(f"Found {len(cut_points)} potential cut points")

        # Build reel segments (40-60s each)
        segments = self._build_segments(cut_points, duration)
        segments = segments[:max_reels]
        logger.info(f"Cutting {len(segments)} reels from long video")

        reel_paths = []
        for i, (start, end) in enumerate(segments):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reel_path = f"{output_dir}/reel_{i+1}_{timestamp}.mp4"
            await self._cut_segment(
                video_path, start, end, reel_path, account, i + 1, len(segments)
            )
            reel_paths.append(reel_path)
            logger.info(f"Reel {i+1}/{len(segments)}: {start:.1f}s–{end:.1f}s → {reel_path}")

        return reel_paths

    async def _get_duration(self, video_path: str) -> float:
        ffprobe_bin = _find_ffprobe()
        proc = await asyncio.create_subprocess_exec(
            ffprobe_bin, "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return float(stdout.decode().strip() or "0")

    async def _find_cut_points(self, video_path: str, duration: float) -> list[float]:
        """Use FFmpeg silencedetect to find good cut points"""
        ffmpeg_bin = _find_ffmpeg()
        proc = await asyncio.create_subprocess_exec(
            ffmpeg_bin, "-i", video_path,
            "-af", f"silencedetect=noise={self.SILENCE_DB}dB:d=0.3",
            "-f", "null", "-",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        output = stderr.decode()

        # Parse silence_end times (these are natural cut points)
        silence_ends = re.findall(r"silence_end: (\d+\.?\d*)", output)
        cut_points = [float(t) for t in silence_ends]

        # Always include start and end
        cut_points = [0.0] + sorted(cut_points) + [duration]
        return cut_points

    def _build_segments(
        self, cut_points: list[float], total_duration: float
    ) -> list[tuple[float, float]]:
        """Build 40-60s segments from cut points"""
        segments = []
        current_start = 0.0

        for i in range(len(cut_points)):
            elapsed = cut_points[i] - current_start
            if elapsed >= self.REEL_MIN:
                # Good segment — use it or extend to next cut point
                if elapsed <= self.REEL_MAX or i == len(cut_points) - 1:
                    end = min(cut_points[i], total_duration)
                    segments.append((current_start, end))
                    current_start = cut_points[i]

        return segments

    async def _cut_segment(
        self,
        source: str,
        start: float,
        end: float,
        output_path: str,
        account,
        reel_num: int,
        total_reels: int
    ):
        """Cut one segment cleanly from long video preserving all styling"""
        ffmpeg_bin = _find_ffmpeg()
        duration = end - start

        # Clean cut preserving high quality video & audio
        cmd = [
            ffmpeg_bin, "-y",
            "-ss", str(start),
            "-i", source,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"FFmpeg cut failed: {stderr.decode()[-300:]}")
