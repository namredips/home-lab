#!/usr/bin/env python3
"""
Discord App Icon Generator

Generates simpler, bolder app icons optimized for small display sizes.
These are designed to be uploaded to the Discord Developer Portal.

Usage:
    .env/bin/python scripts/discord_app_icons.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple
import math

# Icon specifications
ICON_SIZE = 512
SYMBOL_SIZE = int(ICON_SIZE * 0.55)  # Larger symbol for app icons (55%)

# App icon configurations (simpler, bolder designs)
APP_ICON_CONFIGS = {
    "zeus": {
        "symbol": "lightning_bold",
        "color": "#FFD700",
        "name": "Zeus"
    },
    "athena": {
        "symbol": "owl_bold",
        "color": "#5B7FA5",
        "name": "Athena"
    },
    "apollo": {
        "symbol": "sun_bold",
        "color": "#FF8C00",
        "name": "Apollo"
    },
    "artemis": {
        "symbol": "moon_bold",
        "color": "#708090",
        "name": "Artemis"
    },
    "hermes": {
        "symbol": "wing_bold",
        "color": "#2ECC71",
        "name": "Hermes"
    },
    "perseus": {
        "symbol": "shield_bold",
        "color": "#4682B4",
        "name": "Perseus"
    },
    "prometheus": {
        "symbol": "flame_bold",
        "color": "#E74C3C",
        "name": "Prometheus"
    },
    "ares": {
        "symbol": "sword_bold",
        "color": "#8B0000",
        "name": "Ares"
    },
    "freya_falcon": {
        "symbol": "falcon_bold",
        "color": "#95A5A6",
        "name": "Freya"
    },
    "freya_necklace": {
        "symbol": "necklace_bold",
        "color": "#95A5A6",
        "name": "Freya"
    }
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_lightning_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold lightning bolt."""
    w = size // 3
    h = size
    points = [
        (cx, cy - h//2),
        (cx + w//2, cy - h//8),
        (cx + w//3, cy + h//8),
        (cx + w, cy + h//2),
        (cx, cy + h//4),
        (cx - w//4, cy - h//4),
    ]
    draw.polygon(points, fill="white")


def draw_owl_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold, simplified owl."""
    # Body
    body_r = size // 2
    draw.ellipse([cx - body_r, cy - body_r//2, cx + body_r, cy + body_r], fill="white")

    # Large eyes
    eye_r = size // 6
    eye_spacing = size // 3
    # Left eye
    draw.ellipse([cx - eye_spacing - eye_r, cy - size//4 - eye_r,
                  cx - eye_spacing + eye_r, cy - size//4 + eye_r], fill="#2C3E50")
    # Right eye
    draw.ellipse([cx + eye_spacing - eye_r, cy - size//4 - eye_r,
                  cx + eye_spacing + eye_r, cy - size//4 + eye_r], fill="#2C3E50")

    # Beak
    beak_size = size // 5
    beak = [
        (cx, cy),
        (cx - beak_size//2, cy + beak_size),
        (cx + beak_size//2, cy + beak_size)
    ]
    draw.polygon(beak, fill="#E67E22")


def draw_sun_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold sun."""
    # Central circle
    circle_r = size // 3
    draw.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r], fill="white")

    # Bold rays (8 rays)
    ray_length = size // 2
    ray_width = size // 8
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        start_x = cx + int(circle_r * 1.1 * math.cos(rad))
        start_y = cy + int(circle_r * 1.1 * math.sin(rad))
        end_x = cx + int(ray_length * math.cos(rad))
        end_y = cy + int(ray_length * math.sin(rad))
        draw.line([start_x, start_y, end_x, end_y], fill="white", width=ray_width)


def draw_moon_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold crescent moon."""
    outer_r = size // 2
    inner_r = int(size // 2.3)
    offset = size // 6

    # Outer circle
    draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], fill="white")
    # Inner circle (cuts out the crescent)
    draw.ellipse([cx - inner_r + offset, cy - inner_r,
                  cx + inner_r + offset, cy + inner_r], fill=hex_to_rgb("#708090"))


def draw_wing_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold stylized wing."""
    # Wing shape (simplified feathered wing)
    wing_points = [
        (cx - size//3, cy),
        (cx - size//4, cy - size//3),
        (cx, cy - size//2),
        (cx + size//4, cy - size//3),
        (cx + size//2, cy),
        (cx + size//3, cy + size//4),
        (cx, cy + size//3),
        (cx - size//4, cy + size//4)
    ]
    draw.polygon(wing_points, fill="white")


def draw_shield_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold shield."""
    # Classic heater shield shape
    shield_points = [
        (cx, cy - size//2),  # Top point
        (cx + size//3, cy - size//2),  # Top right
        (cx + size//3, cy + size//4),  # Right side
        (cx, cy + size//2),  # Bottom point
        (cx - size//3, cy + size//4),  # Left side
        (cx - size//3, cy - size//2),  # Top left
    ]
    draw.polygon(shield_points, fill="white")

    # Center emblem (cross)
    cross_w = size // 12
    cross_h = size // 3
    draw.rectangle([cx - cross_w, cy - cross_h, cx + cross_w, cy + cross_h], fill="#2C3E50")
    draw.rectangle([cx - cross_h//2, cy - cross_w, cx + cross_h//2, cy + cross_w], fill="#2C3E50")


def draw_flame_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold flame."""
    # Outer flame
    outer_flame = [
        (cx, cy - size//2),
        (cx + size//3, cy - size//4),
        (cx + size//4, cy + size//4),
        (cx, cy + size//2),
        (cx - size//4, cy + size//4),
        (cx - size//3, cy - size//4),
    ]
    draw.polygon(outer_flame, fill="white")

    # Inner flame (orange)
    inner_flame = [
        (cx, cy - size//3),
        (cx + size//6, cy),
        (cx, cy + size//3),
        (cx - size//6, cy),
    ]
    draw.polygon(inner_flame, fill="#FFA500")


def draw_sword_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold sword pointing up."""
    blade_w = size // 6
    blade_h = int(size * 0.7)

    # Blade
    draw.rectangle([cx - blade_w//2, cy - size//2, cx + blade_w//2, cy + size//4], fill="white")

    # Point
    point = [
        (cx - blade_w//2, cy - size//2),
        (cx, cy - size//2 - blade_w),
        (cx + blade_w//2, cy - size//2)
    ]
    draw.polygon(point, fill="white")

    # Crossguard
    guard_w = size // 2
    guard_h = size // 10
    draw.rectangle([cx - guard_w//2, cy + size//4 - guard_h//2,
                   cx + guard_w//2, cy + size//4 + guard_h//2], fill="#E67E22")

    # Handle
    handle_w = blade_w
    handle_h = size // 4
    draw.rectangle([cx - handle_w//2, cy + size//4,
                   cx + handle_w//2, cy + size//4 + handle_h], fill="#8B4513")

    # Pommel
    pommel_r = blade_w
    draw.ellipse([cx - pommel_r, cy + size//4 + handle_h - pommel_r//2,
                 cx + pommel_r, cy + size//4 + handle_h + pommel_r//2], fill="#E67E22")


def draw_falcon_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw a bold falcon in flight."""
    # Body
    body_h = size // 3
    body_w = size // 4
    draw.ellipse([cx - body_w//2, cy - body_h//2, cx + body_w//2, cy + body_h//2], fill="white")

    # Head
    head_r = size // 6
    draw.ellipse([cx - head_r, cy - size//2, cx + head_r, cy - size//2 + head_r*2], fill="white")

    # Beak
    beak = [
        (cx + head_r//2, cy - size//2 + head_r),
        (cx + head_r + size//12, cy - size//2 + head_r - size//20),
        (cx + head_r + size//12, cy - size//2 + head_r + size//20)
    ]
    draw.polygon(beak, fill="#E67E22")

    # Wings (spread wide)
    # Left wing
    left_wing = [
        (cx - body_w//2, cy),
        (cx - size//2, cy - size//4),
        (cx - size//2 - size//8, cy),
        (cx - size//3, cy + size//6)
    ]
    draw.polygon(left_wing, fill="white")

    # Right wing
    right_wing = [
        (cx + body_w//2, cy),
        (cx + size//2, cy - size//4),
        (cx + size//2 + size//8, cy),
        (cx + size//3, cy + size//6)
    ]
    draw.polygon(right_wing, fill="white")

    # Tail feathers
    tail = [
        (cx - body_w//4, cy + body_h//2),
        (cx, cy + size//2),
        (cx + body_w//4, cy + body_h//2)
    ]
    draw.polygon(tail, fill="white")


def draw_necklace_bold(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int):
    """Draw Brísingamen necklace (bold design)."""
    # Necklace chain (arc)
    chain_r = size // 2
    chain_thickness = size // 15

    # Draw arc segments for chain
    for angle in range(30, 151, 15):  # Top arc from 30 to 150 degrees
        rad1 = math.radians(angle)
        rad2 = math.radians(angle + 10)
        x1 = cx + int(chain_r * math.cos(rad1))
        y1 = cy + int(chain_r * math.sin(rad1))
        x2 = cx + int(chain_r * math.cos(rad2))
        y2 = cy + int(chain_r * math.sin(rad2))
        draw.line([x1, y1, x2, y2], fill="white", width=chain_thickness)

    # Central pendant (ornate gem)
    pendant_w = size // 3
    pendant_h = size // 4

    # Gem shape (hexagonal)
    gem_points = [
        (cx, cy - pendant_h//2),
        (cx + pendant_w//2, cy - pendant_h//4),
        (cx + pendant_w//2, cy + pendant_h//4),
        (cx, cy + pendant_h//2),
        (cx - pendant_w//2, cy + pendant_h//4),
        (cx - pendant_w//2, cy - pendant_h//4),
    ]
    draw.polygon(gem_points, fill="white")

    # Inner gem detail (golden color)
    inner_gem = [
        (cx, cy - pendant_h//3),
        (cx + pendant_w//3, cy - pendant_h//6),
        (cx + pendant_w//3, cy + pendant_h//6),
        (cx, cy + pendant_h//3),
        (cx - pendant_w//3, cy + pendant_h//6),
        (cx - pendant_w//3, cy - pendant_h//6),
    ]
    draw.polygon(inner_gem, fill="#FFD700")

    # Side gems (smaller)
    side_gem_r = size // 12
    # Left gem
    draw.ellipse([cx - chain_r//2 - side_gem_r, cy - chain_r//3 - side_gem_r,
                  cx - chain_r//2 + side_gem_r, cy - chain_r//3 + side_gem_r], fill="#FFD700")
    # Right gem
    draw.ellipse([cx + chain_r//2 - side_gem_r, cy - chain_r//3 - side_gem_r,
                  cx + chain_r//2 + side_gem_r, cy - chain_r//3 + side_gem_r], fill="#FFD700")


def generate_app_icon(config: dict, output_path: Path):
    """Generate a single app icon."""
    # Create image with transparent background
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw colored circular background
    bg_color = hex_to_rgb(config["color"])
    draw.ellipse([0, 0, ICON_SIZE, ICON_SIZE], fill=bg_color)

    # Draw symbol (centered, no text for app icons - text is too small)
    center_x, center_y = ICON_SIZE // 2, ICON_SIZE // 2

    symbol_func = {
        "lightning_bold": draw_lightning_bold,
        "owl_bold": draw_owl_bold,
        "sun_bold": draw_sun_bold,
        "moon_bold": draw_moon_bold,
        "wing_bold": draw_wing_bold,
        "shield_bold": draw_shield_bold,
        "flame_bold": draw_flame_bold,
        "sword_bold": draw_sword_bold,
        "falcon_bold": draw_falcon_bold,
        "necklace_bold": draw_necklace_bold
    }[config["symbol"]]

    symbol_func(draw, center_x, center_y, SYMBOL_SIZE)

    # Save to file
    img.save(output_path, format='PNG')
    print(f"✅ Generated: {output_path.name}")


def main():
    """Main execution function."""
    print("🎨 Discord App Icon Generator")
    print("=" * 50)

    # Create output directory
    output_dir = Path("assets/app_icons")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all app icons
    print("\n🎨 Generating app-specific icons (bold, simple designs)...")
    for icon_name, config in APP_ICON_CONFIGS.items():
        output_path = output_dir / f"{icon_name}.png"
        generate_app_icon(config, output_path)

    print("\n" + "=" * 50)
    print(f"✅ Generated {len(APP_ICON_CONFIGS)} app icons")
    print(f"📁 Icons saved to: {output_dir}")
    print("\n📝 Next steps:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select each bot application")
    print("3. Under 'General Information', upload the corresponding app icon")
    print("4. Save changes")
    print("\n💡 For Freya, you have two options:")
    print("   - freya_falcon.png (falcon in flight)")
    print("   - freya_necklace.png (Brísingamen necklace)")


if __name__ == "__main__":
    main()
