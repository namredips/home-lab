# Architecture Overview

Technical architecture and design decisions for the OpenClaw virtual employee infrastructure.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Design Decisions](#design-decisions)
3. [Network Topology](#network-topology)
4. [Data Flow](#data-flow)
5. [Security Model](#security-model)
6. [Scalability](#scalability)

---

## System Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Physical Layer                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │   r420   │  │  r8202   │  │  r720xd  │  │   r820   │                │
│  │  70G RAM │  │  51G RAM │  │  94G RAM │  │ 377G RAM │                │
│  │  24 vCPU │  │  32 vCPU │  │  24 vCPU │  │  64 vCPU │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
└───────┼─────────────┼─────────────┼─────────────┼──────────────────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────────────────┐
│               Hypervisor Layer — Proxmox VE 9.1.1 (Debian Trixie)       │
│               Cluster "olympus" — 4-node corosync quorum                │
│                                                                           │
│  r420 (master)   r8202 (node)   r720xd (node)   r820 (node)             │
│  ├─ Artemis(103) ├─ Ares(107)   ├─ Perseus(105)  ├─ Zeus(100)           │
│  └─ Hermes(104)                 └─ Prometheus(106)├─ Athena(101)         │
│                                                   └─ Apollo(102)         │
│                                                                           │
│  ZFS storage per host:                                                    │
│  nvme-fast (VM disks) + sas-data (backup/bulk, where available)          │
└───────────────────────────────────────────────────────────────────────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────────────────┐
│                    Network Layer (10.220.1.0/24)                         │
│                    Gateway/DNS: 10.220.1.1 (UniFi UDM)                  │
│                                                                           │
│  Agent VMs: 10.220.1.50–57  (static DHCP via MAC reservations)          │
└───────────────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────────┐
│                        Application Layer                                  │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  OpenClaw    │  │    Ollama    │  │    GitHub    │                   │
│  │  Agents      │  │  (local LLM) │  │  (external)  │                   │
│  │  - Memory    │  │  - Llama 3   │  │  - Repos     │                   │
│  │  - Tasks     │  │  - Mistral   │  │  - Issues    │                   │
│  │  - Discord   │  │              │  │  - PRs       │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└───────────────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────────┐
│                       External Services Layer                             │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  Anthropic   │  │   OpenAI     │  │   Google     │                   │
│  │  Claude API  │  │   GPT API    │  │  Gemini API  │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Physical Infrastructure

| Server | Role | RAM | vCPU | NVMe | SAS | VMs Hosted |
|--------|------|-----|------|------|-----|------------|
| **r420** | Proxmox master | 70G | 24 | 931G | 3×931G (raidz1) | Artemis, Hermes |
| **r8202** | Proxmox node | 51G | 32 | 931G | — | Ares |
| **r720xd** | Proxmox node | 94G | 24 | 931G | 6×1.8T + 5×2.7T (raidz2×2) | Perseus, Prometheus |
| **r820** | Proxmox node | 377G | 64 | 931G | 8×931G (raidz2) | Zeus, Athena, Apollo |

**Total capacity**: 592G RAM, 64TB+ raw storage across 4 servers

#### Virtual Machine Layer

| VMID | Agent | Host | vCPU | RAM | Disk | Role | IP |
|------|-------|------|------|-----|------|------|----|
| 100 | Zeus | r820 | 4 | 16G | 250G | PM, Orchestration | 10.220.1.50 |
| 101 | Athena | r820 | 4 | 16G | 250G | Senior Dev (Architecture) | 10.220.1.51 |
| 102 | Apollo | r820 | 4 | 16G | 250G | Dev (Code Quality) | 10.220.1.52 |
| 103 | Artemis | r420 | 4 | 16G | 250G | Dev (Testing) | 10.220.1.53 |
| 104 | Hermes | r420 | 4 | 16G | 250G | Dev (Integrations) | 10.220.1.54 |
| 105 | Perseus | r720xd | 4 | 16G | 250G | Dev (Complex Problems) | 10.220.1.55 |
| 106 | Prometheus | r720xd | 4 | 16G | 250G | Dev (Innovation) | 10.220.1.56 |
| 107 | Ares | r8202 | 4 | 16G | 250G | Dev (Performance) | 10.220.1.57 |

**OS**: Ubuntu 24.04 LTS (cloud image, provisioned via Proxmox cloud-init)
**Access**: SSH key authentication (agent user)
**Template**: VM ID 9000 on r420 (clone source for all VMs)

#### ZFS Storage Layout

| Host | Pool | RAID type | Devices | Usable | Registered as |
|------|------|-----------|---------|--------|---------------|
| all | `nvme-fast` | single | nvme0n1 | ~931G | images, rootdir |
| r420 | `sas-data` | raidz1 | sdb,sdc,sdd | ~1.86T | backup,iso,snippets |
| r720xd | `sas-data` | raidz2 ×2 vdevs | 6×1.8T + 5×2.7T | ~21T | backup,iso,images |
| r820 | `sas-data` | raidz2 | sdb-sdi (8×931G) | ~5.6T | backup,iso,snippets |

---

## Design Decisions

### Decision 1: Proxmox VE over bare-metal Ubuntu + libvirt

**Chosen**: Proxmox VE 9.1.1 (Debian Trixie)

**Previous approach**: Ubuntu 22.04 + libvirt/KVM + Ansible-managed VMs

**Rationale**:
- **Native cluster management**: `pvecm` handles quorum, live migration, HA without extra software
- **Web UI**: Proxmox web console for emergency access without Ansible
- **ZFS integration**: pvesm registers ZFS pools as first-class storage
- **Cloud-init support**: `qm set --ide2 storage:cloudinit` native, no virt-install overhead
- **Template cloning**: `qm clone` is significantly faster than virt-install from ISO

**Trade-offs**:
- No-subscription nag (cosmetic, suppressed via no-sub repo)
- Less familiar than Ubuntu for host-level debugging

### Decision 2: VMs over Containers

**Chosen**: KVM VMs

**Alternatives considered**: Docker, LXC, native installation

**Rationale**:
- **Identity separation**: Each agent needs distinct MAC, IP, SSH identity for GitHub, Discord, etc.
- **Full OS isolation**: Complete Debian userspace per agent
- **Cloud-init**: Native cloud image provisioning is fast and clean
- **Snapshot capability**: `qm snapshot` for easy rollback

### Decision 3: VM Distribution Strategy

**Chosen**: Distribute by host RAM headroom

| Host | RAM | VMs | Committed | Headroom |
|------|-----|-----|-----------|---------|
| r420 | 70G | 2 | 32G | 38G |
| r8202 | 51G | 1 | 16G | 35G |
| r720xd | 94G | 2 | 32G | 62G |
| r820 | 377G | 3 | 48G | 329G |

r8202 gets only 1 VM due to its 51G RAM being the most constrained.
r820 is intentionally under-provisioned to leave headroom for future expansion.

### Decision 4: ZFS Pool Naming

**Chosen**: `nvme-fast` (always) + `sas-data` (where SAS disks exist)

**Rationale**:
- Consistent naming across hosts makes playbooks host-agnostic
- `nvme-fast` used for VM disk images (IOPS-sensitive)
- `sas-data` used for bulk content (backup, ISO, snippets) where latency matters less

### Decision 5: Cloud Image Template Approach

**Chosen**: Download Ubuntu cloud image once on master, convert to Proxmox template (VM 9000), clone per VM

**Rationale**:
- Download once vs 8 times
- `qm clone --full true` creates fully independent copy on nvme-fast
- Cloud-init handles per-VM customization (user, SSH keys, network, hostname)
- Future re-provisioning is fast: destroy + clone takes ~2 minutes

### Decision 6: Ansible Deployment Automation

**Role structure**:
```
role/
├── defaults/main.yml    # reset: false, config vars
├── tasks/main.yml       # Routes to setup or reset based on `reset` var
├── tasks/setup.yml      # Idempotent installation
└── tasks/reset.yml      # Cleanup (runs when reset=true)
```

**Playbook phase tags** allow running individual phases without the full pipeline.

---

## Network Topology

### IP Allocation

```
Network: 10.220.1.0/24
Gateway / DNS: 10.220.1.1 (UniFi UDM)

Proxmox hosts (physical):
  r420:    10.220.1.7   (Proxmox master)
  r8202:   10.220.1.8   (Proxmox node)
  r720xd:  10.220.1.10  (Proxmox node)
  r820:    10.220.1.11  (Proxmox node)

Agent VMs (static DHCP reservations on UDM, MAC-based):
  Zeus:       10.220.1.50   MAC: 52:54:00:80:70:b5
  Athena:     10.220.1.51   MAC: 52:54:00:78:c4:0f
  Apollo:     10.220.1.52   MAC: 52:54:00:64:b0:5e
  Artemis:    10.220.1.53   MAC: 52:54:00:80:1a:26
  Hermes:     10.220.1.54   MAC: 52:54:00:05:26:d8
  Perseus:    10.220.1.55   MAC: 52:54:00:58:86:1c
  Prometheus: 10.220.1.56   MAC: 52:54:00:7c:57:d6
  Ares:       10.220.1.57   MAC: 52:54:00:ac:09:45
```

### Connectivity Matrix

| From | To | Protocol | Port | Purpose |
|------|-----|----------|------|---------|
| Ansible (localhost) | Proxmox hosts | SSH | 22 | Cluster management (user: root) |
| Ansible (localhost) | Agent VMs | SSH | 22 | Agent stack deployment (user: agent) |
| Agent VMs | Internet | HTTPS | 443 | API calls, git, packages |
| Agent VMs | GitHub | SSH | 22 | Git operations |
| Agent VMs | Agent VMs | any | any | Inter-agent coordination |

---

## Data Flow

### Work Assignment Flow

```
Human (Jeff)
    │  Discord / direct
    ▼
Zeus (PM — 10.220.1.50)
    │  GitHub API → creates issue
    ▼
GitHub Issue Queue
    │  assigned to agent
    ▼
Developer Agent (e.g. Apollo)
    │  1. git clone → 2. code → 3. PR
    ▼
Pull Request
    │  peer reviews
    ▼
Reviewer Agents (Artemis, Hermes, Perseus)
    │  approvals
    ▼
Human Approval Gate
    │  merge
    ▼
Production (AWS)
```

### Communication Flow

Each agent connects to:
- **Discord** — team channel for discussion and coordination
- **GitHub** — issues, PRs, code review
- **Ollama** (local) + **Cloud APIs** (Anthropic, OpenAI, Google) for LLM inference

---

## Security Model

### Authentication Layers

1. **Proxmox hosts**: SSH key auth as `root` (Ansible automation), Proxmox web UI with local PAM
2. **Proxmox API**: `ansible@pam` token (`ansible-token`) with `PVEAdmin` role
3. **Agent VMs**: SSH key auth as `agent` user, sudo NOPASSWD
4. **GitHub**: Per-agent SSH keys (generated during `agent_provision`)
5. **LLM APIs**: API keys in Ansible vault, deployed to `~/.openclaw/.env` (mode 0600)

### Secrets Management

**Ansible Vault** (`group_vars/all/all.yml`):
- Discord bot tokens per agent
- SSH become password
- Docker Hub token
- Proxmox API token secret (`proxmox_api_token_secret`)

### Isolation Boundaries

1. **VM isolation**: Full KVM hardware virtualization
2. **Network**: Private 10.220.1.0/24, UDM firewall controls external access
3. **Process**: Systemd service per agent with restricted user
4. **Credentials**: Per-agent SSH keys, no shared secrets between VMs

---

## Scalability

### Current Utilization

| Resource | Committed | Available | Headroom |
|----------|-----------|-----------|---------|
| RAM | 128G | 592G | 78% free |
| VM disk | 2TB | ~28T (nvme-fast across all hosts) | ~93% free |
| vCPUs | 32 | 144 | 78% free |

### Expansion Options

**Add agents** (r820 has 329G free RAM — can host 20+ more VMs):
1. Add entry to `agents` dict in `proxmox_vm/defaults/main.yml`
2. Add to `agent_vms` inventory group
3. Run `proxmox_vm` role tag + agent stack playbooks

**Add Proxmox nodes**:
- Install PVE, add to inventory under `proxmox_nodes`
- Run `proxmox_base` → `pvecm add` → `proxmox_storage`

**Local LLM inference**:
- Add GPU server running Ollama
- Agents already configured to use Ollama as inference option

---

**Last Updated**: 2026-02-28
**Maintainer**: jeff@infiquetra.com
