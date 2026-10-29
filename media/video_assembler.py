"""
Video Assembler - Combines images + audio + subtitles into viral-ready MP4
Uses Pillow for frame rendering + FFmpeg for final assembly
Output: 1080x1920 (9:16), H.264, ready for Facebook Reels / YouTube Shorts

Visual Style: Voice of Dhaka / Bangla News Channel inspired
- Bold cinematic text
- Channel watermark top-left
- Card-style content sections
- Clean subtitle zone
"""
import asyncio
import logging
import json
import os
import textwrap
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from config import Config

logger = logging.getLogger(__name__)


# ── Colour palette (neutral defaults; overridden per account) ──────────────
GOLD   = (255, 205, 0)
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (220, 30,  30)   # accent for news/breaking style
DARK   = (15,  15,  20)


class VideoAssembler:
    def __init__(self):
        self.config = Config()
        self.W = self.config.VIDEO_WIDTH    # 1080
        self.H = self.config.VIDEO_HEIGHT   # 1920
        self.FPS = self.config.VIDEO_FPS    # 30

        # Font sizes
        self.font_channel  = self._load_font("bold",    40)   # channel watermark
        self.font_hook     = self._load_font("bold",    74)   # hero headline
        self.font_badge    = self._load_font("bold",    42)   # section badge / chapter pill
        self.font_body     = self._load_font("bold",    48)   # body text
        self.font_small    = self._load_font("regular", 36)   # small labels
        self.font_subtitle = self._load_font("bold",    58)   # burned-in subtitles
        self.font_cta_big  = self._load_font("bold",    68)   # CTA headline
        self.font_cta_btn  = self._load_font("bold",    46)   # CTA button text

    # ─────────────────────────────────────────────────────────────────────
    def _load_font(self, style: str, size: int) -> ImageFont.FreeTypeFont:
        font_path = self.config.FONT_BOLD if style == "bold" else self.config.FONT_REGULAR
        try:
            return ImageFont.truetype(str(font_path), size)
        except (IOError, OSError):
            logger.warning("Custom font not found, using default")
            return ImageFont.load_default()

    # ─────────────────────────────────────────────────────────────────────
    # Ken Burns motion types cycled per scene
    _MOTION_CYCLE = ["zoom_in", "pan_right", "zoom_out", "pan_left"]

    async def assemble(
        self,
        script: dict,
        audio_path: str,
        images: list,
        subtitle_segments: list,
        output_path: str,
        account_name: str = "",
        subtitle_style: str = "hormozi_yellow",
        bgm_style: str = "ambient_cinematic",
        is_chapter: bool = False,
        chapter_index: int = 1,
        is_final_chapter: bool = True,
        show_cta: bool = True,
    ) -> str:
        """Main assembly pipeline — dynamic 3.5s micro-clip pacing per scene"""
        self.current_channel_name = account_name or self.config.CHANNEL_NAME
        logger.info(f"Starting video assembly for {self.current_channel_name}...")
        output_file = Path(output_path).resolve()
        temp_dir = output_file.parent / f"temp_{output_file.stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Get audio duration
        audio_file = Path(audio_path).resolve()
        duration = await self._get_audio_duration(str(audio_file))
        logger.info(f"Audio duration: {duration:.1f}s")

        # Build scene timeline with micro-clip beats (3-4s per visual cut)
        scenes = self._build_scenes(
            script=script,
            images=images,
            total_duration=duration,
            is_chapter=is_chapter,
            chapter_index=chapter_index,
            is_final_chapter=is_final_chapter,
            show_cta=show_cta,
        )

        # ── Render overlay PNGs + animated clips ──────────────────────
        clip_paths = []
        for i, scene in enumerate(scenes):
            # 1. Render Pillow overlay (transparent PNG, no background)
            overlay_path = temp_dir / f"overlay_{i:04d}.png"
            self._render_frame(scene, script, i, len(scenes), overlay_path)

            # 2. Build per-scene animated MP4 with Ken Burns / real video background
            motion = self._MOTION_CYCLE[i % len(self._MOTION_CYCLE)]
            clip_path = temp_dir / f"clip_{i:04d}.mp4"
            await self._make_animated_clip(
                bg_image=scene.get("image"),
                overlay_png=str(overlay_path.resolve()),
                output_path=str(clip_path.resolve()),
                duration=scene["duration"],
                motion=motion,
            )
            clip_paths.append(str(clip_path.resolve()))
            logger.info(f"Micro-clip {i+1}/{len(scenes)} ({scene['duration']:.1f}s, {scene['type']})")

        # Write FFmpeg concat file pointing to animated clips
        concat_file = temp_dir / "concat.txt"
        with open(str(concat_file), "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        # Subtitle ASS
        ass_path = None
        if subtitle_segments:
            ass_file = temp_dir / "subtitles.ass"
            self._write_ass_subtitles(subtitle_segments, str(ass_file), subtitle_style)
            ass_path = str(ass_file.resolve())

        # Final assembly: concat animated clips + audio + subtitles
        await self._ffmpeg_assemble(
            concat_file=str(concat_file.resolve()),
            audio_path=str(audio_file),
            ass_path=ass_path,
            output_path=str(output_file),
            duration=duration,
            bgm_style=bgm_style,
        )

        # Cleanup temp dir
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"Cleaned temporary dir: {temp_dir}")
        except Exception as e:
            logger.debug(f"Failed to remove temp dir {temp_dir}: {e}")

        logger.info(f"Video assembled: {output_path}")
        return output_path

    # ─────────────────────────────────────────────────────────────────────
    def _build_scenes(
        self,
        script: dict,
        images: list,
        total_duration: float,
        is_chapter: bool = False,
        chapter_index: int = 1,
        is_final_chapter: bool = True,
        show_cta: bool = True,
    ) -> list:
        """
        Distribute micro-clips across video duration (target 3.0–4.2s per visual cut).
        Prevents static scenes and keeps retention high with frequent visual shifts.
        """
        sections = script.get("sections")
        if not sections:
            if "chapters" in script and isinstance(script["chapters"], list):
                sections = [
                    {"heading": ch.get("title", f"Chapter {ch.get('number', i+1)}"), "script": ch.get("script", "")}
                    for i, ch in enumerate(script["chapters"])
                ]
            elif "story_acts" in script and isinstance(script["story_acts"], list):
                sections = [
                    {"heading": act.get("act", f"Act {i+1}"), "script": act.get("script", "")}
                    for i, act in enumerate(script["story_acts"])
                ]
            elif "scenes" in script and isinstance(script["scenes"], list):
                sections = [
                    {"heading": sc.get("visual") or f"Scene {sc.get('scene', i+1)}", "script": sc.get("dialogue") or sc.get("action", "")}
                    for i, sc in enumerate(script["scenes"])
                ]
            elif "bits" in script and isinstance(script["bits"], list):
                sections = [
                    {"heading": b.get("setup", f"Bit {i+1}"), "script": f"{b.get('setup', '')} - {b.get('punchline', '')}"}
                    for i, b in enumerate(script["bits"])
                ]
            else:
                sections = []

        if not sections:
            sections = [{"heading": script.get("title", "Insight"), "script": script.get("voiceover", "")}]

        TARGET_BEAT = 3.6  # 3.6 seconds per cut for viral retention
        img_cursor = 0
        scenes = []

        if not images:
            images = [None]

        # 1. Opening: Hook card (for reels / ch 1) or Chapter divider (for ch 2+)
        if is_chapter and chapter_index > 1:
            intro_dur = min(2.8, max(2.0, total_duration * 0.08))
            scenes.append({
                "type": "chapter_intro",
                "chapter_num": chapter_index,
                "heading": script.get("title", f"Part {chapter_index}"),
                "image": images[img_cursor % len(images)],
                "duration": round(intro_dur, 2)
            })
            img_cursor += 1
            allocated_lead = intro_dur
        else:
            hook_dur = min(3.8, max(2.5, total_duration * 0.10))
            scenes.append({
                "type": "hook",
                "image": images[img_cursor % len(images)],
                "heading": script.get("title_card", script.get("title", ""))[:50],
                "subtext": script.get("hook", ""),
                "duration": round(hook_dur, 2)
            })
            img_cursor += 1
            allocated_lead = hook_dur

        # 2. Outro / CTA: ONLY for standalone reels or final chapter of long video
        include_cta = show_cta and (not is_chapter or is_final_chapter)
        cta_dur = min(4.2, max(3.0, total_duration * 0.10)) if include_cta else 0.0

        content_dur = total_duration - allocated_lead - cta_dur
        if content_dur < 3.0:
            content_dur = total_duration - allocated_lead
            include_cta = False
            cta_dur = 0.0

        # 3. Content sections: split into 3.2–4.2s micro-clips with alternating visuals
        sec_dur = content_dur / len(sections)
        for s_idx, sec in enumerate(sections, 1):
            n_beats = max(1, round(sec_dur / TARGET_BEAT))
            beat_dur = round(sec_dur / n_beats, 2)
            for b_idx in range(n_beats):
                scenes.append({
                    "type": "content",
                    "image": images[img_cursor % len(images)],
                    "heading": sec.get("heading", ""),
                    "subtext": sec.get("script", ""),
                    "scene_num": s_idx,
                    "total_scenes": len(sections),
                    "is_sub_beat": (b_idx > 0),
                    "duration": beat_dur
                })
                img_cursor += 1

        # 4. Outro / CTA frame
        if include_cta:
            cta_text = script.get("cta") or script.get("outro") or script.get("moral") or script.get("punchline") or "Follow for more"
            scenes.append({
                "type": "cta",
                "image": images[img_cursor % len(images)],
                "heading": cta_text,
                "duration": round(cta_dur, 2)
            })
            img_cursor += 1

        # Balance rounding drift on final scene
        sum_dur = sum(s["duration"] for s in scenes)
        diff = total_duration - sum_dur
        if abs(diff) > 0.02 and scenes:
            scenes[-1]["duration"] = round(scenes[-1]["duration"] + diff, 2)

        return scenes

    # ─────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────
    def _render_frame(self, scene: dict, script: dict, idx: int, total: int, output_path: Path):
        """Render one overlay frame — saves RGBA transparent PNG.
        Background image is NOT composited here; it is handled by FFmpeg Ken Burns.
        Only the UI chrome (watermark, progress bar, chapter pill, hook card, CTA card)
        is drawn on a transparent canvas so it can be overlaid on the animated bg.
        """

        # ── Transparent canvas ────────────────────────────────────────
        bg = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))

        # ── Top gradient strip (subtle protection, semi-transparent) ──
        overlay_strip = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        draw_strip = ImageDraw.Draw(overlay_strip)
        # Top: dark strip for channel pill + progress bar (y: 0 → 220)
        top_h = 220
        for y in range(top_h):
            ratio = y / top_h
            alpha = int(120 * (1.0 - ratio))
            draw_strip.line([(0, y), (self.W, y)], fill=(0, 0, 0, alpha))
        # Bottom: dark strip for subtitle safe zone (y: 1350 → 1920)
        bot_start = 1350
        bot_h = self.H - bot_start
        for y in range(bot_start, self.H):
            ratio = (y - bot_start) / bot_h
            alpha = int(110 * (ratio ** 1.3))
            draw_strip.line([(0, y), (self.W, y)], fill=(0, 0, 0, alpha))
        bg = Image.alpha_composite(bg, overlay_strip)

        draw = ImageDraw.Draw(bg)
        channel_name = getattr(self, "current_channel_name", self.config.CHANNEL_NAME)

        # ══════════════════════════════════════════════════════════════
        #  TOP SAFE ZONE  (y = 90 – 210)
        # ══════════════════════════════════════════════════════════════

        # ── Channel watermark (top-left, y=95) ─────────────────────
        watermark_text = f"▶ {channel_name.upper()}"
        wm_bbox = draw.textbbox((0, 0), watermark_text, font=self.font_channel)
        wm_tw = wm_bbox[2] - wm_bbox[0]
        wm_th = wm_bbox[3] - wm_bbox[1]
        wm_w = wm_tw + 44
        wm_h = wm_th + 24
        wm_x, wm_y = 60, 95
        # Sleek dark glass pill with subtle gold border
        pill_bg = Image.new("RGBA", (wm_w, wm_h), (12, 14, 20, 215))
        p_draw = ImageDraw.Draw(pill_bg)
        p_draw.rounded_rectangle([(0, 0), (wm_w, wm_h)], radius=14, outline=(255, 205, 0, 190), width=2)
        bg.alpha_composite(pill_bg, (wm_x, wm_y))
        draw = ImageDraw.Draw(bg)
        draw.text((wm_x + 22, wm_y + 11), watermark_text, font=self.font_channel, fill=WHITE)

        # ── Step indicator text (top-right, y=95) ─────────────────────
        step_label = f"{idx + 1} / {total}"
        step_bbox  = draw.textbbox((0, 0), step_label, font=self.font_small)
        step_tw = step_bbox[2] - step_bbox[0]
        step_th = step_bbox[3] - step_bbox[1]
        step_w = step_tw + 36
        step_h = step_th + 24
        step_x = self.W - 60 - step_w
        step_pill = Image.new("RGBA", (step_w, step_h), (12, 14, 20, 215))
        s_draw = ImageDraw.Draw(step_pill)
        s_draw.rounded_rectangle([(0, 0), (step_w, step_h)], radius=14, outline=(100, 100, 120, 160), width=1)
        bg.alpha_composite(step_pill, (step_x, wm_y))
        draw = ImageDraw.Draw(bg)
        draw.text((step_x + 18, wm_y + 11), step_label, font=self.font_small, fill=GOLD)

        # ── Progress bar (y=175, sleek) ─────────────────────────────
        bar_y  = 175
        bar_h  = 6
        bar_x0, bar_x1 = 60, self.W - 60
        progress = (idx + 1) / total
        draw.rounded_rectangle(
            [(bar_x0, bar_y), (bar_x1, bar_y + bar_h)],
            radius=3, fill=(50, 50, 60, 200)
        )
        fill_w = int(bar_x0 + (bar_x1 - bar_x0) * progress)
        if fill_w > bar_x0:
            draw.rounded_rectangle(
                [(bar_x0, bar_y), (fill_w, bar_y + bar_h)],
                radius=3, fill=(*GOLD, 240)
            )

        # ══════════════════════════════════════════════════════════════
        #  SCENE OVERLAYS (Hook / Content Chapter Pill / CTA)
        # ══════════════════════════════════════════════════════════════

        if scene["type"] == "hook":
            self._render_hook(draw, bg, scene)

        elif scene["type"] == "chapter_intro":
            self._render_chapter_intro(draw, bg, scene)

        elif scene["type"] == "content":
            self._render_content(draw, bg, scene, script)

        elif scene["type"] == "cta":
            self._render_cta(draw, bg, scene, channel_name)

        # Save as RGBA PNG (transparent overlay — background handled by FFmpeg)
        bg.save(str(output_path), format="PNG")

    # ─────────────────────────────────────────────────────────────────────
    def _render_chapter_intro(self, draw: ImageDraw.Draw, bg: Image.Image, scene: dict):
        """Cinematic chapter divider card for long-form episodes"""
        ch_num = scene.get("chapter_num", 1)
        heading = scene.get("heading", f"CHAPTER {ch_num}").upper()

        box_y1 = 440
        box_h = 240
        card = Image.new("RGBA", (self.W - 120, box_h), (10, 12, 18, 220))
        c_draw = ImageDraw.Draw(card)
        c_draw.rounded_rectangle([(0, 0), (self.W - 120, box_h)], radius=24, outline=(255, 205, 0, 220), width=3)
        bg.alpha_composite(card, (60, box_y1))
        draw = ImageDraw.Draw(bg)

        self._draw_text_centered(
            draw, f"— CHAPTER {ch_num:02d} —",
            y=490,
            font=self.font_badge,
            color=(255, 205, 0),
            shadow=True
        )
        self._draw_text_centered(
            draw, heading[:45],
            y=580,
            font=self.font_badge,
            color=WHITE,
            shadow=True,
            max_width=860
        )



    # ─────────────────────────────────────────────────────────────────────
    def _render_hook(self, draw: ImageDraw.Draw, bg: Image.Image, scene: dict):
        """HOOK frame: viral punchy title badge + bold headline"""
        headline = scene.get("heading", "").upper().strip()

        # Category tag badge at y=235
        tag_text = "• EXCLUSIVE STORY •"
        t_bbox = draw.textbbox((0, 0), tag_text, font=self.font_small)
        tw = t_bbox[2] - t_bbox[0] + 36
        th = t_bbox[3] - t_bbox[1] + 18
        tx = (self.W - tw) // 2
        ty = 230
        tag_img = Image.new("RGBA", (tw, th), (220, 30, 30, 230))
        t_draw = ImageDraw.Draw(tag_img)
        t_draw.rounded_rectangle([(0, 0), (tw, th)], radius=12, outline=(255, 255, 255, 220), width=2)
        bg.alpha_composite(tag_img, (tx, ty))
        draw = ImageDraw.Draw(bg)
        draw.text((tx + 18, ty + 7), tag_text, font=self.font_small, fill=WHITE)

        # Main headline with floating glass backdrop pill (y=305)
        lines = self._wrap_text(headline, self.font_hook, max_width=880)
        line_height = self.font_hook.size + 14
        total_h = len(lines) * line_height
        box_pad_y = 25
        box_y1 = 305
        box_y2 = box_y1 + total_h + box_pad_y * 2
        box_h = box_y2 - box_y1

        # Draw sleek floating dark glass card for the title
        card = Image.new("RGBA", (self.W - 100, box_h), (10, 12, 18, 215))
        c_draw = ImageDraw.Draw(card)
        c_draw.rounded_rectangle([(0, 0), (self.W - 100, box_h)], radius=22, outline=(255, 205, 0, 220), width=3)
        bg.alpha_composite(card, (50, box_y1))
        draw = ImageDraw.Draw(bg)

        # Draw headline text centered inside the card
        for i, line in enumerate(lines):
            ly = box_y1 + box_pad_y + i * line_height
            bbox = draw.textbbox((0, 0), line, font=self.font_hook)
            lw = bbox[2] - bbox[0]
            lx = (self.W - lw) // 2
            draw.text((lx + 3, ly + 3), line, font=self.font_hook, fill=(0, 0, 0))
            draw.text((lx, ly), line, font=self.font_hook, fill=WHITE)

    # ─────────────────────────────────────────────────────────────────────
    def _render_content(self, draw: ImageDraw.Draw, bg: Image.Image, scene: dict, script: dict):
        """CONTENT frame: sleek floating glass chapter pill at top, keeping visual 100% clear!"""
        scene_num   = scene.get("scene_num", 1)
        total_scenes = scene.get("total_scenes", 1)
        heading     = scene.get("heading", "").strip().upper()

        if not heading:
            heading = f"CHAPTER {scene_num}"

        # Clean short heading (max 42 chars)
        if len(heading) > 42:
            heading = heading[:39] + "..."

        pill_text = f"  PART {scene_num:02d} • {heading}  "
        p_bbox = draw.textbbox((0, 0), pill_text, font=self.font_badge)
        pw = min(self.W - 80, p_bbox[2] - p_bbox[0] + 48)
        ph = p_bbox[3] - p_bbox[1] + 24
        px = max(40, (self.W - pw) // 2)
        py = 230

        # Floating dark frosted glass pill with gold accent outline
        pill_img = Image.new("RGBA", (pw, ph), (12, 14, 22, 215))
        p_draw = ImageDraw.Draw(pill_img)
        p_draw.rounded_rectangle([(0, 0), (pw, ph)], radius=18, outline=(255, 205, 0, 220), width=2)
        bg.alpha_composite(pill_img, (px, py))
        draw = ImageDraw.Draw(bg)

        # Draw the chapter text inside the pill
        self._draw_text_centered(
            draw, pill_text,
            y=py + ph // 2,
            font=self.font_badge,
            color=WHITE,
            shadow=True,
            shadow_offset=2,
            max_width=pw - 20
        )
        # Note: Center visual (y: 310 - 1340) is 100% CLEAR so AI visual is completely visible!
        # Kinetic subtitles render at y: 1340 via ASS subtitles.

    # ─────────────────────────────────────────────────────────────────────
    def _render_cta(self, draw: ImageDraw.Draw, bg: Image.Image, scene: dict, channel_name: str):
        """CTA frame: sleek outro badge + follow button"""
        cta_text = scene.get("heading") or "Follow for more daily stories!"
        if len(cta_text) > 80:
            cta_text = cta_text[:77] + "..."

        # Outro glass container card
        box_y1 = 480
        box_y2 = 890
        box_h = box_y2 - box_y1
        card = Image.new("RGBA", (self.W - 120, box_h), (12, 14, 22, 220))
        c_draw = ImageDraw.Draw(card)
        c_draw.rounded_rectangle([(0, 0), (self.W - 120, box_h)], radius=28, outline=(255, 205, 0, 220), width=3)
        bg.alpha_composite(card, (60, box_y1))
        draw = ImageDraw.Draw(bg)

        # Headline
        self._draw_text_centered(
            draw, "ENJOYED THIS STORY?",
            y=550,
            font=self.font_badge,
            color=(255, 205, 0),
            shadow=True
        )

        # CTA dynamic text
        self._draw_text_centered(
            draw, cta_text,
            y=640,
            font=self.font_small,
            color=WHITE,
            shadow=True,
            max_width=860
        )

        # Follow button pill
        btn_w = 640
        btn_h = 86
        btn_x = (self.W - btn_w) // 2
        btn_y = 750
        draw.rounded_rectangle(
            [(btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h)],
            radius=43,
            fill=(220, 30, 30)
        )
        self._draw_text_centered(
            draw, f"FOLLOW @{channel_name.upper()}",
            y=btn_y + btn_h // 2,
            font=self.font_cta_btn,
            color=WHITE,
            shadow=True,
            shadow_offset=2
        )


    # ─────────────────────────────────────────────────────────────────────
    def _draw_text_centered(
        self, draw, text: str, y: int, font,
        color, shadow=False,
        shadow_color=(0, 0, 0), shadow_offset=3,
        max_width=900
    ):
        """Draw horizontally centered text with optional shadow + word wrap"""
        lines       = self._wrap_text(text, font, max_width)
        line_height = font.size + 14
        total_h     = len(lines) * line_height
        start_y     = y - total_h // 2

        for i, line in enumerate(lines):
            line_y = start_y + i * line_height
            bbox   = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x      = (self.W - text_w) // 2

            if shadow:
                off = shadow_offset
                draw.text((x + off, line_y + off), line, font=font, fill=shadow_color)
            draw.text((x, line_y), line, font=font, fill=color)

    def _draw_text_at(
        self, draw, text: str, x: int, y: int, font,
        color, shadow=False, max_width=900
    ):
        """Draw left-aligned text at (x, y) with optional shadow + word wrap"""
        lines       = self._wrap_text(text, font, max_width)
        line_height = font.size + 14

        for i, line in enumerate(lines):
            line_y = y + i * line_height
            if shadow:
                draw.text((x + 3, line_y + 3), line, font=font, fill=(0, 0, 0))
            draw.text((x, line_y), line, font=font, fill=color)

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """Word wrap text to fit max_width pixels"""
        words        = text.split()
        lines        = []
        current_line = []
        _draw        = ImageDraw.Draw(Image.new("RGB", (1, 1)))

        for word in words:
            test = " ".join(current_line + [word])
            bbox = _draw.textbbox((0, 0), test, font=font)
            if bbox[2] > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    # ─────────────────────────────────────────────────────────────────────
    def _write_ass_subtitles(
        self, segments: list, output_path: str, subtitle_style: str = "hormozi_yellow"
    ):
        """Write ASS subtitle file using style from SUBTITLE_STYLES registry"""
        from config import SUBTITLE_STYLES
        st = SUBTITLE_STYLES.get(subtitle_style, SUBTITLE_STYLES["hormozi_yellow"])

        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{st['fontname']},{st['fontsize']},{st['primary']},&H000000FF,{st['outline']},{st['back']},{st['bold']},0,0,0,100,100,1,0,{st['border_style']},{st['outline_px']},{st['shadow_px']},{st['alignment']},80,150,{st['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        lines = [ass_header]
        for seg in segments:
            start = self._seconds_to_ass(seg["start"])
            end   = self._seconds_to_ass(seg["end"])
            text  = seg["text"].replace("\n", "\\N")
            # Highlight marker if style has one (e.g. hormozi yellow word highlight)
            if st.get("marker") and " " in text:
                words = text.split()
                marker = st["marker"]
                if not marker.startswith("{"):
                    marker = f"{{{marker}}}"
                words[0] = f"{marker}{words[0]}{{\\r}}"
                text = " ".join(words)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _seconds_to_ass(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    # ─────────────────────────────────────────────────────────────────────
    async def _make_animated_clip(
        self,
        bg_image: str | None,
        overlay_png: str,
        output_path: str,
        duration: float,
        motion: str = "zoom_in",
    ):
        """Create a short animated MP4 clip for one scene using Ken Burns zoompan.

        Steps:
          1. Apply zoompan (Ken Burns) on the background image → animated video
          2. Composite the transparent overlay PNG on top
          3. Output: scene clip MP4 (no audio, will be concat'd later)

        motion options: zoom_in | zoom_out | pan_right | pan_left
        """
        import shutil as _shutil
        ffmpeg_bin = _shutil.which("ffmpeg") or "ffmpeg"

        W, H = self.W, self.H
        fps = self.FPS
        frames = max(int(duration * fps), 1)

        # ── Ken Burns zoompan expression per motion type ──────────────
        if motion == "zoom_in":
            zoom_expr  = "min(zoom+0.0015,1.25)"
            x_expr     = "iw/2-(iw/zoom/2)"
            y_expr     = "ih/2-(ih/zoom/2)"
        elif motion == "zoom_out":
            zoom_expr  = "max(zoom-0.0015,1.0)"
            x_expr     = "iw/2-(iw/zoom/2)"
            y_expr     = "ih/2-(ih/zoom/2)"
        elif motion == "pan_right":
            zoom_expr  = "1.08"
            x_expr     = f"(iw/zoom/2)*((on-1)/{max(frames-1,1)})"
            y_expr     = "ih/2-(ih/zoom/2)"
        elif motion == "pan_left":
            zoom_expr  = "1.08"
            x_expr     = f"iw/zoom - (iw/zoom/2)*((on-1)/{max(frames-1,1)})"
            y_expr     = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr  = "min(zoom+0.0015,1.25)"
            x_expr     = "iw/2-(iw/zoom/2)"
            y_expr     = "ih/2-(ih/zoom/2)"

        zoompan_filter = (
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
            f":d={frames}:s={W}x{H}:fps={fps}"
        )

        has_bg = bg_image and Path(bg_image).exists()
        is_video = has_bg and Path(bg_image).suffix.lower() in [".mp4", ".mov", ".mkv", ".webm"]

        if is_video:
            # ── Real HD Video Background (Pixabay / Stock Video) ───────
            # Scale & crop to 1080x1920 vertical, enhance contrast, add subtle vignette, overlay UI
            filter_complex = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},"
                f"eq=saturation=1.10:contrast=1.05,"
                f"vignette=PI/6[bg];"
                f"[bg][1:v]overlay=0:0[vout]"
            )
            cmd = [
                ffmpeg_bin, "-y",
                "-stream_loop", "-1", "-i", bg_image,
                "-i", overlay_png,
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "22",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                output_path,
            ]
        elif has_bg:
            # ── Animated background + overlay composite ────────────────
            # Filter graph:
            #   [0:v] scale → enhance color/contrast → zoompan → vignette → [bg]
            #   [bg][1:v] overlay → [vout]
            filter_complex = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},"
                f"eq=saturation=1.10:contrast=1.05,"
                f"{zoompan_filter},"
                f"vignette=PI/6[bg];"
                f"[bg][1:v]overlay=0:0:shortest=1[vout]"
            )
            cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-i", bg_image,
                "-i", overlay_png,
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "24",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                output_path,
            ]
        else:
            # ── No background image: dark gradient + overlay ───────────
            # Use FFmpeg lavfi color source as background
            filter_complex = (
                f"color=c=0x0f1219:size={W}x{H}:rate={fps}[bg];"
                f"[bg][0:v]overlay=0:0:shortest=1[vout]"
            )
            cmd = [
                ffmpeg_bin, "-y",
                "-i", overlay_png,
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "24",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                output_path,
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode()
            logger.error(f"Ken Burns clip failed ({motion}): {err[-400:]}")
            raise Exception(f"Animated clip error: {err[-200:]}")

    # ─────────────────────────────────────────────────────────────────────
    async def _get_audio_duration(self, audio_path: str) -> float:
        import shutil
        ffprobe_bin = shutil.which("ffprobe") or "ffprobe"
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
            return 55.0

    # ─────────────────────────────────────────────────────────────────────
    async def _ffmpeg_assemble(
        self,
        concat_file: str,
        audio_path: str,
        ass_path: str | None,
        output_path: str,
        duration: float,
        bgm_style: str = "ambient_cinematic",
    ):
        """Final FFmpeg command: burns subtitles + synthesizes BGM + mixes audio"""
        import shutil
        from config import BGM_STYLES
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"

        # ── Synthesize BGM via FFmpeg lavfi ──────────────────────────────
        bgm_info   = BGM_STYLES.get(bgm_style, BGM_STYLES["ambient_cinematic"])
        freqs      = bgm_info["freqs"]
        bgm_temp   = Path(output_path).parent / f"bgm_{bgm_style}.mp3"
        bgm_exists = bgm_temp.exists()

        # Check if custom BGM file is available in assets/audio/
        custom_bgm = self.config.ASSETS_DIR / "audio" / f"{bgm_style}.mp3"
        if not custom_bgm.exists():
            custom_bgm = self.config.ASSETS_DIR / "audio" / "bgm_cinematic.mp3"

        if custom_bgm.exists():
            bgm_source = str(custom_bgm)
            use_synth  = False
        elif not bgm_exists:
            # Synthesize harmonic chord BGM via lavfi
            sine_inputs = "".join(
                f"sine=frequency={f}:sample_rate=44100:duration={int(duration)+5},"
                f"volume=0.22[s{i}];"
                for i, f in enumerate(freqs)
            )
            amix_inputs = "".join(f"[s{i}]" for i in range(len(freqs)))
            lavfi_filter = (
                f"{sine_inputs}"
                f"{amix_inputs}amix=inputs={len(freqs)}:duration=longest[bgm_out]"
            )
            synth_cmd = [
                ffmpeg_bin, "-y",
                "-filter_complex", lavfi_filter,
                "-map", "[bgm_out]",
                "-c:a", "libmp3lame", "-b:a", "128k",
                str(bgm_temp)
            ]
            proc_bgm = await asyncio.create_subprocess_exec(
                *synth_cmd,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc_bgm.communicate()
            bgm_source = str(bgm_temp) if bgm_temp.exists() else None
            use_synth  = True
        else:
            bgm_source = str(bgm_temp)
            use_synth  = True

        # ── Build main FFmpeg command ─────────────────────────────────────
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-i", audio_path,
        ]

        filters = []
        maps    = []

        # Video: burn ASS subtitles (clips already at correct fps/timebase)
        if ass_path and Path(ass_path).exists():
            ass_escaped = ass_path.replace("\\", "/").replace(":", "\\:")
            filters.append(f"[0:v]ass={ass_escaped}[vout]")
            maps.extend(["-map", "[vout]"])
        else:
            maps.extend(["-map", "0:v"])

        # Audio: voice + BGM mix
        if bgm_source and Path(bgm_source).exists():
            cmd.extend(["-stream_loop", "-1", "-i", bgm_source])
            filters.append(
                "[1:a]volume=1.0[voice];"
                "[2:a]volume=0.10[bgm];"
                "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            maps.extend(["-map", "[aout]"])
        else:
            maps.extend(["-map", "1:a"])

        if filters:
            cmd.extend(["-filter_complex", ";".join(filters)])
        cmd.extend(maps)

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-t", str(duration + 0.5),
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            output_path
        ])

        logger.info(f"Running FFmpeg (BGM: {bgm_style})...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode()
            logger.error(f"FFmpeg failed: {err[-500:]}")
            raise Exception(f"FFmpeg error: {err[-200:]}")

        size_mb = Path(output_path).stat().st_size / 1024 / 1024
        logger.info(f"Video ready: {output_path} ({size_mb:.1f} MB)")
