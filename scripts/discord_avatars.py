#!/usr/bin/env python3
"""
Discord Bot & Server Icon Generator

Generates distinctive icons for Mount Olympus Discord server and all mythological bots,
then uploads them via Discord API.

Usage:
    .env/bin/python scripts/discord_avatars.py
"""

import base64
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

# Discord API Configuration
DISCORD_API_BASE = "https://discord.com/api/v10"
GUILD_ID = "832250938571227217"

# Icon specifications
ICON_SIZE = 512
BACKGROUND_RADIUS = ICON_SIZE // 2
SYMBOL_SIZE = int(ICON_SIZE * 0.4)  # Symbol occupies 40% of icon
TEXT_Y_OFFSET = int(ICON_SIZE * 0.75)  # Text starts at 75% down

# Bot icon configurations
BOT_CONFIGS = {
    "zeus": {
        "symbol": "lightning",
        "color": "#FFD700",  # Gold
        "name": "Zeus"
    },
    "athena": {
        "symbol": "owl",
        "color": "#5B7FA5",  # Blue-gray
        "name": "Athena"
    },
    "apollo": {
        "symbol": "sun",
        "color": "#FF8C00",  # Warm orange
        "name": "Apollo"
    },
    "artemis": {
        "symbol": "moon_arrow",
        "color": "#708090",  # Silver
        "name": "Artemis"
    },
    "hermes": {
        "symbol": "sandal",
        "color": "#2ECC71",  # Emerald
        "name": "Hermes"
    },
    "perseus": {
        "symbol": "sword_shield",
        "color": "#4682B4",  # Steel blue
        "name": "Perseus"
    },
    "prometheus": {
        "symbol": "flame",
        "color": "#E74C3C",  # Red-orange
        "name": "Prometheus"
    },
    "ares": {
        "symbol": "crossed_swords",
        "color": "#8B0000",  # Dark red
        "name": "Ares"
    },
    "freya": {
        "symbol": "cat",
        "color": "#95A5A6",  # Cool gray
        "name": "Freya"
    }
}

SERVER_CONFIG = {
    "symbol": "temple",
    "color": "#2C1654",  # Deep purple
    "name": "Mount Olympus"
}


def get_vault_tokens() -> Dict[str, str]:
    """Extract Discord bot tokens from Ansible Vault using ansible localhost."""
    vault_pass = Path.home() / ".vault_pass.txt"
    inventory_path = Path.home() / "workspace/infiquetra/home-lab/ansible/inventory/hosts.yml"

    if not vault_pass.exists():
        print(f"❌ Vault password file not found: {vault_pass}")
        sys.exit(1)

    tokens = {}

    # Use ansible to decrypt and print each token
    for bot_name in BOT_CONFIGS.keys():
        token_var = f"vault_discord_bot_token_{bot_name}"

        try:
            # Use ansible to decrypt the variable
            result = subprocess.run(
                [
                    "ansible", "localhost",
                    "-i", str(inventory_path),
                    "-m", "debug",
                    "-a", f"var={token_var}",
                    "--vault-password-file", str(vault_pass)
                ],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.home() / "workspace/infiquetra/home-lab"
            )

            # Parse JSON output from ansible
            # Format: localhost | SUCCESS => { "var_name": "value" }
            # JSON may span multiple lines
            if 'SUCCESS =>' in result.stdout:
                json_start = result.stdout.find('{')
                json_end = result.stdout.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_str = result.stdout[json_start:json_end+1]
                    try:
                        data = json.loads(json_str)
                        if token_var in data:
                            # Strip whitespace and newlines
                            token = data[token_var].strip()
                            if token:
                                tokens[bot_name] = token
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse JSON for {bot_name}: {e}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to decrypt token for {bot_name}: {e}")
            print(f"   STDERR: {e.stderr}")
            continue

    if not tokens:
        print("❌ No tokens could be decrypted!")
        sys.exit(1)

    return tokens


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_lightning(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a lightning bolt symbol."""
    points = [
        (center_x, center_y - size//2),
        (center_x + size//4, center_y - size//6),
        (center_x + size//6, center_y),
        (center_x + size//3, center_y + size//6),
        (center_x, center_y + size//2),
        (center_x - size//6, center_y + size//8),
        (center_x - size//8, center_y - size//8),
    ]
    draw.polygon(points, fill="white")


def draw_owl(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw an owl face symbol."""
    # Owl body (rounded rectangle)
    draw.ellipse([center_x - size//3, center_y - size//3, center_x + size//3, center_y + size//2], fill="white")

    # Eyes
    eye_radius = size // 8
    eye_y = center_y - size // 6
    draw.ellipse([center_x - size//4 - eye_radius, eye_y - eye_radius,
                  center_x - size//4 + eye_radius, eye_y + eye_radius], fill="#2C3E50")
    draw.ellipse([center_x + size//4 - eye_radius, eye_y - eye_radius,
                  center_x + size//4 + eye_radius, eye_y + eye_radius], fill="#2C3E50")

    # Beak
    beak_points = [
        (center_x, center_y),
        (center_x - size//10, center_y + size//8),
        (center_x + size//10, center_y + size//8)
    ]
    draw.polygon(beak_points, fill="#E67E22")


def draw_sun(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a sun with rays symbol."""
    # Central circle
    circle_radius = size // 4
    draw.ellipse([center_x - circle_radius, center_y - circle_radius,
                  center_x + circle_radius, center_y + circle_radius], fill="white")

    # Rays
    for angle in range(0, 360, 45):
        import math
        rad = math.radians(angle)
        start_x = center_x + int(circle_radius * 1.2 * math.cos(rad))
        start_y = center_y + int(circle_radius * 1.2 * math.sin(rad))
        end_x = center_x + int(size//2 * math.cos(rad))
        end_y = center_y + int(size//2 * math.sin(rad))
        draw.line([start_x, start_y, end_x, end_y], fill="white", width=size//20)


def draw_moon_arrow(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a crescent moon with arrow symbol."""
    # Crescent moon (two overlapping circles)
    draw.ellipse([center_x - size//3, center_y - size//3,
                  center_x + size//6, center_y + size//3], fill="white")
    draw.ellipse([center_x - size//4, center_y - size//3,
                  center_x + size//4, center_y + size//3], fill=hex_to_rgb("#708090"))

    # Arrow
    arrow_y = center_y
    draw.line([center_x + size//6, arrow_y, center_x + size//2, arrow_y], fill="white", width=size//25)
    # Arrowhead
    draw.polygon([
        (center_x + size//2, arrow_y),
        (center_x + size//2 - size//10, arrow_y - size//15),
        (center_x + size//2 - size//10, arrow_y + size//15)
    ], fill="white")


def draw_sandal(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a winged sandal symbol."""
    # Sandal base
    draw.ellipse([center_x - size//3, center_y - size//6,
                  center_x + size//3, center_y + size//4], fill="white")

    # Wings (simplified)
    wing_points_left = [
        (center_x - size//3, center_y),
        (center_x - size//2, center_y - size//6),
        (center_x - size//4, center_y + size//12)
    ]
    wing_points_right = [
        (center_x + size//3, center_y),
        (center_x + size//2, center_y - size//6),
        (center_x + size//4, center_y + size//12)
    ]
    draw.polygon(wing_points_left, fill="white")
    draw.polygon(wing_points_right, fill="white")


def draw_sword_shield(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a sword and shield symbol."""
    # Shield (circle)
    shield_radius = size // 3
    draw.ellipse([center_x - shield_radius, center_y - shield_radius,
                  center_x + shield_radius, center_y + shield_radius], fill="white", outline="#2C3E50", width=size//30)

    # Sword (vertical line with crossguard and pommel)
    sword_x = center_x
    draw.line([sword_x, center_y - size//2, sword_x, center_y + size//2], fill="#34495E", width=size//20)
    # Crossguard
    draw.line([sword_x - size//6, center_y - size//4, sword_x + size//6, center_y - size//4],
              fill="#34495E", width=size//15)
    # Blade
    draw.polygon([
        (sword_x, center_y - size//2),
        (sword_x - size//30, center_y - size//4),
        (sword_x + size//30, center_y - size//4)
    ], fill="#BDC3C7")


def draw_flame(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a stylized flame symbol."""
    flame_points = [
        (center_x, center_y - size//2),
        (center_x + size//4, center_y - size//4),
        (center_x + size//6, center_y),
        (center_x + size//4, center_y + size//4),
        (center_x, center_y + size//2),
        (center_x - size//4, center_y + size//4),
        (center_x - size//6, center_y),
        (center_x - size//4, center_y - size//4),
    ]
    draw.polygon(flame_points, fill="white")

    # Inner flame detail
    inner_points = [
        (center_x, center_y - size//3),
        (center_x + size//8, center_y),
        (center_x, center_y + size//3),
        (center_x - size//8, center_y),
    ]
    draw.polygon(inner_points, fill="#E67E22")


def draw_crossed_swords(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw two crossed swords symbol."""
    import math

    # First sword (diagonal \)
    angle1 = math.radians(45)
    x1_start = center_x - int(size//2 * math.cos(angle1))
    y1_start = center_y - int(size//2 * math.sin(angle1))
    x1_end = center_x + int(size//2 * math.cos(angle1))
    y1_end = center_y + int(size//2 * math.sin(angle1))
    draw.line([x1_start, y1_start, x1_end, y1_end], fill="white", width=size//15)

    # Second sword (diagonal /)
    angle2 = math.radians(-45)
    x2_start = center_x - int(size//2 * math.cos(angle2))
    y2_start = center_y - int(size//2 * math.sin(angle2))
    x2_end = center_x + int(size//2 * math.cos(angle2))
    y2_end = center_y + int(size//2 * math.sin(angle2))
    draw.line([x2_start, y2_start, x2_end, y2_end], fill="white", width=size//15)


def draw_cat(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a sitting cat silhouette."""
    # Body
    draw.ellipse([center_x - size//4, center_y - size//6,
                  center_x + size//4, center_y + size//2], fill="white")

    # Head
    head_radius = size // 5
    draw.ellipse([center_x - head_radius, center_y - size//2,
                  center_x + head_radius, center_y - size//6], fill="white")

    # Ears (triangles)
    left_ear = [
        (center_x - head_radius, center_y - size//2),
        (center_x - head_radius - size//8, center_y - size//2 - size//6),
        (center_x - head_radius//2, center_y - size//2)
    ]
    right_ear = [
        (center_x + head_radius, center_y - size//2),
        (center_x + head_radius + size//8, center_y - size//2 - size//6),
        (center_x + head_radius//2, center_y - size//2)
    ]
    draw.polygon(left_ear, fill="white")
    draw.polygon(right_ear, fill="white")

    # Tail
    draw.ellipse([center_x + size//6, center_y + size//4,
                  center_x + size//2, center_y + size//2 + size//8], fill="white")


def draw_temple(draw: ImageDraw.ImageDraw, center_x: int, center_y: int, size: int):
    """Draw a mountain with temple symbol."""
    # Mountain (triangle)
    mountain_points = [
        (center_x, center_y - size//3),
        (center_x - size//2, center_y + size//4),
        (center_x + size//2, center_y + size//4)
    ]
    draw.polygon(mountain_points, fill="white", outline="white")

    # Temple columns (simplified Parthenon)
    temple_width = size // 3
    temple_height = size // 4
    temple_y = center_y + size//4

    # Roof triangle
    roof_points = [
        (center_x, temple_y - temple_height),
        (center_x - temple_width//2, temple_y - temple_height//2),
        (center_x + temple_width//2, temple_y - temple_height//2)
    ]
    draw.polygon(roof_points, fill="#34495E")

    # Columns
    col_width = size // 30
    num_cols = 4
    col_spacing = temple_width // (num_cols + 1)
    for i in range(num_cols):
        col_x = center_x - temple_width//2 + (i + 1) * col_spacing
        draw.rectangle([col_x - col_width, temple_y - temple_height//2,
                       col_x + col_width, temple_y], fill="#34495E")


def generate_icon(config: dict, output_path: Path) -> BytesIO:
    """Generate a single icon based on configuration."""
    # Create image with transparent background
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw colored circular background
    bg_color = hex_to_rgb(config["color"])
    draw.ellipse([0, 0, ICON_SIZE, ICON_SIZE], fill=bg_color)

    # Draw symbol
    center_x, center_y = ICON_SIZE // 2, int(ICON_SIZE * 0.4)
    symbol_func = {
        "lightning": draw_lightning,
        "owl": draw_owl,
        "sun": draw_sun,
        "moon_arrow": draw_moon_arrow,
        "sandal": draw_sandal,
        "sword_shield": draw_sword_shield,
        "flame": draw_flame,
        "crossed_swords": draw_crossed_swords,
        "cat": draw_cat,
        "temple": draw_temple
    }[config["symbol"]]

    symbol_func(draw, center_x, center_y, SYMBOL_SIZE)

    # Add text label
    try:
        # Try to use a nice system font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=48)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    text = config["name"]
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (ICON_SIZE - text_width) // 2

    draw.text((text_x, TEXT_Y_OFFSET), text, fill="white", font=font)

    # Save to file
    img.save(output_path, format='PNG')
    print(f"✅ Generated: {output_path.name}")

    # Also return as BytesIO for upload
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


def upload_bot_avatar(bot_name: str, token: str, image_data: bytes) -> bool:
    """Upload avatar for a specific bot."""
    url = f"{DISCORD_API_BASE}/users/@me"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # Encode image as base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    data_uri = f"data:image/png;base64,{base64_image}"

    payload = {"avatar": data_uri}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✅ Uploaded avatar for {bot_name}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to upload avatar for {bot_name}: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False


def upload_server_icon(token: str, image_data: bytes) -> bool:
    """Upload server icon (requires admin token - using Freya's)."""
    url = f"{DISCORD_API_BASE}/guilds/{GUILD_ID}"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # Encode image as base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    data_uri = f"data:image/png;base64,{base64_image}"

    payload = {"icon": data_uri}

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"✅ Uploaded server icon")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to upload server icon: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False


def main():
    """Main execution function."""
    print("🎨 Discord Icon Generator")
    print("=" * 50)

    # Create output directory
    output_dir = Path("assets/icons")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get bot tokens from Ansible Vault
    print("\n🔐 Extracting bot tokens from Ansible Vault...")
    tokens = get_vault_tokens()
    print(f"   Found {len(tokens)} bot tokens")

    # Generate bot icons
    print("\n🎨 Generating bot icons...")
    bot_images = {}
    for bot_name, config in BOT_CONFIGS.items():
        output_path = output_dir / f"{bot_name}.png"
        image_buffer = generate_icon(config, output_path)
        bot_images[bot_name] = image_buffer.read()

    # Generate server icon
    print("\n🎨 Generating server icon...")
    server_output_path = output_dir / "mount_olympus.png"
    server_image_buffer = generate_icon(SERVER_CONFIG, server_output_path)
    server_image_data = server_image_buffer.read()

    # Upload bot avatars
    print("\n📤 Uploading bot avatars...")
    upload_success = 0
    upload_failed = 0

    for bot_name, image_data in bot_images.items():
        if bot_name in tokens:
            if upload_bot_avatar(bot_name, tokens[bot_name], image_data):
                upload_success += 1
            else:
                upload_failed += 1
        else:
            print(f"⚠️  Skipping {bot_name} - no token available")
            upload_failed += 1

    # Upload server icon (using Freya's token as admin)
    print("\n📤 Uploading server icon...")
    if "freya" in tokens:
        if upload_server_icon(tokens["freya"], server_image_data):
            upload_success += 1
        else:
            upload_failed += 1
    else:
        print("⚠️  Cannot upload server icon - Freya's token not available")
        upload_failed += 1

    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Successfully uploaded: {upload_success}")
    print(f"❌ Failed uploads: {upload_failed}")
    print(f"📁 Icons saved to: {output_dir}")
    print("\n🎉 Done! Check Discord to see the new icons.")


if __name__ == "__main__":
    main()
