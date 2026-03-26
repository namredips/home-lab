# Hermes Fleet Deployment Readiness Report

**Date**: 2026-03-25
**Scope**: 7 remaining agent VMs (Hephaestus already deployed)

## VM Connectivity Status

All 7 VMs are **reachable** via SSH as `agent@<IP>`.

| VM | IP | SSH | Hostname Confirmed |
|----|----|-----|--------------------|
| Zeus | 10.220.1.50 | OK | zeus |
| Athena | 10.220.1.51 | OK | athena |
| Apollo | 10.220.1.52 | OK | apollo |
| Artemis | 10.220.1.53 | OK | artemis |
| Perseus | 10.220.1.55 | OK | perseus |
| Prometheus | 10.220.1.56 | OK | prometheus |
| Ares | 10.220.1.57 | OK | ares |

**Note**: All 7 VMs have changed SSH host keys since last known_hosts entry. The local `~/.ssh/known_hosts` has stale entries (lines 142, 148, 161, 174, 182, 188, 192). Ansible with `host_key_checking=false` or updating known_hosts before deployment will be needed.

## Current Hermes Status

| VM | ~/.hermes/ exists | Hermes Service | Hermes Binary |
|----|-------------------|----------------|---------------|
| Zeus | No (empty) | inactive | Unknown |
| Athena | No (empty) | inactive | Unknown |
| Apollo | No (empty) | inactive | Unknown |
| Artemis | No (empty) | inactive | Unknown |
| Perseus | No (empty) | inactive | Unknown |
| Prometheus | No (empty) | inactive | Unknown |
| Ares | No (empty) | inactive | Unknown |

**Summary**: No VM has Hermes installed. All are clean slates for fresh deployment.

## Current Ollama Status

| VM | Ollama Service | Models Pulled |
|----|----------------|---------------|
| Zeus | inactive | None |
| Athena | inactive | None |
| Apollo | inactive | None |
| Artemis | inactive | None |
| Perseus | inactive | None |
| Prometheus | inactive | None |
| Ares | inactive | None |

**Summary**: Ollama is installed on all VMs (systemctl recognizes the service) but inactive with no models pulled. The `hermes_cluster.yml` playbook includes the `ollama` role which will handle starting it and pulling models.

## Playbook Analysis: `hermes_cluster.yml`

### Structure
The playbook runs 3 roles sequentially on `agent_vms`:
1. **`agent_provision`** — Dev environment, SSH keys, GitHub setup
2. **`ollama`** — Install/configure Ollama, pull models
3. **`hermes`** — Install Hermes binary, deploy config/env/SOUL.md, create systemd service

### Hermes Role Details
The `hermes` role (`ansible/roles/hermes/tasks/setup.yml`) will:
1. Check if `~/.local/bin/hermes` binary exists
2. Install via curl if missing (`--skip-setup` flag)
3. Create `~/.hermes/` config directory
4. Deploy **config.yaml** (model settings, Discord, memory, schedule)
5. Deploy **.env** (Discord token, Ollama endpoint, model name)
6. Deploy **SOUL.md** (per-agent personality/role document)
7. Deploy **systemd service** (`hermes-<name>.service`)
8. Reload systemd, enable and start the service

### Key Configuration
- **Primary model**: `gemini-3-flash-preview:cloud` (cloud model, not local Ollama)
- **Ollama base URL**: `http://127.0.0.1:11434` (local per-VM)
- **Discord guild**: `832250938571227217`
- **Discord tokens**: Per-agent from vault (`vault_discord_bot_token_<name>`)
- **Allowed user**: `378678500737155082`
- **Memory**: FTS5 persistent, auto-recall enabled
- **Active hours**: 08:00–01:00 ET
- **Service**: `hermes-<name>` (e.g., `hermes-zeus`)

### Pre-requisites
1. **Vault password** at `~/.vault_pass.txt` — needed for Discord bot tokens
2. **Ansible collections** installed (`ansible-galaxy collection install -r requirements.yml`)
3. **Known hosts** — stale entries need updating or `ANSIBLE_HOST_KEY_CHECKING=False`
4. **Discord bot tokens** — must exist in vault for all 7 agents:
   - `vault_discord_bot_token_zeus`
   - `vault_discord_bot_token_athena`
   - `vault_discord_bot_token_apollo`
   - `vault_discord_bot_token_artemis`
   - `vault_discord_bot_token_perseus`
   - `vault_discord_bot_token_prometheus`
   - `vault_discord_bot_token_ares`

## Blockers / Notes

1. **SSH host key mismatch** — All 7 VMs have changed host keys. Either:
   - Run `ssh-keygen -R <IP>` for each VM before deployment, OR
   - Set `ANSIBLE_HOST_KEY_CHECKING=False` for the playbook run
2. **No cloud models pre-pulled** — Since primary model is `gemini-3-flash-preview:cloud`, no local model pull is needed for core operation. Ollama is just the backend wrapper.
3. **Ollama inactive but installed** — The `ollama` role should handle starting it.
4. **Clean state** — No existing Hermes configs to conflict with. Fresh deployment.

## Deployment Command

```bash
cd ansible

# Option A: Full fleet (all agent_vms including already-deployed Hephaestus)
ANSIBLE_HOST_KEY_CHECKING=False uv run ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt

# Option B: Only the 7 remaining VMs (exclude Hephaestus)
ANSIBLE_HOST_KEY_CHECKING=False uv run ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --limit 'agent_vms:!hephaestus.infiquetra.com'

# Option C: Single VM pilot test first
ANSIBLE_HOST_KEY_CHECKING=False uv run ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --limit zeus.infiquetra.com
```

**Recommendation**: Run Option A (full fleet). The Hermes role is idempotent — re-running on Hephaestus will just confirm its config matches the templates. This ensures all 8 agents have identical, current configuration.
