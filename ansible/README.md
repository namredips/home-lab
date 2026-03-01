# OpenClaw Virtual Employee Infrastructure

**"Mount Olympus" Agent Cluster**

AI-powered virtual employees for software development using OpenClaw, deployed across 4 Dell servers running Proxmox VE.

## Overview

This infrastructure deploys 8 OpenClaw AI agents as Ubuntu 24.04 VMs on a Proxmox VE 9.1.1 cluster. Each agent is a full-stack generalist that can take on different specializations (security, QA, DevOps, etc.) depending on the task.

### Team Composition

| VMID | Agent | Role | Trait | IP | Host |
|------|-------|------|-------|-----|------|
| 100 | **Zeus** | PM, Orchestration | Leadership & authority | 10.220.1.50 | r820 |
| 101 | **Athena** | Senior Developer (Architecture) | Wisdom & strategy | 10.220.1.51 | r820 |
| 102 | **Apollo** | Developer (Code Quality) | Light, truth, reason | 10.220.1.52 | r820 |
| 103 | **Artemis** | Developer (Testing & Precision) | Precision, focus | 10.220.1.53 | r420 |
| 104 | **Hermes** | Developer (Integrations) | Speed, communication | 10.220.1.54 | r420 |
| 105 | **Perseus** | Developer (Complex Problems) | Heroic problem-solver | 10.220.1.55 | r720xd |
| 106 | **Prometheus** | Developer (Innovation) | Innovation, foresight | 10.220.1.56 | r720xd |
| 107 | **Ares** | Developer (Performance) | Strength, determination | 10.220.1.57 | r8202 |

## Architecture

### Physical Infrastructure

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Proxmox VE Cluster "olympus"                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  r420  (10.220.1.7)   Proxmox master │ Artemis(103) Hermes(104)      │
│  r8202 (10.220.1.8)   Proxmox node   │ Ares(107)                     │
│  r720xd(10.220.1.10)  Proxmox node   │ Perseus(105) Prometheus(106)  │
│  r820  (10.220.1.11)  Proxmox node   │ Zeus(100) Athena(101)         │
│                                       │ Apollo(102)                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
         │
         │ 10.220.1.0/24 (UniFi UDM, static DHCP reservations)
         │
┌────────▼─────────────────────────────────────────────────────────────┐
│            Agent VMs (Ubuntu 24.04, 4 vCPU, 16GB RAM, 250GB)        │
│                                                                       │
│  zeus.infiquetra.com     10.220.1.50                                  │
│  athena.infiquetra.com   10.220.1.51                                  │
│  ...                                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Storage Layout

| Host | Pool | Type | Devices | Content |
|------|------|------|---------|---------|
| all | `nvme-fast` | ZFS single | nvme0n1 | images, rootdir |
| r420 | `sas-data` | ZFS raidz1 | sdb,sdc,sdd | backup, iso |
| r720xd | `sas-data` | ZFS raidz2 ×2 | 11 SAS drives | backup, iso, images |
| r820 | `sas-data` | ZFS raidz2 | sdb–sdi | backup, iso |

### Technology Stack

**Hypervisor layer**:
- Proxmox VE 9.1.1 on Debian Trixie
- 4-node cluster (`pvecm`/corosync) named `olympus`
- VM template: Ubuntu 24.04 cloud image (VM 9000)

**Development Environment** (per agent VM):
- Python 3.12, Node.js 22, Dart/Flutter, Rust, Go, C/C++
- Docker, AWS CLI, AWS CDK
- Neovim (custom config), tmux, Starship prompt
- Claude Code CLI, Codex CLI, Gemini CLI

**AI Orchestration**:
- OpenClaw (autonomous agent framework)
- Anthropic Claude (primary LLM)
- Ollama (local LLM inference)

**Collaboration**:
- GitHub (code, issues, PRs)
- Discord (team communication)
- Git (shared repositories)

## Quick Start

### Prerequisites

```bash
cd ansible

# Install Python dependencies
uv sync

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Ensure vault password file exists
echo "your-vault-password" > ~/.vault_pass.txt
chmod 600 ~/.vault_pass.txt
```

### Deploy Proxmox Cluster

```bash
cd ansible

# Full pipeline (base → cluster → storage → template → VMs)
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --vault-password-file ~/.vault_pass.txt

# Single phase by tag
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --tags proxmox_storage --vault-password-file ~/.vault_pass.txt
```

### Deploy Agent Stack (after VMs are running)

```bash
ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```

### Verify Cluster Health

```bash
ansible-playbook -i inventory/hosts.yml proxmox_verify.yml \
  --vault-password-file ~/.vault_pass.txt

# Individual checks
ansible-playbook proxmox_verify.yml --tags verify_cluster
ansible-playbook proxmox_verify.yml --tags verify_storage
ansible-playbook proxmox_verify.yml --tags verify_vms
ansible-playbook proxmox_verify.yml --tags verify_ssh
```

### Teardown

```bash
ansible-playbook -i inventory/hosts.yml proxmox_cluster_reset.yml \
  -e reset=true --vault-password-file ~/.vault_pass.txt
```

## Ansible Roles

### Proxmox Infrastructure Roles

| Role | Purpose |
|------|---------|
| `proxmox_base` | Repo config, dist-upgrade, API user/token creation |
| `proxmox_cluster` | Form 4-node cluster via pvecm |
| `proxmox_storage` | ZFS pool creation + pvesm registration |
| `proxmox_template` | Ubuntu 24.04 cloud image → VM template (ID 9000) |
| `proxmox_vm` | Clone template, configure agents, start VMs |

### Agent Stack Roles (target: `agent_vms`)

| Role | Purpose |
|------|---------|
| `agent_provision` | Dev tools, SSH keys, GitHub setup |
| `agent_desktop` | Neovim, tmux, shell config, Starship |
| `ollama` | Local LLM inference |
| `openclaw` | OpenClaw agent + systemd service |

### Archived Roles (kept for reference)

| Role | Reason archived |
|------|----------------|
| `host_prepare` | Replaced by `proxmox_base` |
| `libvirt` | Proxmox has built-in KVM |
| `agent_vm` | Replaced by `proxmox_vm` |
| `zfs_disk_pools` | Absorbed into `proxmox_storage` |
| All K8s roles | MicroK8s cluster replaced by Proxmox |

## Deployment Phases

1. **Proxmox base** (~10 min)
   - Configure apt repos (no-subscription), dist-upgrade
   - Create `ansible@pam` API user and token

2. **Cluster formation** (~5 min)
   - Master creates cluster `olympus`
   - 3 nodes join one at a time (serial)

3. **ZFS storage** (~5 min)
   - Create pools from host_vars definitions
   - Register with Proxmox storage manager

4. **VM template** (~10 min)
   - Download Ubuntu 24.04 cloud image (~600MB)
   - Create and convert VM 9000 to template

5. **Agent VMs** (~15 min)
   - Clone template on each host for assigned agents
   - Configure resources, cloud-init, start
   - Wait for SSH on each VM

6. **Agent software stack** (~60 min)
   - Install dev tools, AI CLIs, OpenClaw

7. **Manual steps** (~30 min)
   - Authenticate AI tools on each VM
   - Configure GitHub SSH keys
   - Configure Discord bot tokens

**Total**: ~2-2.5 hours

## Post-Deployment

### Manual Steps Required

1. **API Token**: After `proxmox_base` run, the token secret is printed — add it to vault as `proxmox_api_token_secret`

2. **AI Tools**: Authenticate on each VM
   ```bash
   ssh agent@<agent-ip>
   claude --login
   # Edit ~/.openclaw/.env for OpenAI/Google keys
   ```

3. **GitHub**: Add SSH keys per agent
   ```bash
   ansible-playbook -i inventory/hosts.yml github_auth_agents.yml \
     --vault-password-file ~/.vault_pass.txt
   ```

4. **DHCP reservations**: Ensure each VM's MAC has a static reservation on UDM (10.220.1.1)
   - MACs defined in `roles/proxmox_vm/defaults/main.yml`

### Verification

```bash
# All agent VMs reachable
ansible agent_vms -i inventory/hosts.yml -m ping

# OpenClaw services running
ansible agent_vms -i inventory/hosts.yml \
  -a "systemctl status openclaw-{{ inventory_hostname_short }}" \
  -u agent --become

# Proxmox cluster
ssh root@10.220.1.7 pvecm status
```

## Troubleshooting

```bash
# VM not starting
ssh root@<proxmox-host> "qm list && qm status <vmid>"

# SSH access fails
ping <agent-ip>
ssh root@<proxmox-host> "qm agent <vmid> ping"

# ZFS pool degraded
ssh root@<proxmox-host> "zpool status"

# OpenClaw service fails
ssh agent@<agent-ip> "systemctl status openclaw-<agent-name>"

# Cluster quorum lost
ssh root@10.220.1.7 "pvecm status"
```

## Project Structure

```
ansible/
├── roles/
│   ├── proxmox_base/       # Proxmox repo, API user setup
│   ├── proxmox_cluster/    # pvecm cluster formation
│   ├── proxmox_storage/    # ZFS + pvesm registration
│   ├── proxmox_template/   # Ubuntu 24.04 VM template
│   ├── proxmox_vm/         # Agent VM provisioning
│   ├── agent_provision/    # Dev environment
│   ├── agent_desktop/      # Neovim, tmux, shell
│   ├── ollama/             # Local LLM
│   └── openclaw/           # OpenClaw agent
├── inventory/
│   ├── hosts.yml           # Cluster + VM inventory
│   ├── host_vars/          # Per-server ZFS pool config
│   └── group_vars/all/     # Encrypted secrets (vault)
├── proxmox_cluster.yml     # Main Proxmox setup playbook
├── proxmox_cluster_reset.yml  # Teardown playbook
├── proxmox_verify.yml      # Health check playbook
├── openclaw_cluster.yml    # Agent stack playbook
└── requirements.yml        # Ansible collection deps
```

## Resource Allocation

| Server | RAM | vCPU | VMs | RAM Committed |
|--------|-----|------|-----|---------------|
| r420 | 70G | 24 | 2 (Artemis, Hermes) | 32G |
| r8202 | 51G | 32 | 1 (Ares) | 16G |
| r720xd | 94G | 24 | 2 (Perseus, Prometheus) | 32G |
| r820 | 377G | 64 | 3 (Zeus, Athena, Apollo) | 48G |

**Total**: 8 VMs, 128GB RAM committed, 2TB disk (8× 250GB)

## Maintainer

**Jeff Cox** (jeff@infiquetra.com)

---

**Last Updated**: 2026-02-28
