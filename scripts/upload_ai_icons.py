#!/usr/bin/env python3
"""
Upload AI-Generated Discord Icons

Uploads the AI-generated mythological icons to Discord bots and server.
"""

import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict

import requests

# Discord API Configuration
DISCORD_API_BASE = "https://discord.com/api/v10"
GUILD_ID = "832250938571227217"

# Bot list
BOTS = ["zeus", "athena", "apollo", "artemis", "hermes", "perseus", "prometheus", "ares", "freya"]


def get_vault_tokens() -> Dict[str, str]:
    """Extract Discord bot tokens from Ansible Vault."""
    vault_pass = Path.home() / ".vault_pass.txt"
    inventory_path = Path.home() / "workspace/infiquetra/home-lab/ansible/inventory/hosts.yml"

    if not vault_pass.exists():
        print(f"❌ Vault password file not found: {vault_pass}")
        sys.exit(1)

    tokens = {}

    for bot_name in BOTS:
        token_var = f"vault_discord_bot_token_{bot_name}"

        try:
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

            if 'SUCCESS =>' in result.stdout:
                json_start = result.stdout.find('{')
                json_end = result.stdout.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_str = result.stdout[json_start:json_end+1]
                    try:
                        data = json.loads(json_str)
                        if token_var in data:
                            token = data[token_var].strip()
                            if token:
                                tokens[bot_name] = token
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse JSON for {bot_name}: {e}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to decrypt token for {bot_name}")
            continue

    return tokens


def upload_bot_avatar(bot_name: str, token: str, image_path: Path) -> bool:
    """Upload avatar for a specific bot."""
    url = f"{DISCORD_API_BASE}/users/@me"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()

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


def upload_server_icon(token: str, image_path: Path) -> bool:
    """Upload server icon (using Freya's admin token)."""
    url = f"{DISCORD_API_BASE}/guilds/{GUILD_ID}"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()

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
    print("🚀 Uploading AI-Generated Icons to Discord")
    print("=" * 50)

    # Check if AI icons exist
    ai_icons_dir = Path("assets/ai_icons")
    if not ai_icons_dir.exists():
        print("❌ AI icons directory not found!")
        print("   Run discord_ai_icons.py first to generate icons")
        sys.exit(1)

    # Get bot tokens
    print("\n🔐 Extracting bot tokens from Ansible Vault...")
    tokens = get_vault_tokens()
    print(f"   Found {len(tokens)} bot tokens")

    # Upload bot avatars
    print("\n📤 Uploading bot avatars...")
    upload_success = 0
    upload_failed = 0

    for bot_name in BOTS:
        icon_path = ai_icons_dir / f"{bot_name}.png"

        if not icon_path.exists():
            print(f"⚠️  Icon not found: {icon_path}")
            upload_failed += 1
            continue

        if bot_name in tokens:
            if upload_bot_avatar(bot_name, tokens[bot_name], icon_path):
                upload_success += 1
            else:
                upload_failed += 1
        else:
            print(f"⚠️  Skipping {bot_name} - no token available")
            upload_failed += 1

    # Upload server icon
    print("\n📤 Uploading server icon...")
    server_icon_path = ai_icons_dir / "mount_olympus.png"

    if server_icon_path.exists() and "freya" in tokens:
        if upload_server_icon(tokens["freya"], server_icon_path):
            upload_success += 1
        else:
            upload_failed += 1
    else:
        print("⚠️  Cannot upload server icon - file or token missing")
        upload_failed += 1

    # Summary
    print("\n" + "=" * 50)
    print(f"✅ Successfully uploaded: {upload_success}")
    print(f"❌ Failed uploads: {upload_failed}")
    print("\n🎉 Done! Check Discord to see the new AI-generated icons!")


if __name__ == "__main__":
    main()
