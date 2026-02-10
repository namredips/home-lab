#!/usr/bin/env python3
"""
Discord Server Setup Automation

Automates creation of roles, categories, channels, and permissions
for the OpenClaw agent team Discord server.

Usage:
    export DISCORD_BOT_TOKEN="your-bot-token"
    python scripts/discord_setup.py

Output:
    discord_config.json - Contains all created role/channel IDs
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
import requests

# Configuration
GUILD_ID = "832250938571227217"
API_BASE = "https://discord.com/api/v10"

# Role Definitions
ROLES = [
    {
        "name": "Human",
        "color": 0x3498db,  # Blue
        "permissions": "8",  # Administrator
        "hoist": True,
        "mentionable": True,
    },
    {
        "name": "Freya",
        "color": 0x95a5a6,  # Gray
        "permissions": "275415359552",  # Manage Channels, Manage Messages, Send Messages, etc.
        "hoist": False,
        "mentionable": True,
    },
    {
        "name": "Olympus",
        "color": 0x9b59b6,  # Purple
        "permissions": "274878295104",  # Standard bot permissions
        "hoist": True,
        "mentionable": True,
    },
    {
        "name": "Project: CAMPPS",
        "color": 0x2ecc71,  # Green
        "permissions": "0",  # Inherit from @everyone
        "hoist": False,
        "mentionable": True,
    },
    {
        "name": "Project: Mimir",
        "color": 0xe74c3c,  # Red
        "permissions": "0",
        "hoist": False,
        "mentionable": True,
    },
    {
        "name": "Project: JCE",
        "color": 0xf39c12,  # Orange
        "permissions": "0",
        "hoist": False,
        "mentionable": True,
    },
]

# Category and Channel Structure
STRUCTURE = {
    "GENERAL": {
        "channels": [
            {"name": "general", "topic": "Daily chatter and quick questions"},
            {"name": "agent-standups", "topic": "Async standup updates from all agents"},
            {"name": "random", "topic": "Non-work chat, finds, and fun"},
        ]
    },
    "AGENT COORDINATION": {
        "channels": [
            {"name": "agent-updates", "topic": "Heartbeats, completions, status reports"},
            {"name": "agent-handoffs", "topic": "Transfer work between agents"},
            {"name": "agent-sync", "topic": "Cross-agent discussion and shared learning"},
        ]
    },
    "PROJECTS": {
        "channels": [
            {"name": "campps-planning", "topic": "CAMPPS vision, roadmap, camp admin research", "project_role": "Project: CAMPPS"},
            {"name": "campps-dev", "topic": "CAMPPS code, architecture, database design", "project_role": "Project: CAMPPS"},
            {"name": "mimir-dev", "topic": "EVE Online assistant development", "project_role": "Project: Mimir"},
            {"name": "mimir-ops", "topic": "Fleet logs, market tracking, intel", "project_role": "Project: Mimir"},
            {"name": "jce-research", "topic": "Democracy, civic engagement research", "project_role": "Project: JCE"},
            {"name": "jce-content", "topic": "Essays, newsletters, publishing pipeline", "project_role": "Project: JCE"},
        ]
    },
    "COLLABORATION": {
        "channels": [
            {"name": "architecture", "topic": "System design discussions across all projects"},
            {"name": "research", "topic": "Deep dives, findings, resources"},
            {"name": "writing", "topic": "Draft review and editing"},
        ]
    },
    "TOOLS": {
        "channels": [
            {"name": "bot-commands", "topic": "Test commands and tooling"},
            {"name": "deployments", "topic": "Release coordination and deployments"},
        ]
    },
}


class DiscordSetup:
    """Handles Discord server setup via API"""

    def __init__(self, token: str, guild_id: str):
        self.token = token
        self.guild_id = guild_id
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
        }
        self.config: Dict[str, Any] = {
            "guild_id": guild_id,
            "roles": {},
            "categories": {},
            "channels": {},
        }

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make API request with rate limit handling"""
        url = f"{API_BASE}{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, json=data, timeout=10
            )

            # Handle rate limits
            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 1)
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                return self._request(method, endpoint, data)

            response.raise_for_status()
            return response.json() if response.content else None

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def get_current_state(self) -> Dict[str, Any]:
        """Query current server state"""
        print("\n=== Querying Current Server State ===")

        # Get guild info
        guild = self._request("GET", f"/guilds/{self.guild_id}")
        if guild:
            print(f"Guild: {guild.get('name')} (ID: {guild.get('id')})")

        # Get existing roles
        roles = self._request("GET", f"/guilds/{self.guild_id}/roles")
        existing_roles = {role["name"]: role for role in roles} if roles else {}
        print(f"Existing roles: {len(existing_roles)}")

        # Get existing channels
        channels = self._request("GET", f"/guilds/{self.guild_id}/channels")
        existing_channels = {ch["name"]: ch for ch in channels} if channels else {}
        print(f"Existing channels: {len(existing_channels)}")

        return {
            "guild": guild,
            "roles": existing_roles,
            "channels": existing_channels,
        }

    def create_roles(self, existing_roles: Dict[str, Any]) -> None:
        """Create required roles if they don't exist"""
        print("\n=== Creating Roles ===")

        for role_def in ROLES:
            role_name = role_def["name"]

            # Skip if role already exists
            if role_name in existing_roles:
                role = existing_roles[role_name]
                print(f"✓ Role '{role_name}' already exists (ID: {role['id']})")
                self.config["roles"][role_name] = role["id"]
                continue

            # Create new role
            payload = {
                "name": role_name,
                "color": role_def["color"],
                "permissions": role_def["permissions"],
                "hoist": role_def["hoist"],
                "mentionable": role_def["mentionable"],
            }

            result = self._request("POST", f"/guilds/{self.guild_id}/roles", payload)
            if result:
                print(f"✓ Created role '{role_name}' (ID: {result['id']})")
                self.config["roles"][role_name] = result["id"]
            else:
                print(f"✗ Failed to create role '{role_name}'")

    def create_categories_and_channels(self, existing_channels: Dict[str, Any]) -> None:
        """Create categories and channels"""
        print("\n=== Creating Categories and Channels ===")

        everyone_role_id = self._get_everyone_role_id()

        for category_name, category_data in STRUCTURE.items():
            # Create or get category
            category_id = self._create_category(category_name, existing_channels)
            if not category_id:
                print(f"✗ Failed to create category '{category_name}'")
                continue

            self.config["categories"][category_name] = category_id

            # Create channels in category
            for channel_def in category_data["channels"]:
                channel_name = channel_def["name"]

                # Skip if channel already exists
                if channel_name in existing_channels:
                    channel = existing_channels[channel_name]
                    print(f"  ✓ Channel '{channel_name}' already exists (ID: {channel['id']})")
                    self.config["channels"][channel_name] = channel["id"]
                    continue

                # Build permission overrides
                permission_overwrites = []

                # Project channels: restrict to project role
                if "project_role" in channel_def:
                    project_role = channel_def["project_role"]
                    project_role_id = self.config["roles"].get(project_role)

                    if project_role_id and everyone_role_id:
                        # Deny @everyone
                        permission_overwrites.append({
                            "id": everyone_role_id,
                            "type": 0,  # Role
                            "deny": "1024",  # VIEW_CHANNEL
                        })
                        # Allow project role
                        permission_overwrites.append({
                            "id": project_role_id,
                            "type": 0,
                            "allow": "3072",  # VIEW_CHANNEL + SEND_MESSAGES
                        })

                        # Allow Human role
                        human_role_id = self.config["roles"].get("Human")
                        if human_role_id:
                            permission_overwrites.append({
                                "id": human_role_id,
                                "type": 0,
                                "allow": "3072",
                            })

                # Create channel
                payload = {
                    "name": channel_name,
                    "type": 0,  # Text channel
                    "parent_id": category_id,
                    "topic": channel_def.get("topic", ""),
                    "permission_overwrites": permission_overwrites,
                }

                result = self._request("POST", f"/guilds/{self.guild_id}/channels", payload)
                if result:
                    print(f"  ✓ Created channel '{channel_name}' (ID: {result['id']})")
                    self.config["channels"][channel_name] = result["id"]
                else:
                    print(f"  ✗ Failed to create channel '{channel_name}'")

    def _create_category(self, name: str, existing_channels: Dict[str, Any]) -> Optional[str]:
        """Create a category channel"""
        # Check if category already exists
        if name in existing_channels:
            category = existing_channels[name]
            print(f"✓ Category '{name}' already exists (ID: {category['id']})")
            return category["id"]

        # Create new category
        payload = {
            "name": name,
            "type": 4,  # Category
        }

        result = self._request("POST", f"/guilds/{self.guild_id}/channels", payload)
        if result:
            print(f"✓ Created category '{name}' (ID: {result['id']})")
            return result["id"]
        else:
            return None

    def _get_everyone_role_id(self) -> Optional[str]:
        """Get the @everyone role ID (same as guild ID)"""
        return self.guild_id

    def save_config(self, filename: str = "discord_config.json") -> None:
        """Save configuration to JSON file"""
        with open(filename, "w") as f:
            json.dump(self.config, f, indent=2)
        print(f"\n=== Configuration saved to {filename} ===")


def main():
    """Main execution"""
    # Get bot token from environment
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set")
        print("\nUsage:")
        print("  export DISCORD_BOT_TOKEN='your-bot-token'")
        print("  python scripts/discord_setup.py")
        sys.exit(1)

    print("=== Discord Server Setup ===")
    print(f"Guild ID: {GUILD_ID}")
    print(f"API Base: {API_BASE}")

    # Initialize setup
    setup = DiscordSetup(token, GUILD_ID)

    # Get current state
    current_state = setup.get_current_state()
    if not current_state["guild"]:
        print("\nError: Failed to query guild. Check bot token and permissions.")
        sys.exit(1)

    # Create roles
    setup.create_roles(current_state["roles"])

    # Create categories and channels
    setup.create_categories_and_channels(current_state["channels"])

    # Save configuration
    setup.save_config()

    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Create 9 bot applications in Discord Developer Portal")
    print("2. Run Phase 3 to assign bot roles and nicknames")


if __name__ == "__main__":
    main()
