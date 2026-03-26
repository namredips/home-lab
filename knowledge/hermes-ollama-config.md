# Hermes + Ollama Backend Configuration Guide

Date: 2026-03-25
Status: Operational (validated on Hephaestus VM 104)

## Overview

Hermes Agent uses Ollama as its inference backend via the OpenAI-compatible API endpoint. This document covers the critical configuration details, authentication requirements, and model selection rationale discovered during the Phase 6 fleet migration.

## 1. Ollama Cloud Model SSH Key Authentication

Ollama cloud models (e.g., `gemini-3-flash-preview:cloud`, `qwen3.5:cloud`) authenticate via an **SSH ed25519 keypair**, not API keys or OAuth.

### Key Location

The key location depends on how Ollama runs:

| Context | Key Path |
|---------|----------|
| Ollama systemd service (VMs) | `/usr/share/ollama/.ollama/id_ed25519` |
| Ollama user install (mac mini) | `~/.ollama/id_ed25519` |

The systemd service runs as the `ollama` system user, whose home directory is `/usr/share/ollama`. The key is generated on first run and registered with Ollama's cloud service.

### Fleet Deployment

All VMs must share the **same registered key** (the mac mini's key that was first registered). To deploy:

1. Copy the mac mini's key to each VM:
   ```bash
   # Source: ~/.ollama/id_ed25519 on mac mini
   # Target: /usr/share/ollama/.ollama/id_ed25519 on each VM
   ```

2. Set correct ownership and permissions:
   ```bash
   chown ollama:ollama /usr/share/ollama/.ollama/id_ed25519
   chmod 600 /usr/share/ollama/.ollama/id_ed25519
   ```

3. Restart Ollama service:
   ```bash
   systemctl restart ollama
   ```

**Why one key for all VMs**: Ollama registers a single keypair with its cloud service. Generating new keys on each VM would create separate unregistered identities. Sharing the mac mini's already-registered key avoids re-registration.

## 2. Hermes Provider Configuration

### How Hermes Selects Its Model

Hermes uses **environment variables**, not `config.yaml`, for model/provider configuration. The `providers:` block in `config.yaml` is **silently ignored**.

### Required Environment Variables

Set in `/home/<user>/.hermes/.env` (managed by Ansible template `hermes.env.j2`):

```bash
# Point Hermes at local Ollama's OpenAI-compatible endpoint
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama

# Model name — bare name, no "ollama/" prefix
HERMES_MODEL=gemini-3-flash-preview:cloud
```

### What Each Variable Does

| Variable | Purpose | Default if unset |
|----------|---------|------------------|
| `OPENAI_BASE_URL` | API endpoint URL | OpenRouter (`https://openrouter.ai/api/v1`) |
| `OPENAI_API_KEY` | Auth token for the endpoint | None (falls back to cookie auth) |
| `HERMES_MODEL` | Model identifier to request | `openrouter/anthropic/claude-opus-4.6` |

### Ansible Defaults (from `roles/hermes/defaults/main.yml`)

```yaml
hermes_ollama_base_url: "http://127.0.0.1:11434"
hermes_primary_model: "gemini-3-flash-preview:cloud"
hermes_auxiliary_conversation_model: "gemini-3-flash-preview:cloud"
hermes_auxiliary_subagent_model: "gemini-3-flash-preview:cloud"
```

### config.yaml Model Block

The `config.yaml` only uses model names for the `auxiliary` block (conversation and subagent models). The primary model is set exclusively via `HERMES_MODEL` env var:

```yaml
model:
  auxiliary:
    conversation: "gemini-3-flash-preview:cloud"
    subagent: "gemini-3-flash-preview:cloud"
```

There is **no `providers:` block** in the working config. Do not add one.

## 3. Model Selection Rationale

### Primary: `gemini-3-flash-preview:cloud`

| Criteria | Value |
|----------|-------|
| SWE-Bench Verified | 78% (highest among available Ollama cloud models) |
| Design target | Agentic multi-turn tool calling |
| Response latency | Fastest among top-tier cloud models |
| Cost | Free via Ollama cloud (SSH key auth) |

Best fit for Hermes because the agent workflow is multi-turn tool-calling conversations, which is exactly what Gemini 3 Flash was optimized for.

### Fallback Chain

1. **`gemini-3-flash-preview:cloud`** — primary (reasons above)
2. **`qwen3.5:cloud`** — 397B-A17B MoE, multimodal capable, strong reasoning
3. **`kimi-k2.5:cloud`** — alternative if both above are unavailable

All fallbacks are Ollama cloud models using the same SSH key auth mechanism.

## 4. The OpenRouter Trap

### Symptom

```
Error: No cookie auth credentials found
```

### Cause

If `OPENAI_BASE_URL` or `HERMES_MODEL` are **not set**, Hermes defaults to:
- Endpoint: `https://openrouter.ai/api/v1`
- Model: `openrouter/anthropic/claude-opus-4.6`

OpenRouter requires either an API key (`OPENROUTER_API_KEY`) or browser cookie authentication. Since neither is configured on headless VMs, the request fails with the cookie auth error.

### Fix

Always set both environment variables in the Hermes `.env` file:

```bash
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
HERMES_MODEL=gemini-3-flash-preview:cloud
```

### Diagnosis Checklist

If a Hermes instance is failing to generate responses:

1. Check env file exists and is loaded:
   ```bash
   systemctl show hermes-<name> -p EnvironmentFiles
   cat /home/<user>/.hermes/.env
   ```

2. Verify Ollama is running and accessible:
   ```bash
   curl http://127.0.0.1:11434/v1/models
   ```

3. Verify the cloud model is available:
   ```bash
   ollama list  # should show cloud models if key is valid
   ```

4. Check Ollama SSH key exists and has correct permissions:
   ```bash
   ls -la /usr/share/ollama/.ollama/id_ed25519
   # Should be: -rw------- ollama ollama
   ```

## 5. Ansible Role Reference

The Hermes Ansible role (`ansible/roles/hermes/`) manages all of this:

- **`defaults/main.yml`** — model names, Ollama URL, schedule, memory settings
- **`templates/hermes.env.j2`** — environment file with Discord token, Ollama config
- **`templates/config.yaml.j2`** — Hermes config (identity, auxiliary models, Discord, memory, schedule)
- **`tasks/setup.yml`** — installs Hermes, deploys config, enables systemd service

### Deploying to a Single VM

```bash
cd ansible
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --limit hephaestus \
  --vault-password-file ~/.vault_pass.txt
```

### Deploying to All Agent VMs

```bash
cd ansible
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```
