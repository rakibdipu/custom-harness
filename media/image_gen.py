"""
Image Generator - Pollinations.ai (FREE, unlimited, no API key)
Generates cinematic backgrounds for each video section
"""
import asyncio
import aiohttp
import aiofiles
import logging
import hashlib
import urllib.parse
from pathlib import Path
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logger = logging.getLogger(__name__)

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


class ImageGenerator:
    def __init__(self):
        self.config = Config()
        self.cache_dir = self.config.OUTPUT_DIR.parent / "temp" / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def generate_batch(self, prompts: list) -> list:
        """Generate multiple images concurrently"""
        tasks = [self.generate_single(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Replace failed images with fallback
        paths = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Image {i} failed: {result}. Using fallback.")
                fallback = await self._create_fallback_image(i)
                paths.append(fallback)
            else:
                paths.append(result)

        return paths

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
    async def generate_single(self, prompt: str, index: int = 0) -> str:
        """Generate one image from Pollinations.ai"""
        # Enhance prompt for cinematic style
        enhanced_prompt = (
            f"{prompt}, {self.config.IMAGE_STYLE}, "
            f"dark dramatic background, no text, no watermark, "
            f"vertical orientation 9:16, ultra detailed"
        )

        # Create cache key
        cache_key = hashlib.md5(enhanced_prompt.encode()).hexdigest()[:12]
        cached_path = self.cache_dir / f"img_{cache_key}.jpg"

        if cached_path.exists():
            logger.info(f"Using cached image for prompt {index}")
            return str(cached_path)

        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        url = POLLINATIONS_URL.format(prompt=encoded_prompt)
        url += f"?width={self.config.VIDEO_WIDTH}&height={self.config.VIDEO_HEIGHT}"
        url += "&nologo=true&enhance=true"

        logger.info(f"Generating image {index + 1}: {prompt[:50]}...")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(str(cached_path), "wb") as f:
                        await f.write(content)
                    logger.info(f"Image {index + 1} saved: {cached_path.name}")
                    return str(cached_path)
                else:
                    raise Exception(f"Pollinations returned {response.status}")

    async def _create_fallback_image(self, index: int) -> str:
        """Create a simple dark gradient fallback image using Pillow"""
        from PIL import Image, ImageDraw
        import numpy as np

        # Dark gradient backgrounds
        colors = [
            [(5, 10, 30), (20, 30, 80)],      # Deep navy
            [(10, 5, 25), (50, 20, 80)],       # Deep purple
            [(5, 20, 20), (10, 60, 70)],       # Dark teal
            [(20, 5, 5), (70, 15, 20)],        # Dark red
            [(5, 15, 5), (15, 50, 30)],        # Dark green
        ]
        color_pair = colors[index % len(colors)]

        img = Image.new("RGB", (self.config.VIDEO_WIDTH, self.config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)

        # Vertical gradient
        for y in range(self.config.VIDEO_HEIGHT):
            ratio = y / self.config.VIDEO_HEIGHT
            r = int(color_pair[0][0] + (color_pair[1][0] - color_pair[0][0]) * ratio)
            g = int(color_pair[0][1] + (color_pair[1][1] - color_pair[0][1]) * ratio)
            b = int(color_pair[0][2] + (color_pair[1][2] - color_pair[0][2]) * ratio)
            draw.line([(0, y), (self.config.VIDEO_WIDTH, y)], fill=(r, g, b))

        fallback_path = self.cache_dir / f"fallback_{index}.jpg"
        img.save(str(fallback_path), quality=95)
        return str(fallback_path)
