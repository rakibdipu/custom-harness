"""
Central configuration for Custom Harness
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure ~/.local/bin is in PATH for ffmpeg and uv
local_bin = str(Path.home() / ".local" / "bin")
if local_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

BASE_DIR = Path(__file__).parent

class Config:
    # --- LLM ENGINE (Cloud & Local) ---
    # MoneyPrinterTurbo feature: Supports Cloud APIs for 0% laptop CPU/RAM load!
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # auto | gemini | groq | openai | deepseek | ollama
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")

    # Local Ollama Fallback
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # --- STOCK VIDEO / B-ROLL APIS (MoneyPrinterTurbo Feature) ---
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
    PIXABAY_API_KEY: str = os.getenv("PIXABAY_API_KEY", "")

    # --- LAPTOP ECO / LOW-RESOURCE MODE ---
    # Limits CPU usage, prevents overheating, fan noise, and OS stutter
    LOW_RESOURCE_MODE: bool = os.getenv("LOW_RESOURCE_MODE", "false").lower() in ("true", "1", "yes")
    VIDEO_QUALITY: str = os.getenv("VIDEO_QUALITY", "720p" if LOW_RESOURCE_MODE else "1080p")
    FFMPEG_THREADS: int = int(os.getenv("FFMPEG_THREADS", "2" if LOW_RESOURCE_MODE else "0"))

    # --- CONTENT IDENTITY ---
    NICHE: str = os.getenv("NICHE", "psychology_mindset")
    CHANNEL_NAME: str = os.getenv("CHANNEL_NAME", "MindEdge")
    CHANNEL_TAGLINE: str = os.getenv("CHANNEL_TAGLINE", "Unlock Your Mental Edge")

    # --- VIDEO (Resolution automatically adapts to quality mode) ---
    VIDEO_WIDTH: int = 720 if os.getenv("VIDEO_QUALITY", "").lower() == "720p" or LOW_RESOURCE_MODE else int(os.getenv("VIDEO_WIDTH", 1080))
    VIDEO_HEIGHT: int = 1280 if os.getenv("VIDEO_QUALITY", "").lower() == "720p" or LOW_RESOURCE_MODE else int(os.getenv("VIDEO_HEIGHT", 1920))
    VIDEO_FPS: int = 24 if LOW_RESOURCE_MODE else int(os.getenv("VIDEO_FPS", 30))

    # --- TTS ---
    TTS_VOICE: str = "en-US-GuyNeural"      # Professional US male voice
    TTS_RATE: str = "+10%"                   # Slightly faster = more engaging
    TTS_PITCH: str = "+0Hz"

    # --- FACEBOOK ---
    FB_PAGE_ACCESS_TOKEN: str = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    FB_PAGE_ID: str = os.getenv("FB_PAGE_ID", "")

    # --- YOUTUBE ---
    YT_CLIENT_SECRETS_FILE: str = os.getenv("YT_CLIENT_SECRETS_FILE", "client_secret.json")
    YT_CREDENTIALS_FILE: str = os.getenv("YT_CREDENTIALS_FILE", "yt_credentials.pickle")

    # --- SCHEDULING ---
    POST_TIMES: list = os.getenv("POST_TIMES", "09:00,13:00,19:00").split(",")
    TIMEZONE: str = "US/Eastern"

    # --- PUBLISHING ---
    PUBLISH_FACEBOOK: bool = os.getenv("PUBLISH_FACEBOOK", "false").lower() == "true"
    PUBLISH_YOUTUBE: bool = os.getenv("PUBLISH_YOUTUBE", "false").lower() == "true"

    # --- PATHS ---
    OUTPUT_DIR: Path = BASE_DIR / "output" / "videos"
    LOGS_DIR: Path = BASE_DIR / "logs"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    FONT_BOLD: Path = BASE_DIR / "assets" / "fonts" / "bold.ttf"
    FONT_REGULAR: Path = BASE_DIR / "assets" / "fonts" / "regular.ttf"
    DB_PATH: Path = BASE_DIR / "harness.db"

    # --- GUARDRAIL (Strictly calibrated for 30-60 second reels) ---
    MIN_SCRIPT_WORDS: int = 85      # ~32-35s minimum
    MAX_SCRIPT_WORDS: int = 135     # ~50-54s maximum (never exceeds 58s)
    MIN_GUARDRAIL_SCORE: float = 7.0

    # --- IMAGE GENERATION ---
    IMAGE_PROVIDER: str = "pollinations"   # free, no API key
    IMAGE_STYLE: str = "cinematic dark background, professional, 4k, dramatic lighting"


# ─── VISUAL STYLES (10) ───────────────────────────────────────────────────────
VISUAL_STYLES = {
    "cinematic": {
        "label": "🎬 Cinematic",
        "prompt_booster": "cinematic film still, anamorphic lens, dramatic lighting, 4K, ultra realistic",
        "palette": [(10,10,20), (30,25,40), (255,215,0)],
        "gradient_stops": 3,
    },
    "anime": {
        "label": "🎌 Anime",
        "prompt_booster": "anime style, vibrant colors, Studio Ghibli quality, cel shading, 4K",
        "palette": [(5,5,25), (30,20,60), (255,100,200)],
        "gradient_stops": 3,
    },
    "cyberpunk": {
        "label": "⚡ Cyberpunk",
        "prompt_booster": "cyberpunk neon city, rain reflections, neon lights, blade runner aesthetic, 4K",
        "palette": [(5,0,20), (0,10,40), (0,255,200)],
        "gradient_stops": 3,
    },
    "3d_render": {
        "label": "🖥️ 3D Render",
        "prompt_booster": "photorealistic 3D render, studio lighting, octane render, high detail, 4K",
        "palette": [(15,15,15), (40,40,50), (200,200,255)],
        "gradient_stops": 3,
    },
    "documentary": {
        "label": "🎥 Documentary",
        "prompt_booster": "documentary photo, natural lighting, realistic, high resolution, National Geographic style",
        "palette": [(20,18,14), (50,45,35), (180,160,100)],
        "gradient_stops": 3,
    },
    "vintage_retro": {
        "label": "📽️ Vintage/Retro",
        "prompt_booster": "vintage photograph, film grain, sepia tones, retro aesthetic, aged texture",
        "palette": [(30,20,10), (80,55,30), (220,180,100)],
        "gradient_stops": 3,
    },
    "comic_popart": {
        "label": "💥 Comic/Pop Art",
        "prompt_booster": "comic book style, bold outlines, halftone dots, Roy Lichtenstein, vibrant pop art",
        "palette": [(255,230,0), (255,60,60), (0,100,255)],
        "gradient_stops": 3,
    },
    "watercolor_art": {
        "label": "🎨 Watercolor Art",
        "prompt_booster": "watercolor painting, soft brushstrokes, pastel colors, artistic, peaceful",
        "palette": [(200,220,240), (180,200,230), (100,160,200)],
        "gradient_stops": 3,
    },
    "dark_fantasy_horror": {
        "label": "🌑 Dark Fantasy/Horror",
        "prompt_booster": "dark fantasy, gothic atmosphere, dramatic shadows, eerie fog, mysterious, ominous",
        "palette": [(5,0,10), (20,5,25), (150,0,200)],
        "gradient_stops": 3,
    },
    "minimalist_vector": {
        "label": "📐 Minimalist Vector",
        "prompt_booster": "minimalist flat design, clean lines, geometric shapes, vector art, modern",
        "palette": [(245,245,250), (220,225,240), (50,80,200)],
        "gradient_stops": 3,
    },
}

# ─── SUBTITLE STYLES (7) ──────────────────────────────────────────────────────
SUBTITLE_STYLES = {
    "hormozi_yellow": {
        "label": "⚡ Hormozi Yellow",
        "fontname": "Montserrat",
        "fontsize": 64,
        "primary": "&H00FFFFFF",
        "outline": "&H000000FF",
        "back": "&HA0000000",
        "bold": -1,
        "border_style": 1,
        "outline_px": 4,
        "shadow_px": 2,
        "alignment": 2,
        "margin_v": 580,
        "marker": "{\\c&H00FFFF&}",
    },
    "cyberpunk_cyan": {
        "label": "⚡ Cyberpunk Cyan",
        "fontname": "Montserrat",
        "fontsize": 64,
        "primary": "&H00FFFF00",
        "outline": "&H00FF00FF",
        "back": "&HA0000000",
        "bold": -1,
        "border_style": 1,
        "outline_px": 3,
        "shadow_px": 3,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
    "clean_white": {
        "label": "🤍 Clean White",
        "fontname": "Montserrat",
        "fontsize": 58,
        "primary": "&H00FFFFFF",
        "outline": "&H00000000",
        "back": "&H80000000",
        "bold": 0,
        "border_style": 1,
        "outline_px": 2,
        "shadow_px": 1,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
    "fire_coral": {
        "label": "🔥 Fire Coral",
        "fontname": "Montserrat",
        "fontsize": 64,
        "primary": "&H002060FF",
        "outline": "&H00000080",
        "back": "&HA0000000",
        "bold": -1,
        "border_style": 1,
        "outline_px": 4,
        "shadow_px": 2,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
    "neon_green": {
        "label": "💚 Neon Green",
        "fontname": "Montserrat",
        "fontsize": 64,
        "primary": "&H0000FF00",
        "outline": "&H00003300",
        "back": "&HA0000000",
        "bold": -1,
        "border_style": 1,
        "outline_px": 3,
        "shadow_px": 2,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
    "sunset_lavender": {
        "label": "💜 Sunset Lavender",
        "fontname": "Montserrat",
        "fontsize": 60,
        "primary": "&H00FF80FF",
        "outline": "&H00400040",
        "back": "&H80000000",
        "bold": 0,
        "border_style": 1,
        "outline_px": 3,
        "shadow_px": 1,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
    "boxed_contrast": {
        "label": "📦 Boxed Contrast",
        "fontname": "Montserrat",
        "fontsize": 64,
        "primary": "&H00FFFFFF",
        "outline": "&H00000000",
        "back": "&HFF000000",
        "bold": -1,
        "border_style": 3,
        "outline_px": 0,
        "shadow_px": 0,
        "alignment": 2,
        "margin_v": 580,
        "marker": "",
    },
}

# ─── BGM STYLES (6) ───────────────────────────────────────────────────────────
BGM_STYLES = {
    "ambient_cinematic": {
        "label": "🎼 Ambient Cinematic",
        "freqs": [261.63, 329.63, 392.00, 523.25],
        "description": "Sweeping orchestral pads",
    },
    "synthwave_cyber": {
        "label": "🌃 Synthwave Cyber",
        "freqs": [220.00, 277.18, 329.63, 440.00],
        "description": "80s retro-wave synth pulse",
    },
    "lofi_chill": {
        "label": "☕ Lofi Chill",
        "freqs": [261.63, 311.13, 369.99, 440.00],
        "description": "Mellow lo-fi jazz warmth",
    },
    "epic_heroic": {
        "label": "⚔️ Epic Heroic",
        "freqs": [196.00, 246.94, 293.66, 392.00],
        "description": "Dramatic brass and war drums",
    },
    "suspense_mystery": {
        "label": "🎭 Suspense Mystery",
        "freqs": [185.00, 220.00, 261.63, 311.13],
        "description": "Tense strings minor chords",
    },
    "serene_nature": {
        "label": "🌿 Serene Nature",
        "freqs": [293.66, 349.23, 440.00, 587.33],
        "description": "Peaceful gentle harmony",
    },
}

# ─── DURATION MODES ───────────────────────────────────────────────────────────
DURATION_MODES = {
    "reel": {"label": "📱 Reel (30-60s)", "target_sec": 45, "num_scenes": 6},
    "long": {"label": "🎬 Long Video (2-3min)", "target_sec": 150, "num_scenes": 18},
    "teaser": {"label": "⚡ Teaser (15-25s)", "target_sec": 20, "num_scenes": 3},
}


# Viral topic bank for Psychology/Mindset niche (US audience)
TOPIC_BANK = [
    # Dark Psychology
    "3 dark psychology tricks manipulators use on you every day",
    "how to spot a narcissist before they destroy your life",
    "psychological tricks to make anyone respect you instantly",
    "the manipulation tactic most people fall for without realizing",
    "why smart people stay silent: the power of strategic quietness",

    # Mindset / Success
    "the 5am habit that changed millionaires' lives forever",
    "why 99% of people never reach their goals (and how to be the 1%)",
    "stoic principles that will make you mentally unbreakable",
    "the compound effect: why small daily habits beat big efforts",
    "how to rewire your brain for success in 21 days",

    # Social Intelligence
    "body language secrets that reveal if someone is lying to you",
    "how to make people instantly like and trust you",
    "the psychology of persuasion: 3 words that change minds",
    "why some people always get what they want from others",
    "how to read anyone's true intentions in seconds",

    # Self Improvement
    "discipline over motivation: the truth nobody tells you",
    "5 cognitive biases destroying your decision making",
    "how to stop caring what people think and own your life",
    "the scientific reason why most people stay broke",
    "why your environment controls your success more than your willpower",

    # Emotional Intelligence
    "signs you are more intelligent than you think",
    "how emotionally intelligent people handle toxic people",
    "the silent power of detachment: want less, get more",
    "why saying no is the most powerful word for your success",
    "how to turn your anxiety into your greatest strength",

    # Brain / Psychology Facts
    "your brain is lying to you: 3 cognitive distortions to stop now",
    "psychology facts most people learn too late in life",
    "why you procrastinate and the exact fix neuroscience recommends",
    "the neuroscience behind why rich people think differently",
    "how to hack your dopamine system for unstoppable motivation",

    # Relationships
    "3 types of people you need to remove from your life immediately",
    "the attachment style silently ruining all your relationships",
    "why loneliness makes you more dangerous than most people realize",
    "how high value people respond to disrespect",
    "the psychology of attraction: why playing hard to get works",

    # Money Mindset
    "the money mindset shift that separates the wealthy from the poor",
    "why most people will never be rich: the brutal truth",
    "3 financial habits keeping you broke without knowing it",
    "how to think like a billionaire starting with nothing",
    "the psychology of wealth: why your beliefs about money determine your income",

    # Power & Influence
    "the psychological power of never complaining to anyone",
    "how to command respect in any room without speaking loud",
    "the subtle art of letting other people reveal their secrets first",
    "why mysterious people are naturally more influential",
    "the psychological reason why people respect boundaries more than favors",
    "the 4-second silence rule that breaks any negotiation",
    "how to stop absorbing other people's negative energy",
    "why overexplaining yourself destroys your perceived competence",
    "the cognitive trick to stay completely calm under intense disrespect",
    "how high achievers eliminate mental fatigue before lunch",
]
