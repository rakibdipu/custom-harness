"""
Fast Cartoon Animator v2 — State-Based, No Frame Loop

Instead of generating hundreds of individual frames via PIL,
this generates only a handful of STATE images (mouth open/closed/blink etc.)
then uses FFmpeg concat demuxer to switch between them at exact timing.

For a 30s video: instead of 900 PNG frames → 7-8 state images + FFmpeg concat.
~10× faster on CPU.
"""
import asyncio
import logging
import math
import struct
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Mouth state definitions: (half_width_ratio, half_height_ratio)
# relative to the detected mouth region width
MOUTH_STATES = {
    "closed":        (0,    0),
    "slightly_open": (0.55, 0.25),
    "open":          (0.70, 0.45),
    "wide_open":     (0.85, 0.65),
    "round":         (0.45, 0.45),
}

# Viseme cycle used during speech (cycles through ~7fps equivalent)
VISEME_CYCLE = [
    "slightly_open", "open", "slightly_open", "round",
    "open", "wide_open", "slightly_open", "open",
    "closed", "slightly_open",
]

BLINK_INTERVAL = 3.8   # seconds between auto-blinks
BLINK_DURATION = 0.12  # seconds blink lasts


class FastCartoonAnimator:
    """
    Generates avatar animation via state-image switching — no PIL frame loop.

    Pipeline:
      1. Pre-render N state frames (e.g., mouth_closed, mouth_open, blink, etc.)
      2. Compute per-frame state assignments from audio timing
      3. Write FFmpeg concat file with exact durations for each state
      4. FFmpeg concat → final video
    """

    def __init__(self):
        import shutil
        self._ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

    # ─────────────────────────────────────────────────────────────
    async def create_talking_clip(
        self,
        character_png: str,
        character_profile: dict,
        audio_path: str,
        emotion: str = "neutral",
        gesture: str = "idle",
        duration: float = 10.0,
        output_path: str = "output.mp4",
        background_img: Image.Image = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> str:
        """Generate animated avatar video using state-switching approach."""
        temp_dir = Path(output_path).parent / f"states_{Path(output_path).stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load character
        char = Image.open(character_png).convert("RGBA")

        # 2. Prepare background canvas
        if background_img is not None:
            bg = background_img.convert("RGB").resize((width, height), Image.LANCZOS)
        else:
            bg = Image.new("RGB", (width, height), (25, 25, 40))

        # 3. Scale character to fit canvas
        regions = character_profile.get("regions", {})
        char_scaled, char_x, char_y = self._fit_character(char, width, height)

        # 4. Apply emotion tint
        char_scaled = self._apply_emotion(char_scaled, emotion)

        # 5. Pre-render state images
        logger.info("Pre-rendering state frames...")
        state_paths = self._prerender_states(
            bg=bg,
            char=char_scaled,
            char_x=char_x,
            char_y=char_y,
            regions=regions,
            char_w=char_scaled.width,
            char_h=char_scaled.height,
            temp_dir=temp_dir,
            width=width,
            height=height,
        )
        logger.info(f"  {len(state_paths)} state frames rendered")

        # 6. Estimate speech timing
        timing = self._estimate_speech_timing(audio_path, duration)

        # 7. Compute state assignments per frame
        assignments = self._assign_states(timing, duration, fps, state_paths)

        # 8. Compress consecutive identical states into segments
        segments = self._compress_to_segments(assignments, fps)
        logger.info(f"  {len(segments)} segments (from {int(duration*fps)} frames)")

        # 9. Write FFmpeg concat file
        concat_path = temp_dir / "concat.txt"
        self._write_concat(segments, concat_path)

        # 10. FFmpeg: concat → H.264 + audio
        logger.info(f"Assembling video with FFmpeg...")
        await self._assemble(concat_path, audio_path, output_path, duration)

        # Cleanup
        import shutil as _sh
        _sh.rmtree(temp_dir, ignore_errors=True)

        return output_path

    # ─────────────────────────────────────────────────────────────
    def _fit_character(self, char: Image.Image, canvas_w: int, canvas_h: int):
        """Scale character to 70% of canvas height, center-bottom anchor."""
        target_h = int(canvas_h * 0.72)
        scale = target_h / max(char.height, 1)
        new_w = int(char.width * scale)
        new_h = int(char.height * scale)
        char_s = char.resize((new_w, new_h), Image.LANCZOS)
        x = (canvas_w - new_w) // 2
        y = canvas_h - new_h
        return char_s, x, y

    def _apply_emotion(self, char: Image.Image, emotion: str) -> Image.Image:
        """Subtle brightness/saturation for emotion."""
        presets = {
            "happy":     (1.06, 1.12),
            "sad":       (0.88, 0.80),
            "excited":   (1.10, 1.18),
            "surprised": (1.08, 1.05),
            "angry":     (0.93, 1.08),
            "neutral":   (1.00, 1.00),
        }
        br, sat = presets.get(emotion, (1.0, 1.0))
        r = char.copy()
        if abs(br - 1.0) > 0.01:
            r = ImageEnhance.Brightness(r).enhance(br)
        if abs(sat - 1.0) > 0.01:
            bands = r.split()
            if len(bands) == 4:
                rgb = Image.merge("RGB", bands[:3])
                rgb = ImageEnhance.Color(rgb).enhance(sat)
                r = Image.merge("RGBA", (*rgb.split(), bands[3]))
        return r

    # ─────────────────────────────────────────────────────────────
    def _prerender_states(
        self,
        bg: Image.Image,
        char: Image.Image,
        char_x: int,
        char_y: int,
        regions: dict,
        char_w: int,
        char_h: int,
        temp_dir: Path,
        width: int,
        height: int,
    ) -> dict:
        """
        Pre-render state images. Returns dict: state_name → file_path.

        States rendered:
          - closed, slightly_open, open, wide_open, round  (mouth states)
          - blink                                           (eyes closed)
          - breathe_in, breathe_out                        (subtle scale shift)
        """
        states = {}

        # Compute mouth/eye regions in SCALED character coordinates
        m = regions.get("mouth", {})
        mouth_cx = int(m.get("cx", 0.50) * char_w)
        mouth_cy = int(m.get("cy", 0.70) * char_h)
        mouth_w  = int(m.get("w",  0.18) * char_w)
        mouth_h  = int(m.get("h",  0.06) * char_h)

        e = regions.get("eyes", {})
        eye_cy     = int(e.get("cy", 0.35) * char_h)
        eye_cx_l   = int(e.get("cx_left",  0.35) * char_w)
        eye_cx_r   = int(e.get("cx_right", 0.65) * char_w)
        eye_r      = max(4, int(e.get("radius", 0.05) * char_w))

        def composite(char_variant: Image.Image, name: str) -> str:
            """Composite char_variant onto bg, return path."""
            canvas = bg.copy().convert("RGBA")
            # Subtle shadow
            sh = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            sh_d = ImageDraw.Draw(sh)
            cx = char_x + char_w // 2
            cy = char_y + char_h + 8
            for i in range(3, 0, -1):
                a = 55 * i // 3
                rx = int(char_w * 0.32 * (1 + 0.1 * (3-i)))
                ry = max(15, int(char_h * 0.018 * (1 + 0.2 * (3-i))))
                sh_d.ellipse([(cx-rx, cy-ry), (cx+rx, cy+ry)], fill=(0, 0, 0, a))
            canvas.alpha_composite(sh, (0, 0))
            canvas.alpha_composite(char_variant, (max(0, char_x), max(0, char_y)))
            path = str(temp_dir / f"state_{name}.jpg")
            canvas.convert("RGB").save(path, "JPEG", quality=88)
            return path

        # ── Mouth states ──────────────────────────────────────────
        for state_name, (mwr, mhr) in MOUTH_STATES.items():
            c = char.copy()
            draw = ImageDraw.Draw(c)
            if mwr > 0:
                mw = max(3, int(mouth_w * mwr))
                mh = max(2, int(mouth_h * mhr))
                # Dark interior
                draw.ellipse([
                    mouth_cx - mw, mouth_cy - mh,
                    mouth_cx + mw, mouth_cy + mh,
                ], fill=(30, 15, 15, 235))
                # Lip edge
                if mh > 3:
                    draw.ellipse([
                        mouth_cx - mw - 2, mouth_cy - mh - 2,
                        mouth_cx + mw + 2, mouth_cy + mh + 2,
                    ], outline=(70, 40, 40, 180), width=2)
            else:
                # Closed: thin line
                draw.line([
                    (mouth_cx - int(mouth_w * 0.75), mouth_cy),
                    (mouth_cx + int(mouth_w * 0.75), mouth_cy),
                ], fill=(55, 30, 30, 160), width=2)

            states[state_name] = composite(c, state_name)

        # ── Blink state ───────────────────────────────────────────
        c = char.copy()
        draw = ImageDraw.Draw(c)
        lid_h = max(3, int(eye_r * 1.8))
        for ecx in [eye_cx_l, eye_cx_r]:
            draw.rectangle([
                ecx - eye_r, eye_cy - eye_r,
                ecx + eye_r, eye_cy - eye_r + lid_h,
            ], fill=(28, 20, 15, 240))
        states["blink"] = composite(c, "blink")

        # ── Breathe variants (±0.8% scale, minimal difference) ───
        for scale_delta, vname in [(-0.008, "breathe_out"), (0.008, "breathe_in")]:
            scale = 1.0 + scale_delta
            nw = max(1, int(char_w * scale))
            nh = max(1, int(char_h * scale))
            c = char.resize((nw, nh), Image.NEAREST)
            # Center on original canvas
            tmp = Image.new("RGBA", (char_w, char_h), (0, 0, 0, 0))
            ox = (char_w - nw) // 2
            oy = (char_h - nh) // 2
            tmp.alpha_composite(c, (ox, oy))
            states[vname] = composite(tmp, vname)

        return states

    # ─────────────────────────────────────────────────────────────
    def _estimate_speech_timing(self, audio_path: str, duration: float) -> list:
        """Return list of (time, is_speaking) at 10fps resolution."""
        result = []
        step = 0.1  # 10fps resolution — enough for speech detection

        try:
            p = Path(audio_path)
            if p.suffix.lower() == ".wav":
                with wave.open(audio_path, "rb") as wf:
                    sr = wf.getframerate()
                    nc = wf.getnchannels()
                    sw = wf.getsampwidth()
                    chunk = max(1, int(sr * step))
                    t = 0.0
                    while t < duration:
                        raw = wf.readframes(chunk)
                        if not raw:
                            break
                        if sw == 2:
                            samples = struct.unpack(f"<{len(raw)//2}h", raw)
                        else:
                            samples = struct.unpack(f"<{len(raw)}b", raw)
                        if nc > 1:
                            samples = samples[::nc]
                        rms = math.sqrt(sum(s*s for s in samples) / max(len(samples), 1))
                        result.append((t, rms > 350))
                        t += step
            else:
                # MP3/AAC — approximate: 85% speaking with natural-ish pauses
                t = 0.0
                while t < duration:
                    # Pause at sentence boundaries (~every 4-6s)
                    is_spk = not (0.3 < (t % 5.2) < 0.7)
                    result.append((t, is_spk))
                    t += step
        except Exception as e:
            logger.warning(f"Timing fallback: {e}")
            t = 0.0
            while t < duration:
                result.append((t, True))
                t += step

        return result

    # ─────────────────────────────────────────────────────────────
    def _assign_states(
        self,
        timing: list,
        duration: float,
        fps: int,
        state_paths: dict,
    ) -> list:
        """
        Assign a state_path to each frame index.

        Rules:
        - Blink every BLINK_INTERVAL seconds for BLINK_DURATION
        - If speaking → cycle VISEME_CYCLE at ~6fps
        - If silent → alternate breathe_in/breathe_out at 0.5Hz
        - Not speaking + not blinking → closed mouth
        """
        total = int(duration * fps)
        # Build timing lookup at frame resolution
        timing_at = {}
        for t, is_spk in timing:
            frame = int(t * fps)
            for f in range(frame, min(frame + int(0.1 * fps) + 1, total)):
                timing_at[f] = is_spk

        assignments = []
        blink_frames = int(BLINK_DURATION * fps)
        blink_every  = int(BLINK_INTERVAL * fps)
        viseme_rate  = max(1, fps // 6)  # change viseme every ~6fps

        for i in range(total):
            t = i / fps

            # Blink check
            if i % blink_every < blink_frames:
                assignments.append(state_paths.get("blink", state_paths["closed"]))
                continue

            is_spk = timing_at.get(i, False)

            if is_spk:
                # Viseme cycling
                vix = (i // viseme_rate) % len(VISEME_CYCLE)
                state = VISEME_CYCLE[vix]
                assignments.append(state_paths.get(state, state_paths["slightly_open"]))
            else:
                # Idle breathing
                breathe = "breathe_in" if (i // (fps // 2)) % 2 == 0 else "breathe_out"
                assignments.append(state_paths.get(breathe, state_paths["closed"]))

        return assignments

    # ─────────────────────────────────────────────────────────────
    def _compress_to_segments(self, assignments: list, fps: int) -> list:
        """
        Merge consecutive identical state paths into (path, duration) segments.
        This drastically reduces the concat file size.
        """
        if not assignments:
            return []

        segments = []
        current = assignments[0]
        count = 1
        frame_dur = 1.0 / fps

        for i in range(1, len(assignments)):
            if assignments[i] == current:
                count += 1
            else:
                segments.append((current, round(count * frame_dur, 4)))
                current = assignments[i]
                count = 1

        segments.append((current, round(count * frame_dur, 4)))
        return segments

    # ─────────────────────────────────────────────────────────────
    def _write_concat(self, segments: list, concat_path: Path):
        """Write FFmpeg concat file with absolute paths."""
        lines = []
        for path, dur in segments:
            abs_path = str(Path(path).resolve())
            lines.append(f"file '{abs_path}'")
            lines.append(f"duration {dur}")
        # Last file repeated (FFmpeg concat requirement)
        if segments:
            abs_last = str(Path(segments[-1][0]).resolve())
            lines.append(f"file '{abs_last}'")
        with open(concat_path, "w") as f:
            f.write("\n".join(lines))

    # ─────────────────────────────────────────────────────────────
    async def _assemble(
        self,
        concat_path: Path,
        audio_path: str,
        output_path: str,
        duration: float,
    ):
        """FFmpeg concat demuxer → H.264 + AAC MP4."""
        cmd = [
            self._ffmpeg, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_path),
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(duration + 0.3),
            "-movflags", "+faststart",
            output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"FFmpeg concat failed: {stderr.decode()[-400:]}")

        size = Path(output_path).stat().st_size / 1024 / 1024
        logger.info(f"Video ready: {output_path} ({size:.1f} MB)")
