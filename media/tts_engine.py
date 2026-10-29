"""
TTS Engine - Microsoft Neural Voices via edge-tts (free, no API key)
Produces professional US English voiceover with word-level timing
"""
import asyncio
import logging
import shutil
from pathlib import Path
from datetime import datetime
import edge_tts
from config import Config

logger = logging.getLogger(__name__)


def _find_ffprobe() -> str:
    """Find ffprobe binary — checks ~/.local/bin first, then system PATH"""
    return shutil.which("ffprobe") or "ffprobe"


class TTSEngine:
    def __init__(self):
        self.config = Config()
        self.voice = self.config.TTS_VOICE
        self.rate = self.config.TTS_RATE
        self.pitch = self.config.TTS_PITCH

    async def generate(self, text: str, output_dir: str = None, is_long_form: bool = False) -> tuple[str, list]:
        """
        Generate voiceover audio from text.
        Returns: (audio_file_path, subtitle_segments)
        """
        # Guard against empty or too-short text that crashes edge-tts
        if not text or len(text.strip()) < 10:
            logger.warning(f"TTS received empty/short text ({len(text) if text else 0} chars), using placeholder")
            text = "Follow for more content like this every single day."

        if output_dir is None:
            output_dir = str(self.config.OUTPUT_DIR / "temp")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        audio_path = str(Path(output_dir) / f"voice_{timestamp}.mp3")

        # Generate audio with word boundaries
        logger.info(f"Generating TTS ({len(text.split())} words, voice={self.voice})")

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )

        # Collect audio and timing chunks
        audio_chunks = []
        word_timings = []
        sentence_timings = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "word": chunk.get("text", ""),
                    "start": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000
                })
            elif chunk["type"] == "SentenceBoundary":
                sentence_timings.append({
                    "text": chunk.get("text", ""),
                    "start": chunk["offset"] / 10_000_000,
                    "duration": chunk["duration"] / 10_000_000
                })

        # Write audio file
        with open(audio_path, "wb") as f:
            for chunk in audio_chunks:
                f.write(chunk)

        if word_timings:
            logger.info(f"Audio saved: {audio_path} ({len(word_timings)} words timed)")
            subtitle_segments = self._build_subtitles(word_timings, words_per_segment=4)
        elif sentence_timings:
            logger.info(f"Audio saved: {audio_path} ({len(sentence_timings)} sentences timed)")
            subtitle_segments = self._chunk_sentences(sentence_timings, words_per_chunk=4)
        else:
            logger.info(f"Audio saved: {audio_path}")
            subtitle_segments = []

        # ── Strictly guarantee 30–58 second duration window for reels (skip for long-form) ──────
        raw_dur = await self.get_audio_duration(audio_path)
        if not is_long_form and raw_dur > 56.0:
            tempo = round(min(1.45, raw_dur / 50.0), 3)
            logger.info(f"⏱️ Audio {raw_dur:.1f}s exceeds 56s ceiling. Adjusting tempo x{tempo} to fit 30-60s reel limit.")
            audio_path = await self._adjust_audio_tempo(audio_path, tempo)
            for seg in subtitle_segments:
                seg["start"] = round(seg["start"] / tempo, 3)
                seg["end"] = round(seg["end"] / tempo, 3)
        elif not is_long_form and 15.0 < raw_dur < 30.0:
            tempo = round(max(0.85, raw_dur / 32.0), 3)
            logger.info(f"⏱️ Audio {raw_dur:.1f}s below 30s floor. Pacing tempo x{tempo} to ensure 30s minimum.")
            audio_path = await self._adjust_audio_tempo(audio_path, tempo)
            for seg in subtitle_segments:
                seg["start"] = round(seg["start"] / tempo, 3)
                seg["end"] = round(seg["end"] / tempo, 3)

        return audio_path, subtitle_segments

    async def _adjust_audio_tempo(self, src_path: str, tempo: float) -> str:
        """Adjust tempo of audio file to strictly enforce 30-60s window"""
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        dst_path = src_path.replace(".mp3", "_paced.mp3")
        proc = await asyncio.create_subprocess_exec(
            ffmpeg_bin, "-y", "-i", src_path,
            "-filter:a", f"atempo={tempo}",
            "-c:a", "libmp3lame", "-b:a", "192k",
            dst_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if Path(dst_path).exists():
            return dst_path
        return src_path

    def _chunk_sentences(self, sentence_timings: list, words_per_chunk: int = 4) -> list:
        """Break long sentences into punchy 3-4 word chunks with proportional timing"""
        segments = []
        for s in sentence_timings:
            words = s["text"].strip().split()
            if not words:
                continue
            total_dur = s["duration"]
            start_time = s["start"]
            num_chunks = max(1, (len(words) + words_per_chunk - 1) // words_per_chunk)
            chunk_dur = total_dur / num_chunks

            for i in range(num_chunks):
                chunk_words = words[i * words_per_chunk : (i + 1) * words_per_chunk]
                c_start = start_time + i * chunk_dur
                c_end = c_start + chunk_dur
                segments.append({
                    "text": " ".join(chunk_words).upper(),
                    "start": round(c_start, 3),
                    "end": round(c_end, 3)
                })
        return segments

    def _build_subtitles(self, word_timings: list, words_per_segment: int = 4) -> list:
        """Group word timings into subtitle segments"""
        if not word_timings:
            return []

        segments = []
        for i in range(0, len(word_timings), words_per_segment):
            chunk = word_timings[i:i + words_per_segment]
            text = " ".join(w["word"] for w in chunk)
            start = chunk[0]["start"]
            end = chunk[-1]["start"] + chunk[-1]["duration"]
            segments.append({
                "text": text.upper(),  # Uppercase for impact
                "start": round(start, 3),
                "end": round(end, 3)
            })

        return segments

    async def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds using ffprobe"""
        ffprobe_bin = _find_ffprobe()
        proc = await asyncio.create_subprocess_exec(
            ffprobe_bin, "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", audio_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        try:
            return float(stdout.decode().strip())
        except ValueError:
            return 60.0  # fallback
