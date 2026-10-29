"""
Multi-style Script Generator
Generates scripts for: short_reel, long_video, cartoon, storytelling, comic
Adapts to each account's identity and content type
"""
import json
import logging
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ─── PROMPT TEMPLATES ─────────────────────────────────────────────────────────

PROMPTS = {

"short_reel": """You are a viral short-form script writer. Write a strictly 35-50 second script for {channel_name} ({niche}).
Topic: "{topic}"
Return ONLY valid JSON:
{{
  "title": "Hook title (max 70 chars)",
  "hook": "First sentence that stops scrolling (shocking/curiosity)",
  "sections": [
    {{"heading": "Short heading", "script": "2-3 sentence explanation"}}
  ],
  "cta": "Follow {channel_name} for more {niche} content.",
  "voiceover": "Full word-for-word voiceover (EXACTLY 95-120 words. Strictly 35-50 seconds, NEVER exceed 125 words)",
  "image_prompts": ["cinematic dark prompt 1", "prompt 2", "prompt 3", "prompt 4", "prompt 5"],
  "title_card": "Bold 6-word hook text",
  "description": "150-word YouTube/FB description",
  "hashtags": "#relevant #hashtags #here",
  "tags": ["tag1", "tag2"]
}}""",

"long_video": """You are a YouTube scriptwriter. Write a {duration}-minute educational video for {channel_name} ({niche}).
Topic: "{topic}"
Return ONLY valid JSON:
{{
  "title": "Compelling YouTube title (max 80 chars)",
  "hook": "Opening 30 seconds — big promise that keeps viewers watching",
  "intro": "90-second introduction — establish credibility and preview what they'll learn",
  "chapters": [
    {{"number": 1, "title": "Chapter title", "script": "Full 60-90 second section script with examples and stories", "timestamp": "00:00"}},
    {{"number": 2, "title": "Chapter title", "script": "Full section script", "timestamp": "00:00"}},
    {{"number": 3, "title": "Chapter title", "script": "Full section script", "timestamp": "00:00"}},
    {{"number": 4, "title": "Chapter title", "script": "Full section script", "timestamp": "00:00"}},
    {{"number": 5, "title": "Chapter title", "script": "Full section script", "timestamp": "00:00"}}
  ],
  "outro": "60-second outro — summary + strong CTA to subscribe",
  "voiceover": "Complete full script (600-900 words)",
  "image_prompts": ["visual for chapter 1", "chapter 2", "chapter 3", "chapter 4", "chapter 5", "outro"],
  "thumbnail_prompt": "Eye-catching YouTube thumbnail concept (high contrast, bold text area, dramatic image)",
  "description": "Full YouTube description with timestamps and keywords (300 words)",
  "hashtags": "#hashtags",
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}}""",

"cartoon_video": """You are a cartoon educational video writer. Write a fun, energetic script for {channel_name} — "{niche}".
Topic: "{topic}"
Style: Fun, humorous, uses cartoon analogies. Voice: enthusiastic. Target: all ages.
Return ONLY valid JSON:
{{
  "title": "Fun energetic title with emoji (max 70 chars)",
  "hook": "Funny/surprising opener that makes people laugh or go WOW",
  "scenes": [
    {{"scene": 1, "action": "What the cartoon character does", "dialogue": "What narrator/character says", "visual": "Cartoon-style image description"}}
  ],
  "punchline": "Funny or satisfying ending line",
  "voiceover": "Energetic full script (120-160 words, fun tone)",
  "image_prompts": ["cartoon style colorful fun scene 1", "scene 2", "scene 3", "scene 4"],
  "title_card": "Fun title in cartoon font style",
  "description": "Fun description with emojis",
  "hashtags": "#cartoon #funny #educational #fun #animation",
  "tags": ["cartoon", "funny", "educational"]
}}""",

"storytelling_video": """You are a master storyteller. Write a compelling short story for {channel_name} — "{niche}".
Topic/Theme: "{topic}"
Style: Cinematic, emotional, with a twist or lesson. Voice: calm, dramatic narrator.
Return ONLY valid JSON:
{{
  "title": "Compelling story title (creates curiosity)",
  "hook": "First sentence that MUST be read — sets up intrigue",
  "story_acts": [
    {{"act": "Setup", "script": "Establish character and world (60 words)"}},
    {{"act": "Rising Action", "script": "Build tension (80 words)"}},
    {{"act": "Climax", "script": "The turning point (60 words)"}},
    {{"act": "Resolution", "script": "Satisfying ending with lesson (60 words)"}}
  ],
  "moral": "One powerful sentence life lesson",
  "voiceover": "Full story script (250-320 words, cinematic narration style)",
  "image_prompts": ["cinematic warm story scene 1", "scene 2", "scene 3", "scene 4", "emotional final scene"],
  "title_card": "Story title (6 words max)",
  "description": "Story synopsis + moral for description",
  "hashtags": "#story #motivation #lifelesson #storytelling",
  "tags": ["story", "motivation", "life lesson"]
}}""",

"comic": """You are a viral comedy writer. Create a hilarious, relatable comedy script for {channel_name} — "{niche}".
Topic: "{topic}"
Style: Dry humor, relatable observations, unexpected punchlines. Target: US millennial/gen-z audience.
Return ONLY valid JSON:
{{
  "title": "Funny headline (max 70 chars, must make someone smirk)",
  "hook": "The setup — relatable situation everyone has experienced",
  "bits": [
    {{"setup": "The situation", "punchline": "The funny twist"}},
    {{"setup": "Another angle", "punchline": "Unexpected observation"}},
    {{"setup": "Final escalation", "punchline": "The mic drop"}}
  ],
  "outro": "Funny CTA that makes people want to follow",
  "voiceover": "Full comedy script (120-150 words, conversational, punchy)",
  "image_prompts": ["comic pop art bold colors funny scene 1", "scene 2", "scene 3"],
  "title_card": "Funny bold text (5 words)",
  "description": "Funny description with relatable humor",
  "hashtags": "#funny #relatable #comedy #viral #humor",
  "tags": ["funny", "relatable", "comedy", "viral"]
}}"""
}

# ─── COMIC AUTO-TOPIC BANK ────────────────────────────────────────────────────
COMIC_TOPICS = [
    "when your alarm says 5am but your brain says absolutely not",
    "every zoom call has that one person who never mutes",
    "the awkward moment when someone replies-all to an office email",
    "adulting is just googling things your parents definitely knew",
    "gym January vs gym February: a tale of two gyms",
    "that look you give when someone says 'quick meeting'",
    "why coffee hits different on Monday mornings",
    "when your phone dies at 1% right when you needed it most",
    "every group chat has these exact 5 types of people",
    "the universal experience of forgetting why you walked into a room",
    "when your boss says we're a family but cuts the pizza budget",
    "the 3am existential crisis starter pack",
    "when someone says 'we need to talk' and your brain fast-forwards to the worst scenario",
    "how people describe their jobs vs what they actually do",
]


from brain.knowledge_vault import KnowledgeVault

class MultiScriptGenerator:
    def __init__(self, ollama_host: str = "http://localhost:11434",
                 model: str = "llama3.1:8b"):
        self.ollama_url = f"{ollama_host}/api/generate"
        self.model = model
        self.vault = KnowledgeVault()

    async def generate(self, topic: str, content_type: str, account) -> dict:
        """Generate script for given content type and account"""
        prompt_template = PROMPTS.get(content_type, PROMPTS["short_reel"])
        duration = getattr(account, 'long_video_duration_min', 7)

        prompt = prompt_template.format(
            channel_name=account.name,
            tagline=account.tagline,
            niche=account.niche,
            topic=topic,
            duration=duration
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85 if content_type in ["comic", "cartoon_video"] else 0.75,
                "top_p": 0.9,
                "num_predict": 3000 if content_type == "long_video" else 1500,
            }
        }

        logger.info(f"Generating [{content_type}] script: '{topic[:50]}'")

        # 1. Try local Ollama if available
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=4)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        raw = result.get("response", "")
                        parsed = self._parse_json(raw, content_type, topic, account)
                        if parsed:
                            return parsed
        except Exception:
            pass  # Fast fallback to smart dynamic generator

        # 2. Smart dynamic procedural script generator
        return self._dynamic_script(content_type, topic, account)

    def _parse_json(self, text: str, content_type: str, topic: str, account) -> dict:
        """Extract JSON from LLM response and normalize sections/cta"""
        res = None
        try:
            res = json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        if not res:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    res = json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

        if not res or not isinstance(res, dict):
            logger.warning("JSON parse failed — using dynamic script")
            return self._dynamic_script(content_type, topic, account)

        # Normalization across all 5 content types
        if not res.get("sections"):
            if "chapters" in res and isinstance(res["chapters"], list):
                res["sections"] = [
                    {"heading": ch.get("title", f"Chapter {ch.get('number', i+1)}"), "script": ch.get("script", "")}
                    for i, ch in enumerate(res["chapters"])
                ]
            elif "story_acts" in res and isinstance(res["story_acts"], list):
                res["sections"] = [
                    {"heading": act.get("act", f"Act {i+1}"), "script": act.get("script", "")}
                    for i, act in enumerate(res["story_acts"])
                ]
            elif "scenes" in res and isinstance(res["scenes"], list):
                res["sections"] = [
                    {"heading": sc.get("visual") or f"Scene {sc.get('scene', i+1)}", "script": sc.get("dialogue") or sc.get("action", "")}
                    for i, sc in enumerate(res["scenes"])
                ]
            elif "bits" in res and isinstance(res["bits"], list):
                res["sections"] = [
                    {"heading": b.get("setup", f"Bit {i+1}"), "script": f"{b.get('setup', '')} - {b.get('punchline', '')}"}
                    for i, b in enumerate(res["bits"])
                ]

        if not res.get("cta"):
            res["cta"] = res.get("outro") or res.get("moral") or res.get("punchline") or f"Follow {account.name} for more."

        return res

    def _dynamic_script(self, content_type: str, topic: str, account) -> dict:
        """High-converting, niche-specific dynamic script generator using KnowledgeVault"""
        c_name = getattr(account, "name", "MindEdge")
        acc_id = getattr(account, "id", "")

        # 1. Long form videos (5-7 min multi-chapter episodes)
        if content_type in ["long_video", "storytelling_video"]:
            return self.vault.get_long_video_script(topic, channel_name=c_name, account_id=acc_id)

        # 2. Short form reels (30-60s)
        if acc_id == "comic_viral" or content_type == "comic":
            return self.vault.get_comic_script(topic, channel_name=c_name)
        elif acc_id == "storytelling":
            return self.vault.get_story_script(topic, channel_name=c_name)
        elif acc_id == "cartoon_fun" or content_type == "cartoon_video":
            return self.vault.get_cartoon_script(topic, channel_name=c_name)
        else: # psychology_mindset or default
            return self.vault.get_psychology_script(topic, channel_name=c_name)
