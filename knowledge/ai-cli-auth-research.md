# AI CLI Auth Research

## Status: Research Pending (Phase 2b Gate)

This document tracks auth feasibility research for deploying AI CLI tools to headless agent VMs.

## Architecture Context

Hermes Agent runs on **ChatGPT/OpenAI OAuth** as its orchestration brain. The CLI tools below are NOT the agent's model — they are **tools that Hermes invokes via shell execution** for specific tasks:

| Tool | Purpose | Subscription |
|------|---------|--------------|
| `claude` (Claude Code CLI) | Coding, architecture review, security analysis | Claude Max (~$100/mo) |
| `gemini` (Gemini CLI) | Code review, vision/multimodal tasks | Gemini Ultra (~$100/mo) |
| `codex` (OpenAI Codex CLI) | Coding, refactoring, test generation | ChatGPT Pro (~$200/mo) |

Agents invoke these sequentially (not concurrently) — draft with Ollama cloud, refine with `claude`, validate with `gemini`. This reduces concurrent session risk.

## Research Questions

For each CLI tool, we need to determine:
1. Where does the auth token/session get stored after login?
2. Can that file be copied to a headless VM and reused?
3. What are the concurrent session limits?
4. Does the CLI detect non-interactive environments?
5. What's the fallback if subscription auth fails?

## Claude Code CLI

**Install**: `npm install -g @anthropic-ai/claude-code` → binary: `claude`

**Auth flow**: `claude auth` → browser OAuth flow

**Token location** (to research):
- Expected: `~/.claude/credentials.json` or similar
- Need to check: `ls -la ~/.claude/` after auth on Mac mini

**Headless viability**: Unknown — need to test copying session to VM

**Fallback**: API key via `ANTHROPIC_API_KEY` env var (metered billing, no subscription needed)

## Codex CLI (OpenAI)

**Install**: `npm install -g @openai/codex` → binary: `codex`

**Auth flow**: `codex auth` → ChatGPT Pro OAuth (already proven on Mac mini)

**Token location** (to research):
- Expected: `~/.config/openai/` or `~/.openai/`
- Same OAuth as ChatGPT — check if tokens are portable

**Headless viability**: Hermes already uses ChatGPT OAuth. May share the same token store.

**Fallback**: `OPENAI_API_KEY` env var

## Gemini CLI (Google)

**Install**: `npm install -g @google/gemini-cli` → binary: `gemini`

**Auth flow**: `gemini auth` → Google OAuth

**Token location** (to research):
- Expected: `~/.config/google/` or `~/.gemini/`
- Google OAuth refresh tokens are portable

**Headless viability**: Google OAuth refresh tokens are designed for server-to-server use. Most likely portable.

**Fallback**: `GOOGLE_API_KEY` env var or service account

## Research Steps

1. SSH into Mac mini: `ssh jefcox@jeffs-mac-mini.infiquetra.com`
2. Find existing auth token locations:
   ```bash
   find ~/.claude ~/.config ~/.local/share -name "*.json" 2>/dev/null | grep -i "auth\|token\|credential\|session"
   ls -la ~/.claude/
   ls -la ~/.config/openai/ 2>/dev/null
   ls -la ~/.config/google/ 2>/dev/null
   ```
3. Try copying token to Hephaestus (10.220.1.54) and test `claude status`
4. Document findings below

## Findings

*To be filled in after Phase 2b research*

## Decision

*To be made after findings — will determine whether to use subscription token copying, API keys, or manual per-agent browser auth via RustDesk/XRDP*
