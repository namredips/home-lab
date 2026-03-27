#!/usr/bin/env python3
"""
Generate Mimir Discord icon and banner via Replicate.

Usage:
    REPLICATE_API_TOKEN=your_token uv run --with replicate --with pillow --with requests \
      python3 scripts/generate_mimir_assets.py
"""

import os
import sys
import time
from io import BytesIO
from pathlib import Path

import replicate
import requests
from PIL import Image

ICON_PROMPT = (
    "Mimir Norse god of wisdom, ancient wise face with flowing silver beard, "
    "glowing runic waters of the Well of Wisdom reflected in all-knowing eyes, "
    "Yggdrasil roots framing, deep blue and silver ethereal light, "
    "Norse mythology art style, profound and ancient, circular icon format, "
    "4K quality, detailed, mythological, luminous runes"
)

BANNER_PROMPT = (
    "Mímisbrunnr the Well of Wisdom deep beneath the roots of Yggdrasil, "
    "ancient carved stone well filled with glowing blue-silver runic water, "
    "enormous gnarled World Tree roots descending from above into darkness, "
    "Norse runes carved into stone glowing with inner light, mist rising from "
    "the water surface, profound stillness and ancient power, cinematic wide "
    "Norse mythological landscape, detailed"
)


def generate(prompt: str, aspect: str, size: tuple, out_path: Path) -> bool:
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "aspect_ratio": aspect,
                "output_format": "png",
                "output_quality": 100,
                "num_outputs": 1,
            },
        )
        if not output:
            print(f"  No output received for {out_path.name}")
            return False

        resp = requests.get(str(output[0]))
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        img = img.resize(size, Image.Resampling.LANCZOS)
        img.save(out_path, format="PNG")
        print(f"  Saved: {out_path} ({out_path.stat().st_size // 1024}KB)")
        return True

    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def main():
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("Error: REPLICATE_API_TOKEN not set")
        sys.exit(1)

    Path("assets/ai_icons").mkdir(parents=True, exist_ok=True)
    Path("assets/ai_app_icons").mkdir(parents=True, exist_ok=True)
    Path("assets/banners").mkdir(parents=True, exist_ok=True)

    print("Generating Mimir icon (512x512)...")
    icon_path = Path("assets/ai_icons/mimir.png")
    ok = generate(ICON_PROMPT, "1:1", (512, 512), icon_path)
    if ok:
        # Copy to app_icons
        Image.open(icon_path).save(Path("assets/ai_app_icons/mimir.png"))
        print("  Copied to assets/ai_app_icons/mimir.png")

    print("\nWaiting 12s for rate limit...")
    time.sleep(12)

    print("Generating Mimir banner (960x540)...")
    generate(BANNER_PROMPT, "16:9", (960, 540), Path("assets/banners/mimir.png"))

    print("\nDone. Estimated cost: ~$0.006")


if __name__ == "__main__":
    main()
