# Agent VM Onboarding

How a new agent VM goes from zero to fully operational.

## Prerequisites

1. VM cloned from template 9000 (Ubuntu 24.04) and running
2. Cloud-init has set hostname and SSH keys (handled by `proxmox_vm` role)
3. VM accessible at its assigned IP (see cluster-topology.md)
4. Ansible vault password at `~/.vault_pass.txt` on Mac mini

## Step 1: Add to Inventory

In `ansible/inventory/hosts.yml`, add the VM under `agent_vms`:

```yaml
agent_vms:
  hosts:
    new-agent.infiquetra.com:
      ansible_host: 10.220.1.XX
      ansible_user: agent
```

Add per-agent Hermes vars to `ansible/inventory/host_vars/new-agent.infiquetra.com.yml`:

```yaml
agent_name: new-agent
hermes_primary_model: "ollama/qwen3-coder"
```

## Step 2: Add Discord Bot Token to Vault

```bash
cd ansible
ansible-vault encrypt_string 'DISCORD_BOT_TOKEN_HERE' \
  --name 'vault_discord_bot_token_new_agent' \
  --vault-password-file ~/.vault_pass.txt
```

Add the output to `inventory/group_vars/all/all.yml`.

## Step 3: Run Agent Provision Role

```bash
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --limit new-agent.infiquetra.com \
  --vault-password-file ~/.vault_pass.txt
```

This installs:
- Python 3.12, Node.js 22, Go, Rust, Dart/Flutter
- Dev tools: gopls, rust-analyzer, mypy, shellcheck, etc.
- GitHub CLI (`gh`) with PAT auth
- Claude Code CLI (`claude`), Codex CLI, Gemini CLI
- Hermes Agent framework + systemd service
- Redis client tools
- Dotfiles and Neovim config

## Step 4: Verify Hermes

```bash
# Check service status
ssh agent@10.220.1.XX systemctl status hermes-new-agent

# Check logs
ssh agent@10.220.1.XX journalctl -u hermes-new-agent -f

# Verify Discord connectivity
# Look for the bot appearing online in the Discord server
```

## Step 5: Register SSH Key with GitHub

After provisioning, the agent's SSH key needs to be registered with GitHub.
With automated GitHub auth (via `vault_github_pat`):
```bash
# This happens automatically during provisioning via gh ssh-key add
# Verify:
ssh agent@10.220.1.XX gh ssh-key list
```

## Step 6: Clone Repos

```bash
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --limit new-agent.infiquetra.com \
  --tags clone_repos \
  --vault-password-file ~/.vault_pass.txt
```

## Step 7: Verify Coordination

```bash
# Check Redis connectivity from agent
ssh agent@10.220.1.XX redis-cli -h 10.220.1.64 -a $OLYMPUS_REDIS_PASSWORD ping

# Check beads connectivity
ssh agent@10.220.1.XX bd ready
```

## Rollback

To remove a Hermes instance without destroying the VM:

```bash
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --limit new-agent.infiquetra.com \
  -e reset=true \
  --vault-password-file ~/.vault_pass.txt
```

## Agent Identity Reference

Each agent has a named persona that shapes its SOUL.md, Discord bot, and behavior:

| Agent | Persona | Specialty |
|-------|---------|-----------|
| Zeus | Leadership, vision | Project coordination, priority decisions |
| Athena | Architecture, wisdom | System design, senior code review |
| Apollo | Artistry, clarity | Frontend, documentation, quality |
| Artemis | Precision, focus | Testing, performance, hunting bugs |
| Hephaestus | Craftsmanship, build | Infrastructure, automation, tooling |
| Perseus | Courage, exploration | New technology, prototyping |
| Prometheus | Foresight, innovation | Platform engineering, developer tools |
| Ares | Action, directness | Fast execution, incident response |
