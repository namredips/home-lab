#!/usr/bin/env python3
"""
Discord Bot Banner Generator using Replicate

Generates 960x540 landscape banners for each Discord bot, depicting their
mythological domain as an immersive environment.

Usage:
    REPLICATE_API_TOKEN=your_token uv run --with replicate --with pillow --with requests \
      python3 scripts/discord_banners.py
"""

import os
import sys
import time
from pathlib import Path

import replicate
import requests
from PIL import Image
from io import BytesIO

BANNER_PROMPTS = {
    "zeus": {
        "name": "Zeus",
        "prompt": "Throne room atop Mount Olympus, massive marble columns, storm clouds rolling far below, lightning arcing across a violet and gold sky, imposing golden throne in the center, eagle perched nearby, divine light streaming through clouds, epic wide landscape, classical Greek architecture, cinematic, detailed, mythological",
    },
    "athena": {
        "name": "Athena",
        "prompt": "Ancient Athenian library of wisdom, towering shelves packed with scrolls and clay tablets, an owl perched on a marble bust, warm golden oil lamp light, olive branches framing the scene, open window showing the Parthenon at dusk, dust motes in the air, cinematic wide shot, classical Greek setting, detailed, mythological",
    },
    "apollo": {
        "name": "Apollo",
        "prompt": "Temple of Delphi at sunrise, golden light pouring dramatically through marble columns, a golden lyre resting against the oracle's bronze tripod, sacred laurel trees framing the steps, sun cresting over distant mountains, morning mist in the valley below, cinematic wide landscape, classical Greek architecture, detailed, mythological",
    },
    "artemis": {
        "name": "Artemis",
        "prompt": "Moonlit ancient forest clearing, silver bow and quiver of arrows leaning against a massive gnarled oak tree, a deer drinking from a perfectly still silvery pool reflecting stars, crescent moon bright overhead through the canopy, fireflies in the undergrowth, ethereal and serene, cinematic wide landscape, detailed, mythological",
    },
    "hephaestus": {
        "name": "Hephaestus",
        "prompt": "Divine volcanic forge interior beneath Mount Etna, massive glowing anvil at the center with sparks flying, bronze automatons being assembled against the walls, rivers of molten metal, bellows pumping, hammers and tongs on every surface, volcanic fire and orange glow, steam and smoke, cinematic wide industrial mythological scene, detailed",
    },
    "perseus": {
        "name": "Perseus",
        "prompt": "Dramatic sea cliff edge overlooking a vast ancient Mediterranean ocean at night, winged sandals and a reflective polished shield resting on the rocks showing star reflections, the constellation of Perseus blazing in the dark sky above, crashing waves below, heroic atmosphere, cinematic wide landscape, detailed, mythological",
    },
    "prometheus": {
        "name": "Prometheus",
        "prompt": "Craggy mountain peak at twilight, a single defiant torch burning brightly against cold rock and chains, an eagle circling in the distant sky, fire from the torch illuminating darkness below in the valley, storm clouds gathering, dramatic contrast between light and shadow, cinematic wide landscape, detailed, mythological",
    },
    "ares": {
        "name": "Ares",
        "prompt": "Ancient battlefield at dawn, disciplined ranks of Spartan warriors in red and bronze armor carrying shields and spears, war banners snapping in the wind, dust rising from marching feet, morning light casting long shadows, mountains in the background, tense and powerful atmosphere, cinematic wide landscape, detailed, mythological",
    },
    "freya": {
        "name": "Freya",
        "prompt": "Norse great hall with massive golden oak pillars, a magnificent falcon perched on the arm of a carved wooden throne, the glowing Brisingamen necklace displayed on a velvet cushion, two grey cats sleeping by a roaring hearth, mead horns on long tables, carved runes on the walls, cinematic wide Norse mythological interior, detailed",
    },
    "hermes": {
        "name": "Hermes",
        "prompt": "Ancient crossroads at dusk where three worn stone paths meet, a caduceus staff planted upright in the center, winged sandals hovering mid-flight nearby, papyrus scrolls and messages drifting on the wind, travelers' offerings left at the roadside, golden hour light, mysterious and liminal atmosphere, cinematic wide landscape, detailed, mythological",
    },
}


def generate_banner(name: str, prompt: str, output_path: Path) -> bool:
    """Generate a 960x540 landscape banner via Replicate FLUX-schnell."""
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "output_format": "png",
                "output_quality": 100,
                "num_outputs": 1,
            },
        )

        if not output:
            print(f"  {name}: no output received")
            return False

        url = str(output[0])
        resp = requests.get(url)
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))
        img = img.resize((960, 540), Image.Resampling.LANCZOS)
        img.save(output_path, format="PNG")
        print(f"  {name}: saved ({output_path.stat().st_size // 1024}KB)")
        return True

    except Exception as e:
        print(f"  {name}: FAILED — {e}")
        return False


def main():
    print("Discord Banner Generator (Replicate FLUX-schnell)")
    print("=" * 55)

    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("Error: REPLICATE_API_TOKEN not set")
        sys.exit(1)

    out_dir = Path("assets/banners")
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i, (bot_name, config) in enumerate(BANNER_PROMPTS.items()):
        out_path = out_dir / f"{bot_name}.png"
        if out_path.exists():
            print(f"\n  {config['name']}: already exists, skipping")
            ok += 1
            continue
        print(f"\nGenerating {config['name']} ({i+1}/{len(BANNER_PROMPTS)})...")
        if generate_banner(config["name"], config["prompt"], out_path):
            ok += 1
        # Rate limit: free-tier Replicate allows 6 req/min burst=1
        if i < len(BANNER_PROMPTS) - 1:
            time.sleep(12)

    print(f"\n{'=' * 55}")
    print(f"Done: {ok}/{len(BANNER_PROMPTS)} banners generated")
    print(f"Saved to: {out_dir}/")
    print(f"Estimated cost: ~${len(BANNER_PROMPTS) * 0.003:.2f}")


if __name__ == "__main__":
    main()
