# CLAUDE.md — Custom Harness v2.0

This file is the **primary harness** for the Custom Harness multi-account video automation system.
When working in this repository, Claude must follow all conventions defined here.

---

## Project Identity

**Custom Harness v2.0** is a fully local, multi-account AI video generation and auto-publishing pipeline.
It creates viral short-form Reels and long-form YouTube videos using local LLM (Ollama) + free APIs,
then auto-posts to Facebook Pages and YouTube Channels on a cron schedule.

- **Maintainer:** Dipu
- **Location:** `/home/dipu/PROJECT/Github/custom-harness/`
- **System:** Linux, AMD Ryzen 5 7530U (12 threads), 6.7 GB RAM, no GPU
- **Python runtime:** `/home/dipu/PROJECT/Github/custom-harness/.venv` (Python 3.12)
- **FFmpeg:** `/home/dipu/.local/bin/ffmpeg` (v7.0.2 static)
- **LLM:** Ollama local (`llama3.1:8b`) with smart offline fallback

---

## Project Structure

```
custom-harness/
├── main.py                    ← Entry point: CLI, daemon, prebake, single-account
├── config.py                  ← Central config: video settings, VISUAL_STYLES,
│                                SUBTITLE_STYLES, BGM_STYLES, DURATION_MODES, TOPIC_BANK
├── accounts/
│   ├── account_manager.py     ← Account dataclass + JSON loader
│   ├── psychology_mindset.json ← MindEdge (cinematic + hormozi_yellow + ambient_cinematic)
│   ├── comic_viral.json        ← TooReal Facts (comic_popart + neon_green + lofi_chill)
│   ├── storytelling.json       ← StoryVault (vintage_retro + sunset_lavender + serene_nature)
│   └── cartoon_fun.json        ← CartoonBrain (anime + fire_coral + lofi_chill) [disabled]
├── brain/
│   ├── script_generator.py    ← MultiScriptGenerator: Ollama LLM → JSON scripts (5 content types)
│   ├── topic_selector.py      ← Auto topic selector from TOPIC_BANK
│   ├── topic_queue.py         ← User-queued custom topics (SQLite)
│   ├── video_buffer.py        ← Pre-generated video buffer (SQLite)
│   └── knowledge_vault.py     ← Offline fallback script bank
├── media/
│   ├── broll_manager.py       ← 4-tier image pipeline (local→AI→Wikimedia→procedural)
│   ├── image_gen.py           ← Pollinations AI image generation
│   ├── tts_engine.py          ← edge-tts async TTS + subtitle timing
│   └── video_assembler.py     ← Pillow frame renderer + FFmpeg mux + BGM synthesis
├── publisher/
│   ├── facebook.py            ← Facebook Reel upload via Graph API
│   └── youtube_pub.py         ← YouTube upload via OAuth2
├── content_types/
│   └── reel_cutter.py         ← Auto-cuts long video into Reels
├── guardrail/
│   └── checker.py             ← Script quality/safety checker (score ≥ 7.0)
├── scheduler/
│   └── auto_scheduler.py      ← APScheduler cron jobs per account
├── dashboard/
│   └── cli.py                 ← Rich terminal dashboard
├── assets/
│   ├── audio/                 ← Drop custom BGM mp3 files here (named: <bgm_style>.mp3)
│   ├── fonts/
│   │   ├── bold.ttf           ← Main bold font (Montserrat or similar)
│   │   └── regular.ttf        ← Regular weight font
│   └── broll/                 ← Drop custom images/clips here (per niche subdirectory)
├── output/
│   └── videos/                ← All generated videos land here
├── harness.db                 ← SQLite DB (topic queue + video buffer)
├── logs/harness.log           ← Rolling log file
├── requirements.txt
└── setup.sh
```

---

## How to Run

```bash
cd /home/dipu/PROJECT/Github/custom-harness
source .venv/bin/activate

# Run one cycle for all enabled accounts (generate + post)
python main.py

# Pre-generate 2 videos per account into buffer
python main.py --prebake

# Run as daemon (auto-scheduler + buffer maintenance)
python main.py --daemon

# Clean up disk space (removes posted videos and leftover temp frames)
python main.py --cleanup

# CLI Dashboard commands
python dashboard/cli.py status
python dashboard/cli.py buffer
python dashboard/cli.py cleanup
```

---

## Disk Space & Upload Verification

- **2-3x Upload Verification**: After sending a video to Facebook or YouTube, the harness polls the platform status 2–3 times to confirm the upload is acknowledged.
- **Auto Deletion**: Once verified on the platform, the local `.mp4` video file is deleted immediately to prevent disk exhaustion.
- **Temp Frame Cleanup**: Intermediate Pillow render frames (`frame_*.jpg`) and TTS audio clips are automatically deleted right after video assembly completes.
- **Manual Cleanup**: `python main.py --cleanup` or `python dashboard/cli.py cleanup` sweeps away any already-posted videos and orphaned temp directories at any time.

---

## Accounts & Their Styles

| Account ID | Channel | Visual Style | Subtitles | BGM | Content Types |
|-----------|---------|-------------|-----------|-----|--------------|
| `psychology_mindset` | MindEdge | `cinematic` | `hormozi_yellow` | `ambient_cinematic` | short_reel, long_video |
| `comic_viral` | TooReal Facts | `comic_popart` | `neon_green` | `lofi_chill` | short_reel |
| `storytelling` | StoryVault | `vintage_retro` | `sunset_lavender` | `serene_nature` | short_reel, storytelling_video |
| `cartoon_fun` | CartoonBrain | `anime` | `fire_coral` | `lofi_chill` | short_reel, cartoon_video *(disabled)* |

---

## Visual Styles (10 Total)

| Key | Description | Best Accounts |
|-----|-------------|--------------|
| `cinematic` | Film-grade, anamorphic, dramatic | psychology_mindset |
| `anime` | Japanese animation, vibrant, cel-shading | cartoon_fun |
| `cyberpunk` | Neon city, rain, blade runner | tech content |
| `3d_render` | Photorealistic 3D CGI, studio lighting | product content |
| `documentary` | Natural light, realistic photography | educational |
| `vintage_retro` | Film grain, sepia, aged texture | storytelling |
| `comic_popart` | Bold outlines, halftone dots, pop art | comic_viral |
| `watercolor_art` | Soft brushstrokes, pastel washes | lifestyle |
| `dark_fantasy_horror` | Gothic darkness, eerie fog | horror/mystery |
| `minimalist_vector` | Clean lines, flat design | business/edu |

---

## BGM Styles (6 Total) — FFmpeg lavfi synthesis (no files needed)

| Key | Mood | Frequencies |
|-----|------|------------|
| `ambient_cinematic` | Sweeping orchestral pads | C4, E4, G4, C5 |
| `synthwave_cyber` | 80s retro-wave synth | A3, C#4, E4, A4 |
| `lofi_chill` | Mellow lo-fi jazz warmth | C4, Eb4, F#4, A4 |
| `epic_heroic` | Dramatic brass + drums | G3, B3, D4, G4 |
| `suspense_mystery` | Tense strings, minor chords | F#3, A3, C4, Eb4 |
| `serene_nature` | Peaceful gentle harmony | D4, F4, A4, D5 |

> **Custom BGM:** Drop `<bgm_style>.mp3` into `assets/audio/` to override synthesis.

---

## Subtitle Styles (7 Total)

| Key | Look | Best For |
|-----|------|---------|
| `hormozi_yellow` | Bold white + yellow highlight | Viral psychology/mindset |
| `cyberpunk_cyan` | Electric cyan glow | Tech/gaming content |
| `clean_white` | White semi-transparent box | Documentary/news |
| `fire_coral` | Warm coral-red bold | Cartoon/fun |
| `neon_green` | Bright neon green | Comedy/memes |
| `sunset_lavender` | Soft purple | Storytelling/lifestyle |
| `boxed_contrast` | White text + opaque black box | Maximum readability |

---

## Image Sourcing Pipeline (4-Tier Auto Fallback)

```
1. Local assets/broll/<niche>/     → Custom images/clips (highest priority)
         ↓
2. Pollinations AI                 → Flux model → Turbo fallback (free AI, style-boosted)
         ↓
3. Wikimedia Commons               → Real HD stock photographs (open web search)
         ↓
4. Procedural Pillow Canvas        → Style-matched gradient + pattern (always works offline)
```

---

## Content Types & Script Formats

| Content Type | Duration | Script Format | Sections |
|-------------|----------|--------------|----------|
| `short_reel` | 45-60s | hook + 3-4 sections + cta | viral psychology/comedy |
| `long_video` | 7-8 min | hook + intro + 5 chapters + outro | educational deep-dive |
| `cartoon_video` | 3-5 min | scenes with action + dialogue | fun animated explainer |
| `storytelling_video` | 8 min | 4 story acts (setup→climax→resolution) | cinematic narrative |
| `comic` | 45s | setup + 3 bits + punchline | dry humor, relatable |

---

## LLM Script Generation

```
Ollama (llama3.1:8b) → JSON script
      ↓ (if Ollama offline or fails)
KnowledgeVault dynamic fallback (always works)
```

**Guardrail:** Min 100 words, max 220 words, quality score ≥ 7.0. 3 retry attempts before emergency fallback.

---

## Video Buffer System

- **`--prebake`**: Pre-generates 2 videos per account into SQLite buffer
- On scheduled post: pulls from buffer instantly (zero delay)
- After posting: replenishes buffer in background automatically
- Buffer health check: runs every 60 minutes in daemon mode

---

## Scheduling (Daemon Mode)

```
python main.py --daemon
```

| Account | Times (EST) | Content |
|---------|------------|---------|
| psychology_mindset | 09:00, 13:00, 19:00 | short_reel |
| psychology_mindset | 11:00 | long_video |
| comic_viral | 09:30, 12:30, 18:30, 22:00 | short_reel |
| storytelling | 08:00, 14:00, 21:00 | short_reel |
| storytelling | 16:00 | storytelling_video |

---

## Adding a New Account

1. Create `accounts/<account_id>.json` with full Account fields
2. Set `visual_style`, `subtitle_style`, `bgm_style` to valid keys from config.py
3. Add Facebook/YouTube credentials to `.env`
4. Run `python main.py --account <account_id> --test` to verify

**Account JSON required fields:**
```json
{
  "id": "my_account",
  "name": "Channel Name",
  "tagline": "Channel Tagline",
  "niche": "Content Niche",
  "content_types": ["short_reel"],
  "schedule": {"short_reel": ["10:00", "18:00"]},
  "visual_style": "cinematic",
  "subtitle_style": "hormozi_yellow",
  "bgm_style": "ambient_cinematic",
  "tts_voice": "en-US-GuyNeural",
  "tts_rate": "+10%",
  "color_primary": "#FFD700",
  "color_bg": "#0A0A1A",
  "color_text": "#FFFFFF",
  "long_video_duration_min": 7,
  "facebook": {"page_id_env": "FB_PAGE_ID_X", "token_env": "FB_TOKEN_X"},
  "youtube": {"credentials_file": "yt_x.pickle", "client_secrets": "client_secret.json"},
  "enabled": true,
  "auto_reel_from_long": false
}
```

---

## Adding New Styles

### New Visual Style
1. Add to `VISUAL_STYLES` dict in `config.py` (palette + prompt_booster)
2. Add procedural render branch in `media/broll_manager.py` → `_create_procedural_backdrop()`
3. Update relevant account JSON to use the new style key

### New BGM Style
1. Add chord frequencies to `BGM_STYLES` in `config.py`
2. The `video_assembler.py` auto-synthesizes it via FFmpeg lavfi — no extra code needed

### New Subtitle Style
1. Add style dict to `SUBTITLE_STYLES` in `config.py`
2. Automatically available in `video_assembler.py` — no extra code needed

---

## Environment Variables (.env)

```env
# Facebook
FB_PAGE_ID_PSYCHOLOGY=your_page_id
FB_TOKEN_PSYCHOLOGY=your_token
FB_PAGE_ID_COMIC=your_page_id
FB_TOKEN_COMIC=your_token
FB_PAGE_ID_STORY=your_page_id
FB_TOKEN_STORY=your_token

# YouTube (OAuth via client_secret.json files)
# Run once: python publisher/youtube_pub.py --auth

# Ollama LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Pexels (optional — for real video B-roll)
PEXELS_API_KEY=your_key_here
```

---

## Debugging

```bash
# Test full pipeline without posting
python main.py --test

# Check last log
tail -50 logs/harness.log

# Check buffer state
python -c "
import asyncio
from brain.video_buffer import VideoBuffer
buf = VideoBuffer()
async def check():
    for acc in ['psychology_mindset','comic_viral','storytelling']:
        count = await buf.get_ready_count(acc)
        print(f'{acc}: {count} videos ready')
asyncio.run(check())
"

# Verify all accounts + styles load correctly
python -c "
from accounts.account_manager import AccountManager
mgr = AccountManager()
for a in mgr.get_all():
    print(f'[{a.id}] visual={a.visual_style} sub={a.subtitle_style} bgm={a.bgm_style}')
"

# Check FFmpeg
/home/dipu/.local/bin/ffmpeg -version | head -1
```

---

## Agent Instructions (When Working in This Repo)

- **Never remove existing features** without user confirmation
- **Always test with `--test` flag** before enabling publish
- **config.py is the single source of truth** for all style registries — update there first
- **Account JSON fields** must match `Account` dataclass in `account_manager.py` exactly
- **SQLite DB** (`harness.db`) stores topic queue + video buffer — do not delete during testing
- **BGM synthesis** works offline via FFmpeg lavfi — no audio files needed unless custom override
- **4-tier image pipeline** handles all offline scenarios — never assume internet is available
- **Guardrail score** must be ≥ 7.0 — if failing, check script word count (min 100, max 220)
- **Performance:** FFmpeg threads auto-set to `min(cpu_cores-2, 10)` in config — never hardcode
