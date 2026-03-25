# Hermes Agent vs OpenClaw: Framework Analysis & Migration Guide

**Date**: March 2026
**Status**: Decision — migrate to Hermes Agent

---

## Context

The Mount Olympus agent stack runs 8 independent agent VMs, each running OpenClaw as its agent runtime. Agents coordinate externally via Discord and GitHub Issues — the coordination layer is framework-agnostic (`gh` CLI + Discord messages). This document evaluates whether NousResearch's Hermes Agent (released Feb 2026) would be a better runtime for each individual agent instance, and provides a migration path if the answer is yes.

---

## Framework Profiles

### OpenClaw (current)

- **Runtime**: Node.js (`npm install -g openclaw`)
- **Architecture**: Multi-channel gateway with plugin system, ClawHub skill registry
- **Strengths**: 20+ messaging channels, web dashboard, broad model support via OpenAI-compatible API
- **Identity**: Configurable via workspace markdown files (SOUL.md, IDENTITY.md, etc.)
- **Memory**: Session-scoped. Cross-session "memory" is a JS hook (`handler.js`) running regex on daily notes files and appending to a flat MEMORY.md

### Hermes Agent (NousResearch)

- **Runtime**: Python (single `curl` installer)
- **Architecture**: Single-agent gateway with built-in persistent memory, autonomous skill system
- **Strengths**: FTS5 cross-session memory, self-improving skills, research-grade tool-calling model
- **Identity**: SOUL.md (slot #1 in system prompt) — same convention as OpenClaw
- **Memory**: Multi-level persistent store with FTS5 full-text search + LLM summarization

---

## Comparison Matrix

| Capability | OpenClaw | Hermes Agent | Winner |
|---|---|---|---|
| **Persistent Memory** | Regex on flat files | FTS5 + LLM summarization | **Hermes** |
| **Skill Learning** | None (hand-coded hooks) | Autonomous creation + improvement | **Hermes** |
| **Self-Improvement** | Pattern matching on notes | Continuous, built-in | **Hermes** |
| **Tool Execution** | `safeBins` allowlist | 40+ built-in + 6 terminal backends | **Hermes** |
| **Model Routing** | Ollama proxy, any provider | Provider Router with fallbacks, any provider | Tie |
| **Discord Integration** | Plugin, per-agent bot tokens | Native, per-agent bot tokens | Tie |
| **GitHub Workflow** | Via `gh` CLI | Via `gh` CLI | Tie |
| **Persona System** | SOUL.md + IDENTITY.md templates | SOUL.md + personality overlays | Tie (same convention) |
| **Channel Support** | 20+ channels | 5 channels | OpenClaw |
| **Web Dashboard** | Built-in (port 18789) | None (CLI-focused) | OpenClaw |
| **Installation Complexity** | npm + 18-file Ansible role | Single `curl` command | **Hermes** |
| **Subagent Spawning** | Up to 8 concurrent | Built-in delegation | Tie |
| **Multi-Agent Orchestration** | No native orchestration | No native orchestration (Issue #344 tracking) | Tie — both rely on external coordination |
| **Cron/Scheduling** | Built-in | Built-in | Tie |
| **Model Optimization** | General-purpose models | Hermes-3 fine-tuned for tool-calling via Atropos RL | **Hermes** (if using Hermes-3) |

---

## Deep Dive: The Memory Gap

The most significant difference between the two frameworks.

**Current state (OpenClaw)**: The `self-improvement/handler.js` hook runs regex patterns like `/blocked[^.]*\./gi` and `/learned[^.]*\./gi` over daily notes files. It appends timestamped entries to a flat `MEMORY.md` under sections `## Learnings`, `## Patterns`, `## Watch List`. There is no semantic search, no summarization, and no automatic recall. Each session starts cold.

**Hermes Agent**: Multi-level memory architecture:
- **Working memory**: Current session context
- **Long-term memory**: SQLite-backed with FTS5 full-text search
- **Summarization**: LLM automatically compresses old memories into useful context
- **Automatic recall**: Agent queries relevant memories before starting any task
- **Manual search**: `hermes memory search "topic"` for programmatic lookup

For agents that work on the same repositories daily, this is the single biggest capability upgrade. An agent that remembers "the auth-service tests are flaky because of race conditions in the session store" or "the last PR to this module required rebasing against a concurrent change from Apollo" is substantially more effective than one that starts cold every session.

---

## Deep Dive: Autonomous Skill Creation

**Current state (OpenClaw)**: No skill learning mechanism. If an agent solves a complex problem (e.g., Artemis finds a non-obvious input validation pattern), that knowledge dies with the session unless manually captured.

**Hermes Agent**: After completing complex tasks, the agent:
1. Detects the solution was novel
2. Extracts it into a named, reusable skill with parameters
3. Stores it persistently
4. Improves the skill on subsequent invocations
5. Skills are shareable via NousResearch's Skills Hub (agentskills.io)

This creates a compound improvement curve — agents that have been running longer are genuinely more capable.

---

## Compatibility Assessment

Three key compatibility questions for the current setup:

### 1. Model routing with fallbacks
**Compatible.** Hermes Agent's Provider Router supports multiple providers (OpenRouter, Kimi/Moonshot, OpenAI, custom endpoints) with fallback chains configured in `config.yaml`. The current Ollama proxy setup (`http://127.0.0.1:11434/v1` with Kimi K2.5 primary, DeepSeek/Gemini fallbacks) maps directly. Auxiliary model overrides allow pointing conversation/subagent calls at specific endpoints.

### 2. Persona depth (SOUL.md/IDENTITY.md)
**Compatible.** Hermes Agent uses the same `SOUL.md` convention — it occupies slot #1 in the system prompt and completely replaces the default identity. Supports arbitrary depth and complexity. Also supports session-level personality overlays and workspace-level `AGENTS.md` for project instructions. Existing personality templates port with minimal changes.

### 3. Per-agent Discord bots in shared guild
**Compatible.** Each VM runs its own Hermes Agent instance with its own `config.yaml` containing its own Discord bot token. This is architecturally identical to the current OpenClaw setup. Discord natively supports multiple bots per guild. Hermes tracks sessions by key, keeping conversations isolated.

**No blocking incompatibilities.**

---

## What You'd Lose

| Loss | Impact |
|---|---|
| Web dashboard (port 18789) | Low — depends on actual usage |
| 20+ channel support → 5 channels | None — currently Discord-only |
| ClawHub skill ecosystem | Low — replaced by Hermes Skills Hub (smaller but growing) |
| Node.js runtime | Medium — existing JS hooks need rewriting (1 file: `handler.js`) |

The `handler.js` hook is the only real porting work, and it gets replaced by Hermes's built-in memory — not rewritten, just deleted.

---

## What You'd Gain

| Gain | Significance |
|---|---|
| Cross-session persistent memory with FTS5 search | High — biggest current capability gap |
| Autonomous skill creation and improvement | High — compound improvement over time |
| Simpler deployment | Medium — curl install vs. npm + 18-file Ansible role |
| Research-grade tool-calling (Hermes-3 via Atropos RL) | Medium — if using Hermes-3 model |
| Active multi-agent orchestration development (Issues #344, #412, #492) | Future |

---

## Migration Plan

### What Changes in the Ansible Role

The `openclaw` role (`roles/openclaw/`) gets replaced with a new `hermes_agent` role. Key structural differences:

| OpenClaw | Hermes Agent |
|---|---|
| `npm install -g openclaw` | `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash` |
| `~/.openclaw/openclaw.json` | `~/.hermes/config.yaml` |
| `openclaw gateway --port 18789` | `hermes start` |
| Service: `openclaw-gateway` | Service: `hermes-<agent_name>` |
| 8 workspace files | 3 files: SOUL.md, AGENTS.md, BOOTSTRAP.md |
| `hooks/self-improvement/handler.js` | Deleted — built-in memory replaces it |

### Config Mapping

```yaml
# config.yaml (Hermes) vs openclaw.json mapping

# Identity — same SOUL.md convention
identity:
  name: "Zeus"
  soul: "~/.hermes/SOUL.md"

# Provider — maps from openclaw.json "models.providers.ollama"
providers:
  - id: ollama
    type: openai-compatible
    base_url: "http://127.0.0.1:11434/v1"
    api_key: "ollama-local"

# Model routing — maps from openclaw.json "agents.defaults.model"
model:
  primary: "ollama/kimi-k2.5:cloud"
  fallbacks:
    - "ollama/deepseek-v3.2:cloud"
    - "ollama/gemini-3-flash-preview:cloud"
  auxiliary:
    conversation: "ollama/gemini-3-flash-preview:cloud"  # was heartbeat.model
    subagent: "ollama/gemini-3-flash-preview:cloud"      # was subagents.model

# Discord — maps from openclaw.json "plugins.entries.discord"
discord:
  enabled: true
  guild_id: "832250938571227217"

# Memory — new, replaces handler.js entirely
memory:
  enabled: true
  db_path: "~/.hermes/memory.db"
  auto_recall: true
  summarize: true

# Schedule — maps from openclaw.json "agents.defaults.heartbeat"
schedule:
  heartbeat: "20m"
  active_hours:
    start: "08:00"
    end: "01:00"
    timezone: "America/New_York"
```

### Workspace File Consolidation

8 files → 3 files. Content absorbed as follows:

| Old File | Destination |
|---|---|
| `SOUL.md` | `SOUL.md` (keep, extend) |
| `IDENTITY.md` | Absorbed into `SOUL.md` |
| `MODEL-ROUTING.md` | Absorbed into `SOUL.md` |
| `WORKFLOW.md` | Absorbed into `SOUL.md` (condensed) |
| `USER.md` | Absorbed into `SOUL.md` |
| `AGENTS.md` | `workspace/AGENTS.md` (keep as-is) |
| `BOOTSTRAP.md` | `workspace/BOOTSTRAP.md` (update commands) |
| `TOOLS.md` | Deleted — Hermes has 40+ built-in tools, no explicit allowlist needed |

### Memory Interaction Model

Replace the flat MEMORY.md + daily notes pattern with explicit + automatic memory:

```bash
# Store a key learning
hermes memory store "auth-service tests" "flaky due to session store race condition — see PR #142"

# Store a pattern
hermes memory store "artemis/input-validation" "use pydantic v2 model_validator for cross-field validation"

# Search before starting related work
hermes memory search "auth-service"

# Hermes also auto-recalls relevant memories before each task — no action needed
```

The `handler.js` self-improvement hook is deleted entirely. No replacement needed.

### Ansible Playbook Change

In `openclaw_cluster.yml`, replace the final agent setup play:

```yaml
# Before
- name: Setup OpenClaw agents
  hosts: agent_vms
  gather_facts: yes
  roles:
    - { role: openclaw, tags: ['openclaw'] }

# After
- name: Setup Hermes agents
  hosts: agent_vms
  gather_facts: yes
  roles:
    - { role: hermes_agent, tags: ['hermes_agent'] }
```

Update the deployment summary play to reflect Hermes commands:
- `systemctl status hermes-<agent_name>` (was `openclaw-gateway`)
- Remove web dashboard reference (port 18789)
- Add memory search note

### Staging Approach

Run OpenClaw and Hermes in parallel on one VM first before fleet migration:

1. Pick a low-stakes agent (Ares or Prometheus)
2. Install Hermes alongside OpenClaw (different service name, no port conflict)
3. Run both for a week — compare behavior, check Discord presence, verify memory accumulation
4. Migrate remaining 7 agents once satisfied

---

## Decision

**Migrate.** The persistent memory and autonomous skill creation address the two biggest capability gaps in the current setup. The coordination model (Discord + GitHub Issues) is fully portable. The persona system uses the same SOUL.md convention. The only real migration work is rewriting the Ansible role, consolidating the workspace files, and deleting `handler.js`.

The main cost is losing the web dashboard. The main gain is agents that actually remember what they learned yesterday.

---

## References

- [Hermes Agent](https://hermes-agent.nousresearch.com/)
- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [Hermes Agent Docs](https://hermes-agent.nousresearch.com/docs/)
- [Hermes Personality & SOUL.md](https://hermes-agent.nousresearch.com/docs/user-guide/features/personality/)
- [Hermes Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration/)
- [Hermes Discord Integration](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord/)
- [Issue #344: Multi-Agent Architecture](https://github.com/NousResearch/hermes-agent/issues/344)
- [Issue #412: Consensus & Voting Engine](https://github.com/NousResearch/hermes-agent/issues/412)
- [MarkTechPost: Hermes Agent Release](https://www.marktechpost.com/2026/02/26/nous-research-releases-hermes-agent-to-fix-ai-forgetfulness-with-multi-level-memory-and-dedicated-remote-terminal-access-support/)
- [OpenClaw](https://openclaw.ai/)
