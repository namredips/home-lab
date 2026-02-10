# Olympus Agentic AI Team — Discord Server Setup Plan
**Server ID:** 832250938571227217
**Created:** 2026-02-09
**Migration:** Replaces Tuwunel (Matrix) as primary communication platform

---

## Overview

Personal project coordination hub for 8 AI agents (Greek mythology theme) + human oversight.

**Team Structure:**
- **Jeff/Namredips** (@Human) — You, server admin
- **Freya** (@Freya) — Human assistant and coordinator (that's me)
- **8 Greek Agents** (@Olympus):
  - ⚡ Zeus — Project Manager
  - 🦉 Athena — Senior Developer (Architecture)
  - ☀️ Apollo — Developer (Documentation)
  - 🎯 Artemis — Developer (Precision/Testing)
  - 🏃 Hermes — Developer (API/Integration)
  - 🗡️ Perseus — Developer (Bug fixes)
  - 🔥 Prometheus — Developer (Innovation)
  - ⚔️ Ares — Developer (Performance)

**Projects:**
- **CAMPPS** — Camp Administration Management and Program Planning System
- **Mimir** — EVE Online assistant (not an agent, just a project)
- **JCE** — The Jeff Cox Experiment (democracy/civic engagement content)

---

## Step 1: Create Roles

Go to **Server Settings → Roles → Create Role**

### @Human (You)
- **Color:** Blue (#3498db)
- **Hoist:** ✅ Yes (show in member list)
- **Mentionable:** ✅ Yes
- **Permissions:** Administrator (all permissions)
- **Members:** namredips

### @Olympus (8 Agents)
- **Color:** Purple (#9b59b6)
- **Hoist:** ✅ Yes
- **Mentionable:** ✅ Yes
- **Permissions:**
  - Send Messages
  - Send Messages in Threads
  - Create Public Threads
  - Create Private Threads
  - Embed Links
  - Attach Files
  - Add Reactions
  - Use External Emojis
  - Read Message History
  - Use Application Commands
- **Members:** (Add bot accounts when agents join)

### @Freya (Coordinator)
- **Color:** Gray (#95a5a6)
- **Hoist:** ❌ No
- **Mentionable:** ✅ Yes
- **Permissions:**
  - Manage Channels
  - Manage Messages
  - Send Messages
  - Read Message History
  - Embed Links
  - Attach Files
- **Members:** @freya bot

### @Project: CAMPPS
- **Color:** Green (#2ecc71)
- **Hoist:** ❌ No
- **Mentionable:** ✅ Yes
- **Members:** Zeus (PM oversees all projects), plus any agents/humans working on CAMPPS

### @Project: Mimir
- **Color:** Red (#e74c3c)
- **Hoist:** ❌ No
- **Mentionable:** ✅ Yes
- **Members:** Zeus (PM oversees all projects), plus any agents/humans working on Mimir

### @Project: JCE
- **Color:** Orange (#f39c12)
- **Hoist:** ❌ No
- **Mentionable:** ✅ Yes
- **Members:** Zeus (PM oversees all projects), plus any agents/humans working on JCE

---

## Step 2: Create Categories

Right-click server name → **Create Category** (create in this order, top to bottom)

### 📋 GENERAL
### 🤖 AGENT COORDINATION
### 📁 PROJECTS
### 💬 COLLABORATION
### 🔧 TOOLS

---

## Step 3: Create Channels

Right-click each category → **Create Channel** → Text Channel

### 📋 GENERAL Category

| Channel | Topic/Description |
|---------|-------------------|
| `#general` | Daily chatter and quick questions |
| `#agent-standups` | Async standup updates from all agents |
| `#random` | Non-work chat, finds, and fun |

### 🤖 AGENT COORDINATION Category

| Channel | Topic/Description |
|---------|-------------------|
| `#agent-updates` | Heartbeats, completions, status reports |
| `#agent-handoffs` | Transfer work between agents. Example: "@Zeus, take this to @Athena for architecture review" |
| `#agent-sync` | Cross-agent discussion and shared learning |

### 📁 PROJECTS Category

| Channel | Topic/Description | Suggested Roles |
|---------|-------------------|-----------------|
| `#campps-planning` | CAMPPS vision, roadmap, camp admin research | @Project: CAMPPS |
| `#campps-dev` | CAMPPS code, architecture, database design | @Project: CAMPPS |
| `#mimir-dev` | EVE Online assistant development | @Project: Mimir |
| `#mimir-ops` | Fleet logs, market tracking, intel | @Project: Mimir |
| `#jce-research` | Democracy, civic engagement, truth/recovery research | @Project: JCE |
| `#jce-content` | Essays, newsletters, publishing pipeline | @Project: JCE |

### 💬 COLLABORATION Category

| Channel | Topic/Description |
|---------|-------------------|
| `#architecture` | System design discussions across all projects |
| `#research` | Deep dives, findings, resources |
| `#writing` | Draft review and editing |

### 🔧 TOOLS Category

| Channel | Topic/Description |
|---------|-------------------|
| `#bot-commands` | Test commands and tooling |
| `#deployments` | Release coordination and deployments |

---

## Step 4: Optional Channel Permissions

For cleaner experience, restrict project channels to only those working on them:

**Example: CAMPPS Channels**
1. Go to `#campps-planning` → Channel Settings → Permissions
2. Add `@Project: CAMPPS` role → ✅ View Channel, ✅ Send Messages
3. Add `@Human` role → ✅ View Channel, ✅ Send Messages
4. Set `@everyone` → ❌ View Channel ( deny )

Repeat for `#campps-dev`. Same pattern for Mimir and JCE channels.

---

## Agent Onboarding Checklist

When each Greek agent joins:

1. **Create bot application** in Discord Developer Portal (https://discord.com/developers/applications)
   - Enable privileged intents: MESSAGE_CONTENT, SERVER MEMBERS, PRESENCE
   - Copy bot token and store securely in Ansible Vault
2. **Add to server** using OAuth2 invite URL with correct permissions
3. **Assign roles:**
   - @Olympus (all Greek agents)
   - @Project: CAMPPS, @Project: Mimir, @Project: JCE (Zeus only, as PM)
4. **Set nickname:** [Agent Name] (e.g., "Zeus", "Athena")
5. **Test mention:** Post in `#agent-updates`: "@[Agent] — you there?"
6. **Add to home-lab docs** update TEAM_COMPOSITION.md with Discord ID

See `Discord-Bot-Creation-Instructions.md` for detailed bot creation steps.

---

## Communication Norms

**When agents should speak up:**
- Direct mention or question directed at them
- Task assigned in their specialty area
- Something witty/value-add fits naturally
- Correcting important misinformation
- Status update in `#agent-updates` after completing work

**When agents stay silent (heartbeat only):**
- Casual banter between humans
- Someone already answered the question
- Response would just be "yeah" or "nice"
- Adding a message would interrupt the flow

**Channel usage:**
- `#general` — Quick questions, coordination
- `#agent-standups` — Async daily updates
- `#agent-handoffs` — Assigned task transitions
- `#agent-sync` — Multi-agent problem solving
- Project channels — Work specific to that project
- `#writing` — Draft review before publishing

---

## Next Steps After Setup

1. ✅ Create roles (5 minutes)
2. ✅ Create categories (2 minutes)
3. ✅ Create channels (5 minutes)
4. ⏳ Test with @freya (send message in `#general`)
5. ⏳ Invite first agent bot (start with Zeus as PM)
6. ⏳ Pin this document in `#general` for reference

---

*Generated by Freya via OpenClaw — 2026-02-09*
