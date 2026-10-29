"""
Scene Composer — background rendering + character compositing.
Pure PIL, no ML. Generates rich cartoon-style backgrounds.
"""
import logging
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)


class SceneComposer:
    """Composites character frames onto scene backgrounds."""

    BACKGROUNDS = {
        "classroom": {
            "sky": (200, 220, 255),
            "floor": (180, 160, 120),
            "wall": (240, 230, 200),
            "accents": [(100, 80, 60), (80, 60, 40)],
            "type": "indoor",
        },
        "laboratory": {
            "sky": (180, 210, 200),
            "floor": (160, 170, 165),
            "wall": (200, 215, 210),
            "accents": [(50, 120, 100), (40, 100, 80)],
            "type": "indoor",
        },
        "outdoor": {
            "sky": (100, 160, 240),
            "floor": (80, 140, 60),
            "wall": (120, 180, 100),
            "accents": [(60, 100, 50), (50, 80, 40)],
            "type": "outdoor",
        },
        "studio": {
            "sky": (25, 25, 40),
            "floor": (35, 35, 55),
            "wall": (20, 20, 35),
            "accents": [(60, 60, 90), (40, 40, 70)],
            "type": "studio",
        },
        "dark": {
            "sky": (10, 10, 18),
            "floor": (15, 15, 25),
            "wall": (10, 10, 18),
            "accents": [(30, 30, 50), (20, 20, 35)],
            "type": "studio",
        },
        "bright": {
            "sky": (240, 248, 255),
            "floor": (220, 230, 245),
            "wall": (235, 242, 252),
            "accents": [(200, 210, 230), (180, 195, 220)],
            "type": "studio",
        },
        "night": {
            "sky": (10, 15, 45),
            "floor": (20, 20, 35),
            "wall": (15, 18, 50),
            "accents": [(50, 50, 100), (30, 30, 80)],
            "type": "outdoor",
        },
    }

    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self._bg_cache: dict = {}

    # ─────────────────────────────────────────────────────────────
    def render_background(self, bg_type: str) -> Image.Image:
        """Render a rich PIL background. Cached per type."""
        if bg_type in self._bg_cache:
            return self._bg_cache[bg_type].copy()

        cfg = self.BACKGROUNDS.get(bg_type, self.BACKGROUNDS["studio"])
        bg = self._draw_background(cfg)
        self._bg_cache[bg_type] = bg
        return bg.copy()

    def _draw_background(self, cfg: dict) -> Image.Image:
        W, H = self.width, self.height
        bg = Image.new("RGB", (W, H), cfg["wall"])
        draw = ImageDraw.Draw(bg)
        bg_type = cfg.get("type", "studio")

        if bg_type == "outdoor":
            # Sky gradient (top 60%)
            sky_h = int(H * 0.62)
            sky_c = cfg["sky"]
            horizon_c = tuple(min(255, int(c * 1.25)) for c in sky_c)
            for y in range(sky_h):
                ratio = y / sky_h
                r = int(sky_c[0] * (1 - ratio) + horizon_c[0] * ratio)
                g = int(sky_c[1] * (1 - ratio) + horizon_c[1] * ratio)
                b = int(sky_c[2] * (1 - ratio) + horizon_c[2] * ratio)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Ground gradient (bottom 40%)
            gnd_c = cfg["floor"]
            dark_gnd = tuple(max(0, int(c * 0.6)) for c in gnd_c)
            for y in range(sky_h, H):
                ratio = (y - sky_h) / (H - sky_h)
                r = int(gnd_c[0] * (1 - ratio) + dark_gnd[0] * ratio)
                g = int(gnd_c[1] * (1 - ratio) + dark_gnd[1] * ratio)
                b = int(gnd_c[2] * (1 - ratio) + dark_gnd[2] * ratio)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Sun
            draw.ellipse([(W - 200, 80), (W - 80, 200)], fill=(255, 245, 180))

            # Clouds
            self._draw_clouds(draw, W, sky_h)

            # Horizon line
            draw.line([(0, sky_h), (W, sky_h)], fill=tuple(max(0, c - 20) for c in cfg["floor"]), width=3)

        elif bg_type == "indoor":
            # Wall (top 70%)
            wall_h = int(H * 0.75)
            wall_c = cfg["wall"]
            for y in range(wall_h):
                ratio = y / wall_h
                shade = tuple(max(0, int(c - 15 * ratio)) for c in wall_c)
                draw.line([(0, y), (W, y)], fill=shade)

            # Floor (bottom 30%)
            floor_c = cfg["floor"]
            for y in range(wall_h, H):
                ratio = (y - wall_h) / (H - wall_h)
                shade = tuple(max(0, int(c - 30 * ratio)) for c in floor_c)
                draw.line([(0, y), (W, y)], fill=shade)

            # Baseboard
            draw.rectangle([(0, wall_h - 8), (W, wall_h + 8)],
                          fill=cfg["accents"][0])

            # Classroom: chalkboard
            if "classroom" in str(cfg.get("accents")):
                pass
            self._draw_indoor_props(draw, W, H, wall_h, cfg)

        else:
            # Studio: smooth gradient
            c1 = cfg["wall"]
            c2 = tuple(max(0, int(c * 0.7)) for c in c1)
            for y in range(H):
                ratio = y / H
                r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
                g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
                b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Subtle vignette
            self._draw_vignette(draw, W, H)

        return bg

    def _draw_clouds(self, draw: ImageDraw.Draw, W: int, sky_h: int):
        """Draw 3 simple cartoon clouds."""
        cloud_positions = [(150, 120), (500, 80), (800, 160)]
        for cx, cy in cloud_positions:
            for dx, dy, r in [(-30, 0, 40), (0, -20, 50), (30, 0, 40), (-15, 10, 35), (15, 10, 35)]:
                draw.ellipse([
                    (cx + dx - r, cy + dy - r),
                    (cx + dx + r, cy + dy + r)
                ], fill=(255, 255, 255))

    def _draw_indoor_props(self, draw: ImageDraw.Draw, W: int, H: int, wall_h: int, cfg: dict):
        """Draw simple indoor props."""
        accent = cfg["accents"][0]
        # Window (right side)
        wx, wy = W - 220, 100
        ww, wh = 160, 220
        draw.rectangle([(wx, wy), (wx + ww, wy + wh)], fill=(180, 210, 240))
        draw.rectangle([(wx, wy), (wx + ww, wy + wh)], outline=accent, width=6)
        draw.line([(wx + ww // 2, wy), (wx + ww // 2, wy + wh)], fill=accent, width=4)
        draw.line([(wx, wy + wh // 2), (wx + ww, wy + wh // 2)], fill=accent, width=4)

    def _draw_vignette(self, draw: ImageDraw.Draw, W: int, H: int):
        """Dark corners vignette."""
        for i in range(0, min(W, H) // 3, 8):
            alpha = int(60 * (1 - i / (min(W, H) / 3)))
            r, g, b = 0, 0, 0
            draw.rectangle([i, i, W - i, H - i],
                          outline=(r, g, b), width=8)

    # ─────────────────────────────────────────────────────────────
    def composite_character(
        self,
        bg: Image.Image,
        char_frame: Image.Image,  # RGBA
        shot_type: str = "medium",
        position: str = "center",
        add_shadow: bool = True,
    ) -> Image.Image:
        """Composite RGBA character frame onto background."""
        bg = bg.convert("RGBA")
        bg_w, bg_h = bg.size
        char_w, char_h = char_frame.size

        # Scale factors per shot type
        scale_map = {
            "close_up":   0.90,
            "medium":     0.65,
            "full_body":  0.85,
            "wide":       0.50,
        }
        target_h_ratio = scale_map.get(shot_type, 0.65)
        target_h = int(bg_h * target_h_ratio)
        scale = target_h / max(char_h, 1)
        new_w = int(char_w * scale)
        new_h = int(char_h * scale)

        char_scaled = char_frame.resize((new_w, new_h), Image.LANCZOS)

        # Y position: bottom-anchored (character feet at bottom)
        y = bg_h - new_h
        if shot_type == "close_up":
            # Show only upper portion — shift up so face is visible
            y = int(bg_h * 0.05)

        # X position
        if position == "center":
            x = (bg_w - new_w) // 2
        elif position == "left":
            x = int(bg_w * 0.05)
        elif position == "right":
            x = bg_w - new_w - int(bg_w * 0.05)
        else:
            x = (bg_w - new_w) // 2

        result = bg.copy()

        # Shadow
        if add_shadow and shot_type != "close_up":
            result = self._add_shadow(result, x, y, new_w, new_h)

        # Paste character
        result.alpha_composite(char_scaled, (max(0, x), max(0, y)))

        return result.convert("RGB")

    def _add_shadow(self, bg: Image.Image, x: int, y: int, w: int, h: int) -> Image.Image:
        """Soft elliptical contact shadow under character."""
        shadow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow_layer)

        cx = x + w // 2
        cy = y + h + 10
        rx = int(w * 0.38)
        ry = max(20, int(h * 0.025))

        # Multiple ellipses for soft falloff
        for i in range(4, 0, -1):
            alpha = int(70 * i / 4)
            fx = int(rx * (1 + 0.15 * (4 - i)))
            fy = int(ry * (1 + 0.3 * (4 - i)))
            draw.ellipse([
                (cx - fx, cy - fy),
                (cx + fx, cy + fy),
            ], fill=(0, 0, 0, alpha))

        return Image.alpha_composite(bg, shadow_layer)

    # ─────────────────────────────────────────────────────────────
    def add_ui_overlay(
        self,
        frame: Image.Image,
        channel_name: str = "",
        subtitle_text: str = "",
        font_bold=None,
        font_regular=None,
    ) -> Image.Image:
        """Add channel watermark + subtitle bar to a finished frame."""
        from config import Config
        cfg = Config()

        frame = frame.convert("RGBA")
        draw = ImageDraw.Draw(frame)
        W, H = frame.size

        # Font fallback
        try:
            font_sm = ImageFont.truetype(str(cfg.FONT_BOLD), 36) if font_bold is None else font_bold
            font_sub = ImageFont.truetype(str(cfg.FONT_BOLD), 52) if font_bold is None else font_bold
        except Exception:
            font_sm = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Channel watermark (top-left pill)
        if channel_name:
            wm = f"▶ {channel_name.upper()}"
            bbox = draw.textbbox((0, 0), wm, font=font_sm)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pill = Image.new("RGBA", (tw + 40, th + 20), (12, 14, 20, 210))
            pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([(0, 0), (tw + 40, th + 20)], radius=12, outline=(255, 205, 0, 180), width=2)
            frame.alpha_composite(pill, (50, 80))
            draw = ImageDraw.Draw(frame)
            draw.text((70, 90), wm, font=font_sm, fill=(255, 255, 255, 255))

        # Subtitle bar (bottom)
        if subtitle_text:
            bbox = draw.textbbox((0, 0), subtitle_text, font=font_sub)
            tw = bbox[2] - bbox[0]
            # Dark bar
            bar_h = 110
            bar = Image.new("RGBA", (W, bar_h), (0, 0, 0, 190))
            frame.alpha_composite(bar, (0, H - bar_h - 60))
            draw = ImageDraw.Draw(frame)
            tx = (W - tw) // 2
            ty = H - bar_h - 60 + (bar_h - (bbox[3] - bbox[1])) // 2
            # Shadow
            draw.text((tx + 2, ty + 2), subtitle_text, font=font_sub, fill=(0, 0, 0, 200))
            draw.text((tx, ty), subtitle_text, font=font_sub, fill=(255, 255, 255, 255))

        return frame.convert("RGB")
