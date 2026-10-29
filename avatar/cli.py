#!/usr/bin/env python3
"""
Cartoon Avatar Video Generator — CLI

Usage examples:
  # Basic: character + script → video
  python -m avatar.cli --char assets/my_char.png --script "Hello everyone!"

  # With options
  python -m avatar.cli --char char.png --script "Today we learn robotics." \
         --bg classroom --emotion happy --shot medium --quality balanced

  # Provide audio instead of TTS
  python -m avatar.cli --char char.png --audio voice.mp3 --bg studio

  # Preview mode (4s clip)
  python -m avatar.cli --char char.png --script "Hello world!" --preview

  # Multiple backgrounds (same character, 3 scenes)
  python -m avatar.cli --char char.png --script "Hello!" \
         --bg classroom laboratory outdoor --scenes 3
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from avatar.avatar_pipeline import AvatarPipeline

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("avatar.cli")


def parse_args():
    p = argparse.ArgumentParser(
        description="Cartoon Avatar Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--char", required=True,
                   help="Path to character image (PNG/JPG/WebP)")
    p.add_argument("--script", default="",
                   help="Script text for TTS (use quotes)")
    p.add_argument("--audio", default=None,
                   help="Path to pre-recorded audio file (skips TTS)")
    p.add_argument("--bg", nargs="+", default=["studio"],
                   choices=["classroom", "laboratory", "outdoor", "studio",
                            "dark", "bright", "night"],
                   help="Background(s) to use")
    p.add_argument("--emotion",
                   choices=["neutral", "happy", "sad", "surprised",
                             "excited", "angry", "confused", "thinking"],
                   default="neutral")
    p.add_argument("--gesture",
                   choices=["idle", "wave", "point", "nod"],
                   default="idle")
    p.add_argument("--shot",
                   choices=["close_up", "medium", "full_body", "wide"],
                   default="medium")
    p.add_argument("--voice", default="en-US-GuyNeural",
                   help="Edge-TTS voice name")
    p.add_argument("--quality",
                   choices=["fast", "balanced", "quality"],
                   default="balanced")
    p.add_argument("--subtitle", action="store_true", default=True,
                   help="Burn subtitles (default: on)")
    p.add_argument("--no-subtitle", dest="subtitle", action="store_false")
    p.add_argument("--preview", action="store_true",
                   help="Generate a 4-second preview only")
    p.add_argument("--project", default=None,
                   help="Project name (default: derived from char filename)")
    p.add_argument("--out-dir", default="output/avatar_projects",
                   help="Output directory")
    return p.parse_args()


async def main():
    args = parse_args()

    # Validate character file
    char_path = Path(args.char)
    if not char_path.exists():
        logger.error(f"Character file not found: {char_path}")
        sys.exit(1)

    if not args.script and not args.audio:
        logger.error("Provide either --script or --audio")
        sys.exit(1)

    # Project name
    project_name = args.project or char_path.stem.replace(" ", "_")

    print(f"\n{'='*60}")
    print(f"  🎭 Cartoon Avatar Generator")
    print(f"{'='*60}")
    print(f"  Character : {char_path}")
    print(f"  Project   : {project_name}")
    print(f"  Background: {args.bg}")
    print(f"  Emotion   : {args.emotion}")
    print(f"  Quality   : {args.quality}")
    print(f"{'='*60}\n")

    pipeline = AvatarPipeline(project_name, output_dir=args.out_dir)

    # Load and prepare character
    print("📸 Preparing character...")
    profile = await pipeline.load_character(str(char_path))
    print(f"   Body type : {profile['body_type']}")
    print(f"   Size      : {profile['width']}×{profile['height']}")
    print(f"   Level     : Animation Level {profile['animation_level']}")
    print()

    outputs = []

    if args.preview:
        print("🎬 Generating preview (4s)...")
        path = await pipeline.generate_preview(
            script=args.script,
            background=args.bg[0],
            emotion=args.emotion,
            gesture=args.gesture,
            voice=args.voice,
            subtitle=args.subtitle,
            shot_type=args.shot,
            quality="fast",
            audio_path=args.audio,
        )
        outputs.append(path)

    else:
        for i, bg in enumerate(args.bg):
            print(f"🎬 Generating video {i+1}/{len(args.bg)} (bg={bg})...")
            fname = f"{project_name}_{bg}.mp4" if len(args.bg) > 1 else None
            path = await pipeline.generate_video(
                script=args.script,
                background=bg,
                emotion=args.emotion,
                gesture=args.gesture,
                voice=args.voice,
                subtitle=args.subtitle,
                shot_type=args.shot,
                quality=args.quality,
                output_filename=fname,
                audio_path=args.audio if i == 0 else None,
            )
            outputs.append(path)
            print(f"   ✅ Done: {path}\n")

    print(f"\n{'='*60}")
    print(f"  ✅ COMPLETE — {len(outputs)} video(s) generated")
    for o in outputs:
        size = Path(o).stat().st_size / 1024 / 1024
        print(f"  📹 {o}  ({size:.1f} MB)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
