#!/usr/bin/env python3
"""
Discord AI Icon Generator using Replicate

Generates professional mythological-themed icons for Discord bots using AI.
Uses Replicate API with FLUX or Stable Diffusion models.

Usage:
    REPLICATE_API_TOKEN=your_token .env/bin/python scripts/discord_ai_icons.py
"""

import os
import sys
from pathlib import Path
from typing import Dict
import replicate
import requests
from PIL import Image
from io import BytesIO

# Icon configurations with AI prompts
ICON_PROMPTS = {
    "zeus": {
        "name": "Zeus",
        "prompt": "Majestic Zeus Greek god portrait, holding golden lightning bolt, regal and powerful, white beard, laurel crown, classical Greek art style, dramatic storm clouds, lightning in background, circular icon format, 4K quality, detailed, mythological, epic",
        "color": "gold and stormy blue"
    },
    "athena": {
        "name": "Athena",
        "prompt": "Athena Greek goddess of wisdom, beautiful warrior goddess, golden armor, wise owl perched nearby, aegis shield, classical Greek art style, intelligent eyes, circular icon format, 4K quality, detailed, mythological, dignified",
        "color": "gold and blue"
    },
    "apollo": {
        "name": "Apollo",
        "prompt": "Apollo Greek god of sun and music, handsome youthful god, golden lyre, sun rays radiating, laurel crown, classical Greek art style, radiant and artistic, circular icon format, 4K quality, detailed, mythological, luminous",
        "color": "golden and warm orange"
    },
    "artemis": {
        "name": "Artemis",
        "prompt": "Artemis Greek goddess of the hunt, beautiful huntress, silver bow and arrow, crescent moon above, deer companion, classical Greek art style, fierce and graceful, circular icon format, 4K quality, detailed, mythological, moonlit",
        "color": "silver and midnight blue"
    },
    "hermes": {
        "name": "Hermes",
        "prompt": "Hermes Greek messenger god, winged sandals, caduceus staff with serpents, winged helmet, swift and clever, classical Greek art style, dynamic pose, circular icon format, 4K quality, detailed, mythological, energetic",
        "color": "emerald and gold"
    },
    "perseus": {
        "name": "Perseus",
        "prompt": "Perseus Greek hero, heroic warrior, winged sandals, reflective shield showing Medusa, sword of justice, classical Greek art style, brave and noble, circular icon format, 4K quality, detailed, mythological, heroic",
        "color": "steel blue and bronze"
    },
    "prometheus": {
        "name": "Prometheus",
        "prompt": "Prometheus Greek Titan, holding sacred flame, torch with bright fire, wise and defiant, classical Greek art style, fire illuminating face, circular icon format, 4K quality, detailed, mythological, dramatic lighting",
        "color": "red-orange and gold"
    },
    "ares": {
        "name": "Ares",
        "prompt": "Ares Greek god of war, fierce warrior god, battle armor, crossed swords, war helmet, classical Greek art style, intense and aggressive, circular icon format, 4K quality, detailed, mythological, battle-ready",
        "color": "dark red and bronze"
    },
    "freya": {
        "name": "Freya",
        "prompt": "Freya Norse goddess, beautiful and powerful, falcon feather cloak, Brisingamen necklace, magical and regal, cats at her side, Norse mythology art style, warrior goddess of love, circular icon format, 4K quality, detailed, mythological, enchanting",
        "color": "gold and silver"
    },
}

SERVER_PROMPT = {
    "name": "Mount Olympus",
    "prompt": "Mount Olympus Greek mythological mountain, majestic temple with marble columns, home of the gods, clouds and divine light, classical Greek architecture, epic and grand, circular icon format, 4K quality, detailed, mythological, heavenly",
    "color": "white marble and purple sky"
}


def generate_image(prompt: str, api_token: str, output_path: Path) -> bool:
    """Generate an image using Replicate API."""
    try:
        # Use FLUX-schnell for fast, high-quality generation
        # Alternative: black-forest-labs/flux-1.1-pro for even better quality
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "aspect_ratio": "1:1",  # Square for Discord icons
                "output_format": "png",
                "output_quality": 100,
                "num_outputs": 1
            }
        )

        # Download the generated image
        if output and len(output) > 0:
            image_url = output[0]
            response = requests.get(image_url)
            response.raise_for_status()

            # Open and resize to 512x512 (Discord's preferred size)
            img = Image.open(BytesIO(response.content))
            img = img.resize((512, 512), Image.Resampling.LANCZOS)

            # Save as PNG
            img.save(output_path, format='PNG', quality=95)
            print(f"✅ Generated: {output_path.name}")
            return True
        else:
            print(f"❌ No output received for {output_path.name}")
            return False

    except Exception as e:
        print(f"❌ Failed to generate {output_path.name}: {e}")
        return False


def main():
    """Main execution function."""
    print("🎨 AI-Powered Discord Icon Generator (Replicate)")
    print("=" * 60)

    # Get API token from environment
    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        print("❌ Error: REPLICATE_API_TOKEN environment variable not set")
        print("\nUsage:")
        print("  export REPLICATE_API_TOKEN='your_token'")
        print("  .env/bin/python scripts/discord_ai_icons.py")
        sys.exit(1)

    # Set token for replicate client
    os.environ["REPLICATE_API_TOKEN"] = api_token

    # Create output directories
    avatar_dir = Path("assets/ai_icons")
    avatar_dir.mkdir(parents=True, exist_ok=True)

    app_dir = Path("assets/ai_app_icons")
    app_dir.mkdir(parents=True, exist_ok=True)

    # Generate bot avatars
    print("\n🎨 Generating AI bot avatars...")
    print("   (Using FLUX model for high quality)\n")

    success_count = 0
    total_count = len(ICON_PROMPTS) + 1

    for bot_name, config in ICON_PROMPTS.items():
        print(f"🖼️  Generating {config['name']}...")
        print(f"   Prompt: {config['prompt'][:80]}...")

        avatar_path = avatar_dir / f"{bot_name}.png"
        if generate_image(config["prompt"], api_token, avatar_path):
            success_count += 1

            # Also save to app_icons directory (same image works for both)
            app_path = app_dir / f"{bot_name}.png"
            Image.open(avatar_path).save(app_path)

        print()  # Blank line for readability

    # Generate server icon
    print(f"🖼️  Generating {SERVER_PROMPT['name']}...")
    print(f"   Prompt: {SERVER_PROMPT['prompt'][:80]}...")

    server_path = avatar_dir / "mount_olympus.png"
    if generate_image(SERVER_PROMPT["prompt"], api_token, server_path):
        success_count += 1
        app_path = app_dir / "mount_olympus.png"
        Image.open(server_path).save(app_path)

    print()

    # Summary
    print("=" * 60)
    print(f"✅ Successfully generated: {success_count}/{total_count}")
    print(f"📁 AI Avatars saved to: {avatar_dir}")
    print(f"📁 AI App Icons saved to: {app_dir}")

    if success_count == total_count:
        print("\n🎉 All icons generated successfully!")
        print("\n📝 Next steps:")
        print("1. Review the generated icons")
        print("2. Upload bot avatars via API (run discord_avatars.py)")
        print("3. Upload app icons to Discord Developer Portal")
    else:
        print(f"\n⚠️  {total_count - success_count} icons failed to generate")

    # Cost estimate
    cost_estimate = total_count * 0.003  # ~$0.003 per FLUX-schnell image
    print(f"\n💰 Estimated cost: ~${cost_estimate:.2f}")


if __name__ == "__main__":
    main()
