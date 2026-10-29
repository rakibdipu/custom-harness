"""
Character Engine — PIL-only character preparation.
No ML, no GPU required. Uses geometric heuristics.
"""
import json
import logging
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)


class CharacterEngine:
    """Prepares a character image for consistent animation.
    
    Output structure:
        project_dir/character/
            original_reference.png  ← immutable copy
            character.png           ← RGBA, bg removed
            character_mask.png      ← alpha mask
            identity.json           ← profile
    """

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.character_dir = self.project_dir / "character"
        self.character_dir.mkdir(parents=True, exist_ok=True)
        self.profile: dict = {}

    # ─────────────────────────────────────────────────────────────
    async def load_character(self, image_path: str) -> dict:
        """Async wrapper — calls prepare_character."""
        return self.prepare_character(image_path)

    # ─────────────────────────────────────────────────────────────
    def prepare_character(self, image_path: str) -> dict:
        """Full preparation pipeline. Returns identity profile dict."""
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Character image not found: {img_path}")

        logger.info(f"Preparing character from: {img_path}")

        # 1. Load original (convert to RGB first to handle weird modes)
        orig = Image.open(img_path).convert("RGBA")
        w, h = orig.size
        logger.info(f"Original size: {w}×{h}")

        # 2. Save immutable reference
        orig_ref = self.character_dir / "original_reference.png"
        orig.save(orig_ref)

        # 3. Background removal (PIL only)
        char_rgba = self._remove_background(orig)

        # 4. Save processed character
        char_path = self.character_dir / "character.png"
        char_rgba.save(char_path, "PNG")

        # 5. Alpha mask
        alpha = char_rgba.split()[3]
        mask_path = self.character_dir / "character_mask.png"
        alpha.save(mask_path)

        # 6. Build profile
        body_type = self._detect_body_type(w, h)
        colors = self._analyze_colors(orig)
        regions = self._estimate_regions(w, h, body_type)

        self.profile = {
            "character_id": f"char_{img_path.stem[:8]}",
            "source_image": str(img_path),
            "body_type": body_type,
            "width": w,
            "height": h,
            "aspect_ratio": round(h / w, 3),
            "dominant_colors": [list(c) for c in colors],
            "regions": regions,
            "primary_reference": str(orig_ref),
            "processed": str(char_path),
            "mask": str(mask_path),
            "animation_level": 3,  # PIL + FFmpeg animation
        }

        profile_path = self.character_dir / "identity.json"
        with open(profile_path, "w") as f:
            json.dump(self.profile, f, indent=2)

        logger.info(f"Character prepared: {body_type}, regions: {list(regions.keys())}")
        return self.profile

    def get_profile(self) -> dict:
        return self.profile

    def load_profile(self) -> dict:
        """Load existing profile from disk."""
        p = self.character_dir / "identity.json"
        if p.exists():
            with open(p) as f:
                self.profile = json.load(f)
        return self.profile

    # ─────────────────────────────────────────────────────────────
    def _detect_body_type(self, w: int, h: int) -> str:
        """Aspect ratio heuristic."""
        ratio = h / max(w, 1)
        if ratio < 1.1:
            return "portrait"
        elif ratio < 1.7:
            return "half_body"
        else:
            return "full_body"

    def _estimate_regions(self, w: int, h: int, body_type: str) -> dict:
        """Return pixel regions for face/mouth/eyes as fractions of image size.
        These are heuristic—no ML needed."""
        if body_type == "portrait":
            # Whole image is face/head
            face = {"top": 0.05, "bottom": 0.85, "left": 0.10, "right": 0.90}
            eyes = {"cy": 0.38, "cx_left": 0.34, "cx_right": 0.66, "radius": 0.06}
            mouth = {"cy": 0.72, "cx": 0.50, "w": 0.18, "h": 0.06}
            eyebrow_left  = {"cx": 0.33, "cy": 0.28}
            eyebrow_right = {"cx": 0.67, "cy": 0.28}
        elif body_type == "half_body":
            face = {"top": 0.02, "bottom": 0.38, "left": 0.20, "right": 0.80}
            eyes = {"cy": 0.14, "cx_left": 0.36, "cx_right": 0.64, "radius": 0.04}
            mouth = {"cy": 0.28, "cx": 0.50, "w": 0.12, "h": 0.04}
            eyebrow_left  = {"cx": 0.36, "cy": 0.10}
            eyebrow_right = {"cx": 0.64, "cy": 0.10}
        else:
            # full_body
            face = {"top": 0.02, "bottom": 0.22, "left": 0.25, "right": 0.75}
            eyes = {"cy": 0.09, "cx_left": 0.38, "cx_right": 0.62, "radius": 0.025}
            mouth = {"cy": 0.17, "cx": 0.50, "w": 0.08, "h": 0.025}
            eyebrow_left  = {"cx": 0.38, "cy": 0.07}
            eyebrow_right = {"cx": 0.62, "cy": 0.07}

        return {
            "face": face,
            "eyes": eyes,
            "mouth": mouth,
            "eyebrow_left": eyebrow_left,
            "eyebrow_right": eyebrow_right,
        }

    def _analyze_colors(self, img: Image.Image) -> list:
        """Return top 5 dominant colors (RGB tuples)."""
        small = img.copy().convert("RGB")
        small.thumbnail((40, 40))
        try:
            colors = small.getcolors(1600)
        except Exception:
            return []
        if not colors:
            return []
        colors.sort(key=lambda x: x[0], reverse=True)
        result = []
        for cnt, col in colors[:5]:
            if isinstance(col, (list, tuple)) and len(col) >= 3:
                result.append(tuple(col[:3]))
        return result

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """PIL-only background removal.
        
        Strategy:
        1. Check if corners share similar color → solid BG → color-match removal
        2. If BG is bright/white → luminance thresholding
        3. If BG is complex → gentle edge-preserve fallback (keep original RGBA)
        """
        rgba = img.convert("RGBA")
        w, h = rgba.size
        px = rgba.load()

        # Sample corner colors
        corners = [
            px[0, 0], px[w - 1, 0],
            px[0, h - 1], px[w - 1, h - 1],
        ]

        def cdiff(c1, c2):
            return sum(abs(int(a) - int(b)) for a, b in zip(c1[:3], c2[:3]))

        # Check if corners are uniform (solid BG)
        is_solid = all(cdiff(corners[0], c) < 35 for c in corners[1:])

        if is_solid:
            bg_color = corners[0][:3]
            logger.info(f"Solid background detected: RGB{bg_color}")
            data = list(rgba.getdata())
            new_data = []
            for px_val in data:
                if cdiff(px_val, bg_color) < 45:
                    new_data.append((px_val[0], px_val[1], px_val[2], 0))
                else:
                    new_data.append(px_val)
            result = Image.new("RGBA", (w, h))
            result.putdata(new_data)
            return self._smooth_edges(result)

        # Check for white/near-white background
        avg_corner_lum = sum(sum(c[:3]) / 3 for c in corners) / 4
        if avg_corner_lum > 210:
            logger.info("Light/white background detected — luminance threshold removal")
            data = list(rgba.getdata())
            new_data = []
            for px_val in data:
                lum = (px_val[0] * 0.299 + px_val[1] * 0.587 + px_val[2] * 0.114)
                if lum > 225:
                    new_data.append((px_val[0], px_val[1], px_val[2], 0))
                else:
                    new_data.append(px_val)
            result = Image.new("RGBA", (w, h))
            result.putdata(new_data)
            return self._smooth_edges(result)

        # Complex background — just return as-is (already RGBA)
        logger.info("Complex background — keeping original (no removal)")
        return rgba

    def _smooth_edges(self, img: Image.Image) -> Image.Image:
        """Very light edge smoothing on the alpha channel."""
        try:
            r, g, b, a = img.split()
            a_smooth = a.filter(ImageFilter.GaussianBlur(radius=1))
            return Image.merge("RGBA", (r, g, b, a_smooth))
        except Exception:
            return img
