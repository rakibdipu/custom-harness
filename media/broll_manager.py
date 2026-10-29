"""
B-Roll & Image Manager — 4-Tier Asset Pipeline
Priority:
  1. Local assets/broll/<niche>/ (user custom images)
  2. Pollinations AI (Flux → Turbo fallback, style-boosted, free)
  3. Wikimedia Commons web stock search (real HD photographs)
  4. Instant procedural Pillow canvas (offline, always works)

Visual Styles: cinematic, anime, cyberpunk, 3d_render, documentary,
               vintage_retro, comic_popart, watercolor_art,
               dark_fantasy_horror, minimalist_vector
"""
import os
import re
import logging
import random
import asyncio
import aiohttp
import aiofiles
import aiosqlite
from pathlib import Path
from config import Config, VISUAL_STYLES

logger = logging.getLogger(__name__)

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={seed}&nologo=true&model={model}"

# Curated diverse cinematic b-roll search terms by niche (prevents repeating the same clip)
NICHE_BROLL_POOLS = {
    "psychology": [
        "man thinking dark silhouette", "chess game dramatic strategy", "neural network glowing",
        "clock hourglass sand trickling", "rainy city street night lights", "mysterious silhouette window",
        "human eye close up intense", "antique library dark books", "matrix digital code abstract",
        "lone figure walking foggy road", "smoke dramatic backlighting", "hand writing vintage journal",
        "crowd time lapse city commuters", "brain synapse medical 3d", "shadows on wall noir",
        "whisper secret conversation", "stopwatch ticking macro", "man looking mirror reflection",
        "calm water ripples slow motion", "dramatic sunset clouds time lapse"
    ],
    "storytelling": [
        "ancient ruins drone aerial", "vintage book pages turning slow", "monk meditation temple calm",
        "foggy pine forest cinematic", "campfire night wilderness flames", "antique compass vintage map",
        "candle light flame darkness", "medieval castle fortress", "ocean waves crashing storm rocks",
        "starry night sky milky way", "desert sand dunes wind", "mountain peak climber sunrise",
        "lone horse rider sunset", "old wooden ship sailing", "ancient parchment calligraphy"
    ],
    "comic": [
        "alarm clock ringing morning", "steaming coffee cup breakfast", "typing keyboard laptop frustrated",
        "crowded subway commuters rush", "funny dog head tilt reaction", "confused expression face close up",
        "party dancing crowd lights", "eating popcorn theater dark", "exhausted office worker desk",
        "traffic jam city honking", "supermarket grocery shopping cart", "laughing friends talking table",
        "person running late rushing street", "smartphone screen glowing face bed"
    ]
}

# Words to strip from Wikimedia/Pixabay search so we get actual visual subjects
_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "of", "for", "with", "by", "from",
    "and", "or", "is", "are", "was", "were", "be", "been", "has", "have",
    "to", "that", "this", "it", "as", "up", "so", "but", "if",
    "dark", "light", "background", "cinematic", "dramatic", "realistic",
    "professional", "beautiful", "stunning", "amazing", "incredible",
    "high", "quality", "ultra", "super", "very", "highly", "style",
    "photo", "image", "picture", "scene", "view", "shot", "detailed",
    "contrasting", "comparison", "expert", "demonstrating", "transformation",
    "futuristic", "inspiring", "visual", "render", "film", "camera",
    "lens", "lighting", "4k", "8k", "hdr", "resolution", "prompt", "chapter",
    "psychology", "facts", "truth", "subconscious", "episode", "audio"
}


class BrollManager:
    def __init__(self):
        self.config = Config()
        self.broll_dir = Path("assets/broll").resolve()
        self.broll_dir.mkdir(parents=True, exist_ok=True)
        self.pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

    async def _init_db(self):
        """Ensure used clips table exists in SQLite"""
        async with aiosqlite.connect("harness.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS used_media_clips (
                    clip_id TEXT PRIMARY KEY,
                    source TEXT,
                    keyword TEXT,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def _is_clip_used(self, clip_id: str) -> bool:
        await self._init_db()
        async with aiosqlite.connect("harness.db") as db:
            async with db.execute("SELECT clip_id FROM used_media_clips WHERE clip_id = ?", (str(clip_id),)) as cur:
                return await cur.fetchone() is not None

    async def _mark_clip_used(self, clip_id: str, keyword: str):
        await self._init_db()
        async with aiosqlite.connect("harness.db") as db:
            await db.execute("""
                INSERT OR REPLACE INTO used_media_clips (clip_id, source, keyword, used_at)
                VALUES (?, 'pixabay', ?, CURRENT_TIMESTAMP)
            """, (str(clip_id), keyword))
            await db.commit()

    def get_local_clips(self, niche: str = "") -> list[Path]:
        """Find all local images/clips in assets/broll/"""
        exts = ["*.mp4", "*.jpg", "*.jpeg", "*.png", "*.webp"]
        clips = []
        for ext in exts:
            clips.extend(self.broll_dir.glob(ext))
        if niche:
            niche_dir = self.broll_dir / niche
            if niche_dir.exists():
                for ext in exts:
                    clips.extend(niche_dir.glob(ext))
        return clips

    async def get_clips_for_keywords(
        self,
        keywords: list[str],
        niche: str = "",
        count: int = 4,
        visual_style: str = "cinematic",
    ) -> list[str]:
        """
        Get unique background clips matching keywords using 4-tier pipeline.
        Pads with diverse niche terms instead of repeating identical queries.
        """
        style_info = VISUAL_STYLES.get(visual_style, VISUAL_STYLES["cinematic"])
        chosen = []

        # ── Tier 1: Local custom images ──────────────────────────────────
        local = self.get_local_clips(niche)
        if local:
            for _ in range(count):
                chosen.append(str(random.choice(local)))
            logger.info(f"Using {len(chosen)} local images from assets/broll/")
            return chosen

        # ── Tiers 2–4: fetch per keyword in parallel ─────────────────────
        temp_dir = Path("output/temp_broll").resolve()
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Match niche pool
        niche_key = "psychology"
        if "story" in niche.lower():
            niche_key = "storytelling"
        elif "comic" in niche.lower() or "meme" in niche.lower() or "funny" in niche.lower():
            niche_key = "comic"

        pool = list(NICHE_BROLL_POOLS.get(niche_key, NICHE_BROLL_POOLS["psychology"]))
        random.shuffle(pool)

        # Build diverse list of keywords without repeating identical terms
        target_kws = list(keywords[:count]) if keywords else []
        pool_idx = 0
        while len(target_kws) < count:
            if pool_idx < len(pool):
                target_kws.append(pool[pool_idx])
                pool_idx += 1
            else:
                target_kws.append("cinematic atmospheric motion")

        tasks = [
            self._get_one_image(kw, i, niche, style_info, temp_dir, visual_style)
            for i, kw in enumerate(target_kws)
        ]
        chosen = await asyncio.gather(*tasks)
        return list(chosen)

    async def _get_one_image(
        self, keyword: str, idx: int, niche: str,
        style_info: dict, temp_dir: Path, visual_style: str
    ) -> str:
        """Priority: Local -> Pexels HD Video -> Pixabay Real HD Video -> Pollinations AI -> Wikimedia -> Procedural"""

        # ── Tier 1.5: Pexels Real HD Portrait Video (MoneyPrinterTurbo Feature) ──
        if self.pexels_key:
            try:
                search_kw = self._extract_subject_keyword(keyword)
                video_clip = await self._fetch_pexels_video(search_kw, idx, temp_dir)
                if video_clip:
                    logger.info(f"[Pexels Video 🎬✅] '{search_kw}' -> {Path(video_clip).name}")
                    return video_clip
            except Exception as e:
                logger.debug(f"Pexels video search error for '{keyword}': {e}")

        # ── Tier 2: Pixabay Real HD Video Clip (Priority!) ────────────────
        if self.pixabay_key:
            try:
                search_kw = self._extract_subject_keyword(keyword)
                video_clip = await self._fetch_pixabay_video(search_kw, idx, temp_dir)
                if video_clip:
                    logger.info(f"[Pixabay Video 🎬✅] '{search_kw}' -> {Path(video_clip).name}")
                    return video_clip
            except Exception as e:
                logger.debug(f"Pixabay video search error for '{keyword}': {e}")

        # ── Tier 3: Pollinations AI (Active Free Model: sana) ──────────────
        try:
            boosted = f"{keyword}, {style_info['prompt_booster']}"
            img = await self._fetch_pollinations(boosted, idx, temp_dir)
            if img:
                logger.info(f"[Pollinations ✅] {keyword[:40]}")
                return img
        except Exception as e:
            logger.debug(f"Pollinations error for '{keyword}': {e}")

        # ── Tier 4: Wikimedia Commons ─────────────────────────────────────
        try:
            search_kw = self._extract_subject_keyword(keyword)
            img = await self._fetch_wikimedia(search_kw, idx, temp_dir)
            if img:
                logger.info(f"[Wikimedia ✅] '{search_kw}'")
                return img
        except Exception as e:
            logger.debug(f"Wikimedia error for '{keyword}': {e}")

        # ── Tier 5: Procedural canvas fallback ────────────────────────────
        logger.info(f"[Procedural 🎨] style={visual_style}")
        return await self._create_procedural_backdrop(idx, niche, visual_style, temp_dir)

    async def _fetch_pexels_video(self, keyword: str, idx: int, temp_dir: Path) -> str | None:
        """Search and download real vertical HD video clip from Pexels Video API (MoneyPrinterTurbo Feature)"""
        if not self.pexels_key:
            return None

        clean_kw = re.sub(r'[^a-zA-Z0-9 ]', '', keyword).strip()
        if not clean_kw:
            clean_kw = "cinematic atmospheric"

        headers = {
            "Authorization": self.pexels_key,
            "User-Agent": "CustomHarness/2.0"
        }
        import urllib.parse
        q_encoded = urllib.parse.quote(clean_kw)
        url = f"https://api.pexels.com/videos/search?query={q_encoded}&orientation=portrait&per_page=15"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    videos = data.get("videos", [])
                    if not videos:
                        words = clean_kw.split()
                        if len(words) > 1:
                            q_simple = urllib.parse.quote(words[0])
                            url_simple = f"https://api.pexels.com/videos/search?query={q_simple}&orientation=portrait&per_page=10"
                            async with session.get(url_simple, timeout=aiohttp.ClientTimeout(total=10)) as r_simple:
                                if r_simple.status == 200:
                                    data_s = await r_simple.json()
                                    videos = data_s.get("videos", [])

                    if not videos:
                        return None

                    fresh_vids = [v for v in videos if not await self._is_clip_used(str(v.get("id")))]
                    candidates = fresh_vids if fresh_vids else videos
                    chosen_vid = random.choice(candidates)
                    clip_id = str(chosen_vid.get("id"))

                    out_file = temp_dir / f"pexels_{clip_id}.mp4"
                    if out_file.exists() and out_file.stat().st_size > 50000:
                        await self._mark_clip_used(clip_id, clean_kw)
                        return str(out_file)

                    video_files = chosen_vid.get("video_files", [])
                    video_url = None
                    portrait_files = [f for f in video_files if (f.get("height", 0) or 0) > (f.get("width", 0) or 0)]
                    target_pool = portrait_files if portrait_files else video_files
                    for vf in target_pool:
                        if vf.get("file_type") == "video/mp4" and vf.get("link"):
                            video_url = vf.get("link")
                            if vf.get("quality") == "hd":
                                break

                    if not video_url:
                        return None

                    async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                        if v_resp.status == 200:
                            content = await v_resp.read()
                            if len(content) > 50000:
                                async with aiofiles.open(str(out_file), "wb") as f:
                                    await f.write(content)
                                await self._mark_clip_used(clip_id, clean_kw)
                                return str(out_file)
        except Exception as e:
            logger.debug(f"Pexels video download error: {e}")
            return None

    async def _fetch_pixabay_video(self, keyword: str, idx: int, temp_dir: Path) -> str | None:
        """Search and download real HD video clip from Pixabay Video API with deduplication"""
        if not self.pixabay_key:
            return None

        clean_kw = re.sub(r'[^a-zA-Z0-9 ]', '', keyword).strip()
        if not clean_kw:
            clean_kw = "cinematic atmospheric"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
        }
        import urllib.parse
        q_encoded = urllib.parse.quote(clean_kw)
        url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={q_encoded}&per_page=20"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    hits = data.get("hits", [])
                    if not hits:
                        # Fallback search with first word if multi-word query had 0 hits
                        words = clean_kw.split()
                        if len(words) > 1:
                            q_simple = urllib.parse.quote(words[0])
                            url_simple = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={q_simple}&per_page=15"
                            async with session.get(url_simple, timeout=aiohttp.ClientTimeout(total=10)) as r_simple:
                                if r_simple.status == 200:
                                    data_s = await r_simple.json()
                                    hits = data_s.get("hits", [])

                    if not hits:
                        return None

                    # Prioritize fresh, unused video clips
                    fresh_hits = []
                    for h in hits:
                        cid = str(h.get("id"))
                        if not await self._is_clip_used(cid):
                            fresh_hits.append(h)

                    # If all hits in this query were previously used, use any hit
                    candidates = fresh_hits if fresh_hits else hits
                    chosen_hit = random.choice(candidates)
                    clip_id = str(chosen_hit.get("id"))

                    out_file = temp_dir / f"pixabay_{clip_id}.mp4"
                    if out_file.exists() and out_file.stat().st_size > 50000:
                        await self._mark_clip_used(clip_id, clean_kw)
                        return str(out_file)

                    vids = chosen_hit.get("videos", {})
                    # Prefer medium (1280x720) or small (960x540) or large
                    video_url = (
                        vids.get("medium", {}).get("url")
                        or vids.get("small", {}).get("url")
                        or vids.get("large", {}).get("url")
                    )
                    if not video_url:
                        return None

                    # Download the video binary
                    async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=30)) as v_resp:
                        if v_resp.status == 200:
                            content = await v_resp.read()
                            if len(content) > 50000:
                                async with aiofiles.open(str(out_file), "wb") as f:
                                    await f.write(content)
                                await self._mark_clip_used(clip_id, clean_kw)
                                return str(out_file)
        except Exception as e:
            logger.debug(f"Pixabay video download error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    async def _fetch_pollinations(self, prompt: str, idx: int, temp_dir: Path) -> str | None:
        """Fetch from Pollinations AI using free active 'sana' model and browser headers"""
        import urllib.parse
        W, H = self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT
        seed = random.randint(1000, 99999)

        safe = "".join(c if c.isalnum() else "_" for c in prompt[:30])
        path = temp_dir / f"poll_sana_{idx}_{safe[:20]}.jpg"
        if path.exists() and path.stat().st_size > 10000:
            return str(path)

        encoded = urllib.parse.quote(prompt)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }

        # 'sana' is the currently free, unmetered high-res model on Pollinations
        for model in ["sana", ""]:
            m_param = f"&model={model}" if model else ""
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={W}&height={H}&seed={seed}&nologo=true{m_param}"
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as r:
                        if r.status == 200:
                            content = await r.read()
                            if len(content) > 10000:
                                async with aiofiles.open(str(path), "wb") as f:
                                    await f.write(content)
                                return str(path)
            except Exception as e:
                logger.debug(f"Pollinations model {model} attempt failed: {e}")
                continue
        return None

    async def _fetch_wikimedia(self, keyword: str, idx: int, temp_dir: Path) -> str | None:
        """Search Wikimedia Commons for a real HD photograph"""
        path = temp_dir / f"wiki_{idx}_{keyword[:20].replace(' ','_')}.jpg"
        if path.exists() and path.stat().st_size > 10000:
            return str(path)

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": keyword,
            "gsrnamespace": "6",
            "gsrlimit": "8",
            "prop": "imageinfo",
            "iiprop": "url|size|mediatype",
            "iiurlwidth": str(self.config.VIDEO_WIDTH),
            "format": "json",
            "origin": "*"
        }
        headers = {
            "User-Agent": "CustomHarnessBot/2.0 (contact@mindedge.media)"
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    WIKIMEDIA_API, params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()

                pages = data.get("query", {}).get("pages", {})
                urls = []
                for page in pages.values():
                    info = page.get("imageinfo", [{}])[0]
                    url = info.get("thumburl") or info.get("url", "")
                    mt = info.get("mediatype", "")
                    if url and mt in ("BITMAP", "") and not url.endswith(".svg"):
                        urls.append(url)

                if not urls:
                    return None

                img_url = random.choice(urls[:4])
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=20)) as r2:
                    if r2.status == 200:
                        content = await r2.read()
                        if len(content) > 10000:
                            raw = temp_dir / f"wiki_raw_{idx}.jpg"
                            async with aiofiles.open(str(raw), "wb") as f:
                                await f.write(content)
                            fitted = self._fit_and_save(raw, path)
                            return fitted
        except Exception as e:
            logger.debug(f"Wikimedia error: {e}")
        return None

    def _fit_and_save(self, src: Path, dst: Path) -> str:
        """Center-crop and resize image to 9:16 video resolution"""
        from PIL import Image
        try:
            W, H = self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT
            img = Image.open(src).convert("RGB")
            iw, ih = img.size
            target_ratio = W / H
            current_ratio = iw / ih

            if current_ratio > target_ratio:
                new_w = int(ih * target_ratio)
                left = (iw - new_w) // 2
                img = img.crop((left, 0, left + new_w, ih))
            else:
                new_h = int(iw / target_ratio)
                top = (ih - new_h) // 2
                img = img.crop((0, top, iw, top + new_h))

            img = img.resize((W, H), Image.LANCZOS)
            img.save(str(dst), quality=92)
            return str(dst)
        except Exception as e:
            logger.debug(f"Image fit failed: {e}")
            return str(src)

    def _extract_subject_keyword(self, prompt: str) -> str:
        """Extract meaningful subject nouns from a visual prompt with semantic mapping"""
        bn_words = re.findall(r"[\u0980-\u09FF]+", prompt)
        if bn_words:
            return " ".join(bn_words[:2])

        p_lower = prompt.lower()
        if "chess" in p_lower:
            return "chess game"
        elif "brain" in p_lower or "neuro" in p_lower or "synapse" in p_lower:
            return "brain neural"
        elif "clock" in p_lower or "hour" in p_lower or "time" in p_lower or "stopwatch" in p_lower:
            return "clock hourglass"
        elif "book" in p_lower or "library" in p_lower:
            return "antique library"
        elif "rain" in p_lower:
            return "rainy city street"
        elif "think" in p_lower or "mind" in p_lower:
            return "man thinking"
        elif "coffee" in p_lower:
            return "coffee cup steam"
        elif "money" in p_lower or "dollar" in p_lower:
            return "money counting"
        elif "office" in p_lower or "work" in p_lower or "computer" in p_lower or "laptop" in p_lower:
            return "typing laptop office"
        elif "eye" in p_lower or "look" in p_lower or "gaze" in p_lower:
            return "human eye close"
        elif "crowd" in p_lower or "street" in p_lower or "people" in p_lower:
            return "city crowd street"
        elif "forest" in p_lower or "nature" in p_lower or "tree" in p_lower:
            return "foggy forest"
        elif "monk" in p_lower or "meditat" in p_lower or "temple" in p_lower:
            return "monk meditation"
        elif "alarm" in p_lower or "morning" in p_lower:
            return "alarm clock morning"

        words = re.findall(r"[a-zA-Z]+", p_lower)
        kept = [w for w in words if w not in _STOPWORDS and len(w) > 3]
        return " ".join(kept[:2]) if kept else "cinematic atmospheric"

    async def _create_procedural_backdrop(
        self, idx: int, niche: str, visual_style: str, temp_dir: Path
    ) -> str:
        """Style-matched procedural canvas using Pillow (always works offline)"""
        from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
        import numpy as np

        safe_niche = "".join(c if c.isalnum() else "_" for c in niche.lower()).strip("_")
        img_path = temp_dir / f"proc_{visual_style}_{safe_niche}_{idx}.jpg"
        if img_path.exists():
            return str(img_path)

        W, H = self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT
        style_info = VISUAL_STYLES.get(visual_style, VISUAL_STYLES["cinematic"])
        palette = style_info["palette"]

        c0, c1, c2 = palette[0], palette[1], palette[2]

        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Vertical gradient (c0 → c1)
        for y in range(H):
            t = y / H
            r = int(c0[0] + (c1[0] - c0[0]) * t)
            g = int(c0[1] + (c1[1] - c0[1]) * t)
            b = int(c0[2] + (c1[2] - c0[2]) * t)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Style-specific overlays
        if visual_style == "cyberpunk":
            # Neon vertical lines
            for x in range(0, W, W // 6):
                alpha_line = Image.new("RGBA", (3, H), (*c2, 60))
                img_rgba = img.convert("RGBA")
                img_rgba.paste(alpha_line, (x, 0), alpha_line)
                img = img_rgba.convert("RGB")
        elif visual_style == "anime":
            # Speed lines from centre
            for angle in range(0, 360, 20):
                import math
                cx, cy = W // 2, H // 2
                rad = math.radians(angle)
                ex = int(cx + math.cos(rad) * W)
                ey = int(cy + math.sin(rad) * H)
                draw.line([(cx, cy), (ex, ey)], fill=(*c2, ), width=1)
        elif visual_style == "comic_popart":
            # Halftone dot pattern
            dot_r = 18
            for gy in range(0, H, dot_r * 3):
                for gx in range(0, W, dot_r * 3):
                    draw.ellipse(
                        [(gx, gy), (gx + dot_r, gy + dot_r)],
                        fill=tuple(min(v + 40, 255) for v in c2)
                    )
        elif visual_style in ("vintage_retro",):
            # Film grain via noise
            arr = np.array(img).astype(np.int16)
            noise = np.random.randint(-18, 18, arr.shape, dtype=np.int16)
            arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
        elif visual_style == "minimalist_vector":
            # Clean geometric shapes
            draw.rectangle([(W // 4, H // 3), (3 * W // 4, 2 * H // 3)],
                           outline=c2, width=4)
            draw.line([(0, H // 2), (W, H // 2)], fill=c2, width=2)
        elif visual_style == "dark_fantasy_horror":
            # Vignette corners
            vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            vd = ImageDraw.Draw(vig)
            for r_off in range(0, min(W, H) // 2, 8):
                alpha = int(180 * (1 - r_off / (min(W, H) // 2)))
                vd.ellipse(
                    [(r_off, r_off), (W - r_off, H - r_off)],
                    outline=(0, 0, 0, alpha), width=8
                )
            img = Image.alpha_composite(img.convert("RGBA"), vig).convert("RGB")

        # Accent lines (all styles)
        draw = ImageDraw.Draw(img)
        for step in range(4):
            y_pos = int(H * 0.3 + step * H * 0.12)
            draw.line([(80, y_pos), (W - 80, y_pos)], fill=c2, width=1)

        # Soft blur for cinematic feel
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img.save(str(img_path), quality=92)
        return str(img_path)
