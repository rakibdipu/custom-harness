# 🎬 Custom Harness v2.0

> **Autonomous Multi-Account AI Video Generation & Auto-Publishing Engine**  
> Creates viral short-form Reels and long-form videos locally using LLMs, TTS, and FFmpeg, then automatically schedules and posts them to Facebook & YouTube.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(Llama%203.1)-black)](https://ollama.ai)
[![FFmpeg](https://img.shields.io/badge/Render-FFmpeg-red)](https://ffmpeg.org)

---

## 🌟 Key Features

- **🤖 100% Local Script Generation:** Uses local Ollama (`llama3.1:8b`) with offline fallback script bank (`knowledge_vault.py`).
- **🎙️ Neural TTS & Dynamic Subtitles:** Uses `edge-tts` for high-fidelity voiceovers and word-by-word highlighted subtitle timing.
- **🎨 4-Tier Visual / B-Roll Pipeline:** 
  1. Local niche assets
  2. Pollinations AI image generation
  3. Stock APIs (Pexels / Wikimedia)
  4. Dynamic procedural animations
- **📱 Multi-Account Architecture:** Define separate personas/brands with unique visual styles, color palettes, fonts, voices, and upload targets (`accounts/*.json`).
- **🛡️ Guardrail Quality Checker:** Automatically evaluates hooks, engagement potential, and safety before rendering (score $\ge$ 7.0 required).
- **⏳ Video Buffer & Prebake:** Pre-render videos ahead of time into a local buffer so scheduled posts are instant.
- **🚀 Auto-Publishing:**
  - **Facebook Pages:** Graph API upload for Reels with title, hashtags, and description.
  - **YouTube:** OAuth2 upload for Shorts and long-form video playlists.
- **📊 Terminal Dashboard:** Built-in Rich CLI dashboard to monitor buffer status, topics, and background runner.
---

## 🎥 Sample Demo Reels (100% Autonomous Output)

The following reels were generated, narrated, subtitled, and assembled completely autonomously by Custom Harness:

| Niche / Style | Duration | Video Preview / Link |
| :--- | :---: | :--- |
| **🧠 Psychology & Mindset** | ~33s | [▶️ Watch Psychology Demo Reel](assets/demos/psychology_reel_demo.mp4) |
| **🎭 Comic & Viral Story** | ~32s | [▶️ Watch Comic Viral Demo Reel](assets/demos/comic_viral_demo.mp4) |
| **📖 Deep Storytelling** | ~30s | [▶️ Watch Storytelling Demo Reel](assets/demos/storytelling_demo.mp4) |

> 💡 *All voiceovers, word-by-word synchronized subtitles, B-roll selection, Ken Burns panning, and background audio ducking were produced without manual editing.*

---

## 📁 Repository Structure

```
custom-harness/
├── main.py                    # Main CLI entry point
├── config.py                  # Global configurations & topic banks
├── auto_runner.py             # Daemon scheduler and buffer manager
├── setup.sh                   # Automated one-click setup script
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
│
├── accounts/                  # Multi-account profiles (JSON)
│   ├── account_manager.py     # Loader and account validator
│   ├── psychology_mindset.json# Example account 1
│   ├── storytelling.json      # Example account 2
│   └── comic_viral.json       # Example account 3
│
├── brain/                     # Script generation, topics, and buffer
│   ├── script_generator.py    # LLM script creator
│   ├── topic_selector.py      # Topic generator
│   └── knowledge_vault.py     # Offline fallback bank
│
├── media/                     # Audio, visual, and rendering pipeline
│   ├── tts_engine.py          # Edge-TTS voice synthesis
│   ├── image_gen.py           # AI image generator
│   ├── broll_manager.py       # B-roll footage engine
│   └── video_assembler.py     # Pillow + FFmpeg video builder
│
├── avatar/                    # Character & animated scene composers
├── content_types/             # Long video builder & Reel cutter
├── publisher/                 # Facebook Graph API & YouTube OAuth2
├── guardrail/                 # Content quality and safety filter
├── scheduler/                 # APScheduler cron jobs
└── dashboard/                 # Rich CLI terminal monitor
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.10+**
- **FFmpeg 6.0+**
- **Ollama** with `llama3.1:8b` model pulled

```bash
# Install Ollama & pull model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/<your-username>/custom-harness.git
cd custom-harness

# Run automated setup
chmod +x setup.sh
./setup.sh
```

Or manually set up a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Credentials

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your API tokens (Facebook page access tokens, YouTube OAuth secrets, etc.):
```ini
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
PUBLISH_FACEBOOK=false  # Set to true when ready to publish live
PUBLISH_YOUTUBE=false

# Account Facebook Page Tokens (optional)
FB_PAGE_ID_PSYCHOLOGY=your_facebook_page_id
FB_TOKEN_PSYCHOLOGY=your_facebook_page_access_token
```

---

## 💻 Usage

### Generate a Single Video (Test Mode)
Test generation without uploading:
```bash
python main.py --test
```

### Run Generation & Publish Cycle
Run one cycle for all enabled accounts:
```bash
python main.py
```

### Prebake Video Buffer
Pre-render 2 videos per account in the background:
```bash
python main.py --prebake
```

### Run as Background Daemon
Run auto-scheduler with automated cron publishing:
```bash
python main.py --daemon
# Or use runner scripts
./start_runner.sh
./status_runner.sh
./stop_runner.sh
```

### CLI Dashboard
Monitor your accounts and video buffer:
```bash
python dashboard/cli.py status
python dashboard/cli.py buffer
```

---

## ⚙️ Account Customization

You can add or modify accounts by creating a JSON file in `accounts/<account_name>.json`:

```json
{
  "id": "my_account",
  "name": "My Channel Name",
  "niche": "Tech & AI",
  "content_types": ["short_reel"],
  "schedule": {
    "short_reel": ["09:00", "15:00", "21:00"]
  },
  "visual_style": "cinematic",
  "subtitle_style": "hormozi_yellow",
  "bgm_style": "ambient_cinematic",
  "tts_voice": "en-US-GuyNeural",
  "enabled": true
}
```

---

## 🔒 Security Best Practices

- **Never commit `.env`:** Keep your API keys and access tokens strictly in `.env`.
- **Pre-configured `.gitignore`:** Ignores local databases, output videos, caches, and token files by default.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
