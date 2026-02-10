#!/usr/bin/env python3
"""Retry failed icon generation"""
import os
import sys
from pathlib import Path
import replicate
import requests
from PIL import Image
from io import BytesIO

# Get API token from environment
if "REPLICATE_API_TOKEN" not in os.environ:
    print("❌ Error: REPLICATE_API_TOKEN environment variable not set")
    sys.exit(1)

RETRY_PROMPTS = {
    "zeus": "Majestic Zeus Greek god portrait, holding golden lightning bolt, regal and powerful, white beard, laurel crown, classical Greek art style, dramatic storm clouds, lightning in background, circular icon format, 4K quality, detailed, mythological, epic",
    "athena": "Athena Greek goddess of wisdom, beautiful warrior goddess, golden armor, wise owl perched nearby, aegis shield, classical Greek art style, intelligent eyes, circular icon format, 4K quality, detailed, mythological, dignified"
}

for bot_name, prompt in RETRY_PROMPTS.items():
    print(f"🖼️  Retrying {bot_name}...")
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={"prompt": prompt, "aspect_ratio": "1:1", "output_format": "png", "output_quality": 100, "num_outputs": 1}
        )
        if output and len(output) > 0:
            response = requests.get(output[0])
            img = Image.open(BytesIO(response.content)).resize((512, 512), Image.Resampling.LANCZOS)

            avatar_path = Path(f"assets/ai_icons/{bot_name}.png")
            app_path = Path(f"assets/ai_app_icons/{bot_name}.png")

            img.save(avatar_path, format='PNG', quality=95)
            img.save(app_path, format='PNG', quality=95)
            print(f"✅ Generated: {bot_name}.png")
    except Exception as e:
        print(f"❌ Failed: {e}")
