#!/usr/bin/env python3
"""
Discord Phase 3: Bot Role Assignment and Nicknames

Assigns roles and sets nicknames for all OpenClaw agent bots.
"""

import os
import sys
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Configuration
GUILD_ID = "832250938571227217"
API_BASE = "https://discord.com/api/v10"

# Bot Application IDs from agent_info.txt
BOTS = {
    "Zeus": {"app_id": "1470606502179110912", "emoji": "⚡", "projects": ["Project: CAMPPS", "Project: Mimir", "Project: JCE"]},
    "Athena": {"app_id": "1470607465136787621", "emoji": "🦉", "projects": []},
    "Apollo": {"app_id": "1470608246669578423", "emoji": "☀️", "projects": []},
    "Artemis": {"app_id": "1470608455818543135", "emoji": "🎯", "projects": []},
    "Hermes": {"app_id": "1470608660714754102", "emoji": "🏃", "projects": []},
    "Perseus": {"app_id": "1470608832672829635", "emoji": "🗡️", "projects": []},
    "Prometheus": {"app_id": "1470609038008913930", "emoji": "🔥", "projects": []},
    "Ares": {"app_id": "1470609201771315220", "emoji": "⚔️", "projects": []},
}


class DiscordPhase3:
    """Phase 3: Assign roles and nicknames"""

    def __init__(self, token: str, guild_id: str):
        self.token = token
        self.guild_id = guild_id
        self.headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com/infiquetra/home-lab, 1.0)",
        }

    def _request(self, method: str, endpoint: str, data=None):
        """Make API request"""
        url = f"{API_BASE}{endpoint}"
        try:
            request_data = None
            if data is not None:
                request_data = json.dumps(data).encode('utf-8')

            req = Request(url, data=request_data, headers=self.headers, method=method)

            with urlopen(req, timeout=10) as response:
                response_data = response.read()
                if response_data:
                    return json.loads(response_data.decode('utf-8'))
                return None

        except HTTPError as e:
            if e.code == 429:
                error_data = json.loads(e.read().decode('utf-8'))
                retry_after = error_data.get("retry_after", 1)
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                return self._request(method, endpoint, data)

            print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
            return None

        except (URLError, Exception) as e:
            print(f"Request failed: {e}")
            return None

    def get_guild_members(self):
        """Get all guild members"""
        members = self._request("GET", f"/guilds/{self.guild_id}/members?limit=1000")
        return {m["user"]["id"]: m for m in members} if members else {}

    def load_config(self):
        """Load discord_config.json"""
        with open("discord_config.json", "r") as f:
            return json.load(f)

    def assign_roles(self):
        """Assign roles and nicknames to all bots"""
        print("\n=== Phase 3: Bot Role Assignment ===\n")

        # Load config
        config = self.load_config()
        olympus_role_id = config["roles"]["Olympus"]

        # Get all members
        members = self.get_guild_members()

        # Process each bot
        for bot_name, bot_info in BOTS.items():
            # Find member by username (case-insensitive)
            member_id = None
            for member in members.values():
                if member["user"].get("bot") and member["user"]["username"].lower() == bot_name.lower():
                    member_id = member["user"]["id"]
                    break

            if not member_id:
                print(f"⚠️  {bot_name}: Bot not found in server")
                continue

            print(f"=== {bot_name} (ID: {member_id}) ===")

            # Assign Olympus role
            result = self._request("PUT", f"/guilds/{self.guild_id}/members/{member_id}/roles/{olympus_role_id}")
            if result is None:
                print(f"  ✓ Assigned @Olympus role")

            # Assign project roles for Zeus
            if bot_info["projects"]:
                for project in bot_info["projects"]:
                    project_role_id = config["roles"].get(project)
                    if project_role_id:
                        result = self._request("PUT", f"/guilds/{self.guild_id}/members/{member_id}/roles/{project_role_id}")
                        if result is None:
                            print(f"  ✓ Assigned @{project} role")

            # Set nickname
            nickname = f"{bot_info['emoji']} {bot_name}"
            result = self._request("PATCH", f"/guilds/{self.guild_id}/members/{member_id}", {"nick": nickname})
            if result or result is None:
                print(f"  ✓ Set nickname: {nickname}")

            print()

        print("=== Phase 3 Complete ===\n")


def main():
    """Main execution"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set")
        sys.exit(1)

    phase3 = DiscordPhase3(token, GUILD_ID)
    phase3.assign_roles()


if __name__ == "__main__":
    main()
