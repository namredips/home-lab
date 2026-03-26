# Architecture Overview

Technical architecture and design decisions for the Olympus agent infrastructure.

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
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Physical Layer                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│  │  r420  │ │ r640-1 │ │ r640-2 │ │ r720xd │ │  r820  │ │ r640-3 │         │
│  │ 70G/24C│ │125G/72C│ │125G/72C│ │ 94G/24C│ │377G/64C│ │125G/72C│         │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘         │
└──────┼──────────┼──────────┼──────────┼──────────┼──────────┼───────────────┘
       │          │          │          │          │          │
┌──────▼──────────▼──────────▼──────────▼──────────▼──────────▼───────────────┐
│              Hypervisor Layer — Proxmox VE 9.1.1 (Debian Trixie)             │
│              Cluster "olympus" — 6-node corosync quorum                      │
│                                                                               │
│  r420 (master)  r640-1       r640-2       r720xd     r820       r640-3       │
│  ├─ Artemis     ├─ Apollo    ├─ Athena    ├─ Ares    ├─ Zeus    ├─ Monitor.  │
│  └─ Hephaestus  └─ Perseus   └─ Prometheus           └─ RustDesk            │
│                                                                               │
│  Ceph distributed storage:                                                    │
│  ceph-fast (NVMe/SSD on R640s) — VM disks                                   │
│  ceph-bulk (SAS HDDs) — backups, ISOs                                        │
│  Ceph network: 10.220.2.0/24 via vmbr1 (10GbE)                              │
└──────────────────────────────────────────────────────────────────────────────┘
       │          │          │          │          │          │
┌──────▼──────────▼──────────▼──────────▼──────────▼──────────▼───────────────┐
│                      Network Layer (10.220.1.0/24)                            │
│                      Gateway/DNS: 10.220.1.1 (UniFi UDM)                     │
│                      Ceph cluster: 10.220.2.0/24 (dedicated 10GbE)           │
│                                                                               │
│  Agent VMs: 10.220.1.50–57  (static DHCP via MAC reservations)               │
│  Service VMs: 10.220.1.60–64                                                 │
│  Mac Mini: 10.220.1.2 (control node)                                         │
└──────────────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                     │
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Hermes    │  │   Ollama    │  │   GitHub    │  │   Beads     │        │
│  │  Conductor  │  │  (local LLM)│  │  (external) │  │  (Dolt DB)  │        │
│  │  (mac mini) │  │  per-VM     │  │  - Repos    │  │  olympus-bus│        │
│  │  → claude   │  │             │  │  - Issues   │  │  - bd CLI   │        │
│  │  → gemini   │  │             │  │  - PRs      │  │  - sync svc │        │
│  │  → codex    │  │             │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                               │
│  Execution model:                                                             │
│  Hermes (ChatGPT/OpenAI) → invokes CLI tools for specialized execution       │
│  ├─ claude (Anthropic)   — complex reasoning, code, security                 │
│  ├─ gemini (Google)      — vision, code review                               │
│  ├─ codex (OpenAI)       — refactoring                                       │
│  ├─ Ollama cloud         — drafting, documentation                           │
│  ├─ bd (beads CLI)       — task coordination                                 │
│  └─ gh (GitHub CLI)      — issues, PRs, reviews                              │
└──────────────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────────┐
│                    Coordination & Messaging Layer                             │
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │   Redis     │  │   Discord   │  │   Dolt      │                         │
│  │  pub/sub    │  │  (human UI) │  │  (bead DB)  │                         │
│  │ olympus-bus │  │  bridge ←───│──│─ sync svc   │                         │
│  │ 10.220.1.64 │  │  channels:  │  │             │                         │
│  │  :6379      │  │  #agent-*   │  │             │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────────┐
│                       External Services Layer                                │
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Anthropic  │  │   OpenAI    │  │   Google    │  │   Discord   │       │
│  │  Claude API │  │  ChatGPT   │  │  Gemini API │  │     API     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Physical Infrastructure

| Server | Role | RAM | vCPU | Ceph Fast Disks | Ceph Bulk Disks | VMs Hosted |
|--------|------|-----|------|-----------------|-----------------|------------|
| **r420** | Proxmox master | 70G | 24 | — | sdb-sdd (3x931G SAS) | Artemis, Hephaestus |
| **r640-1** | Proxmox node | 125G | 72 | nvme0n1+nvme1n1+sdc-sdf (6 disks) | — | Apollo, Perseus |
| **r640-2** | Proxmox node | 125G | 72 | nvme0n1+nvme1n1+sdc-sdd (4 disks) | — | Athena, Prometheus |
| **r720xd** | Proxmox node | 94G | 24 | — | sdb-sdl (11x SAS) | Ares, PBS |
| **r820** | Proxmox node | 377G | 64 | — | sdb-sdd (3x RAID VDs) | Zeus, RustDesk, Dell OME |
| **r640-3** | Proxmox node | 125G | 72 | nvme0n1+sdc-sdd (3 disks) | — | Monitoring |

**Total capacity**: ~916G RAM, 328 vCPUs across 6 servers

#### Virtual Machine Layer

| VMID | Agent | Host | vCPU | RAM | Disk | Role | IP |
|------|-------|------|------|-----|------|------|----|
| 100 | Zeus | r820 | 4 | 8G | 250G | PM, Orchestration | 10.220.1.50 |
| 101 | Athena | r640-2 | 4 | 16G | 250G | Senior Dev (Architecture) | 10.220.1.51 |
| 102 | Apollo | r640-1 | 4 | 16G | 250G | Dev (Code Quality) | 10.220.1.52 |
| 103 | Artemis | r420 | 4 | 16G | 250G | Dev (Testing) | 10.220.1.53 |
| 104 | Hephaestus | r420 | 4 | 16G | 250G | Dev (Infrastructure) | 10.220.1.54 |
| 105 | Perseus | r640-1 | 4 | 16G | 250G | Dev (Complex Problems) | 10.220.1.55 |
| 106 | Prometheus | r640-2 | 4 | 16G | 250G | Dev (Innovation) | 10.220.1.56 |
| 107 | Ares | r720xd | 4 | 16G | 250G | Dev (Performance) | 10.220.1.57 |

#### Service VMs

| VMID | Name | Host | IP | Purpose |
|------|------|------|----|---------|
| 200 | RustDesk | r820 | 10.220.1.60 | Remote desktop relay |
| 201 | Dell OME | r820 | 10.220.1.61 | Hardware management |
| 202 | PBS | r720xd | 10.220.1.62 | Proxmox Backup Server |
| 203 | Monitoring | r640-3 | 10.220.1.63 | Prometheus + Grafana |
| 204 | olympus-bus | — | 10.220.1.64 | Redis + Dolt + Discord bridge |

**OS**: Ubuntu 24.04 LTS (cloud image, provisioned via Proxmox cloud-init)
**Access**: SSH key authentication (agent user)
**Template**: VM ID 9000 on r420 (clone source for all VMs)

#### Ceph Storage

| Pool | Device Class | Hosts | Purpose |
|------|-------------|-------|---------|
| `ceph-fast` | NVMe/SSD | r640-1, r640-2, r640-3 | VM disks (IOPS-sensitive) |
| `ceph-bulk` | HDD/SAS | r420, r720xd, r820 | Backups, ISOs, bulk data |

Ceph cluster network runs on dedicated 10GbE interfaces (10.220.2.0/24) via vmbr1 on each host.

---

## Design Decisions

### Decision 1: Proxmox VE over bare-metal Ubuntu + libvirt

**Chosen**: Proxmox VE 9.1.1 (Debian Trixie)

**Previous approach**: Ubuntu 22.04 + libvirt/KVM + Ansible-managed VMs

**Rationale**:
- **Native cluster management**: `pvecm` handles quorum, live migration, HA without extra software
- **Web UI**: Proxmox web console for emergency access without Ansible
- **Ceph integration**: Native Ceph management in Proxmox GUI and CLI
- **Cloud-init support**: `qm set --ide2 storage:cloudinit` native, no virt-install overhead
- **Template cloning**: `qm clone` is significantly faster than virt-install from ISO

**Trade-offs**:
- No-subscription nag (cosmetic, suppressed via no-sub repo)
- Less familiar than Ubuntu for host-level debugging

### Decision 2: Ceph over ZFS

**Chosen**: Ceph Squid (distributed storage)

**Previous approach**: Per-host ZFS pools (nvme-fast + sas-data)

**Rationale**:
- **Distributed redundancy**: Data survives host failure without manual intervention
- **Live migration**: VMs can migrate between hosts without shared filesystem hacks
- **Tiered storage**: CRUSH rules route VMs to NVMe (ceph-fast) and bulk to HDD (ceph-bulk)
- **Scale-out**: Adding a new host automatically expands storage capacity

**Trade-offs**:
- Higher network overhead (dedicated 10GbE Ceph network mitigates this)
- More complex than single-host ZFS

### Decision 3: VMs over Containers

**Chosen**: KVM VMs

**Alternatives considered**: Docker, LXC, native installation

**Rationale**:
- **Identity separation**: Each agent needs distinct MAC, IP, SSH identity for GitHub, Discord, etc.
- **Full OS isolation**: Complete Debian userspace per agent
- **Cloud-init**: Native cloud image provisioning is fast and clean
- **Snapshot capability**: `qm snapshot` for easy rollback

### Decision 4: VM Distribution Strategy

**Chosen**: Distribute across all 6 hosts by RAM headroom and storage class

| Host | RAM | VMs | Committed | Headroom |
|------|-----|-----|-----------|---------|
| r420 | 70G | 2 | 32G | 38G |
| r640-1 | 125G | 2 | 32G | 93G |
| r640-2 | 125G | 2 | 32G | 93G |
| r720xd | 94G | 1 | 16G | 78G |
| r820 | 377G | 1 | 8G | 369G |
| r640-3 | 125G | 0 agent | 0G | 125G |

r820 is intentionally under-provisioned for future expansion.

### Decision 5: Hermes as Orchestrator with CLI Tools

**Chosen**: Hermes (ChatGPT/OpenAI OAuth) as the central orchestrator, invoking specialized CLI tools

**Rationale**:
- **Best-of-breed routing**: Each task type uses the optimal model/tool
- **Cost efficiency**: Draft with cheap models (Ollama), refine with quality (Claude)
- **Extensible**: Adding a new tool is just adding a CLI binary
- **Observable**: Each tool invocation is a discrete, loggable operation

See [Model Routing Guide](MODEL_ROUTING_GUIDE.md) for the full routing table.

### Decision 6: Beads + Redis for Coordination

**Chosen**: Beads (Dolt-backed task DB) + Redis pub/sub + Discord bridge

**Previous approach**: Direct GitHub polling + Mattermost announcements

**Rationale**:
- **Atomic claims**: `bd update --claim` prevents double-assignment
- **Real-time events**: Redis pub/sub is millisecond-latency, no polling
- **Human visibility**: Discord bridge selectively surfaces key events
- **Single source of truth**: GitHub Issues remain authoritative; beads syncs every 5 minutes

### Decision 7: Ansible Deployment Automation

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

Control node:
  Mac Mini:  10.220.1.2   (conductor, Hermes + Freya)

Proxmox hosts (physical):
  r420:      10.220.1.7   (Proxmox master)
  r640-1:    10.220.1.8   (Proxmox node)
  r640-2:    10.220.1.9   (Proxmox node)
  r720xd:    10.220.1.10  (Proxmox node)
  r820:      10.220.1.11  (Proxmox node)
  r640-3:    10.220.1.12  (Proxmox node)

iDRAC (physical, offset +10):
  r420:      10.220.1.17
  r640-1:    10.220.1.18
  r640-2:    10.220.1.19
  r720xd:    10.220.1.20
  r820:      10.220.1.21
  r640-3:    10.220.1.22

Agent VMs (static DHCP, MAC-based):
  Zeus:         10.220.1.50
  Athena:       10.220.1.51
  Apollo:       10.220.1.52
  Artemis:      10.220.1.53
  Hephaestus:   10.220.1.54
  Perseus:      10.220.1.55
  Prometheus:   10.220.1.56
  Ares:         10.220.1.57

Service VMs:
  RustDesk:     10.220.1.60
  Dell OME:     10.220.1.61
  PBS:          10.220.1.62
  Monitoring:   10.220.1.63
  olympus-bus:  10.220.1.64

Ceph cluster network: 10.220.2.0/24 (vmbr1, dedicated 10GbE)
  r420:      10.220.2.7
  r640-1:    10.220.2.8
  r640-2:    10.220.2.9
  r720xd:    10.220.2.10
  r820:      10.220.2.11
  r640-3:    10.220.2.12
```

### Connectivity Matrix

| From | To | Protocol | Port | Purpose |
|------|-----|----------|------|---------|
| Mac Mini | Proxmox hosts | SSH | 22 | Cluster management (user: root) |
| Mac Mini | Agent VMs | SSH | 22 | Agent stack deployment (user: agent) |
| Agent VMs | Internet | HTTPS | 443 | API calls, git, packages |
| Agent VMs | GitHub | SSH | 22 | Git operations |
| Agent VMs | olympus-bus | TCP | 6379 | Redis pub/sub |
| Agent VMs | olympus-bus | TCP | 3306 | Dolt SQL (beads) |
| Agent VMs | Agent VMs | any | any | Inter-agent coordination |
| Proxmox hosts | Proxmox hosts | TCP | various | Ceph, corosync, migration |

---

## Data Flow

### Work Assignment Flow

```
Human (Jeff)
    │  Discord / GitHub Issue
    ▼
GitHub Issues (source of truth)
    │  sync every 5 min
    ▼
Beads (Dolt DB on olympus-bus)
    │  bd ready → bd update --claim
    ▼
Agent claims work
    │  Redis: olympus:task:claimed
    │  Discord bridge → #agent-updates
    ▼
Developer Agent (e.g. Apollo)
    │  1. git clone → 2. code → 3. PR
    ▼
Pull Request (gh pr create)
    │  Redis: olympus:review:requested
    │  Discord bridge → #agent-sync
    ▼
Reviewer Agents
    │  gh pr review → approve
    ▼
Human Approval Gate
    │  merge
    ▼
Production
```

### Communication Flow

Each agent connects to:
- **Beads/Dolt** (olympus-bus) — task discovery and claiming
- **Redis** (olympus-bus) — real-time event pub/sub
- **Discord** (via bridge) — human-visible status updates
- **GitHub** — issues, PRs, code review
- **Ollama** (local) + **Cloud APIs** (Anthropic, OpenAI, Google) for LLM inference

---

## Security Model

### Authentication Layers

1. **Proxmox hosts**: SSH key auth as `root` (Ansible automation), Proxmox web UI with local PAM
2. **Proxmox API**: `ansible@pam` token (`ansible-token`) with `PVEAdmin` role
3. **Agent VMs**: SSH key auth as `agent` user, sudo NOPASSWD
4. **GitHub**: Per-agent SSH keys (generated during `agent_provision`)
5. **LLM APIs**: API keys in Ansible vault, deployed to agent home directories (mode 0600)
6. **Discord**: Per-agent bot tokens stored in Ansible vault

### Secrets Management

**Ansible Vault** (`group_vars/all/all.yml`):
- Discord bot tokens per agent (`vault_discord_bot_token_<name>`)
- Hermes conductor token (`vault_hermes_conductor_token`)
- Freya token (`vault_discord_bot_token_freya`)
- SSH become password
- Proxmox API token secret (`proxmox_api_token_secret`)

### Isolation Boundaries

1. **VM isolation**: Full KVM hardware virtualization
2. **Network**: Private 10.220.1.0/24, UDM firewall controls external access
3. **Process**: Systemd service per agent with restricted user
4. **Credentials**: Per-agent SSH keys and bot tokens, no shared secrets between VMs
5. **Ceph**: Dedicated 10.220.2.0/24 network isolated from VM traffic

---

## Scalability

### Current Utilization

| Resource | Committed | Available | Headroom |
|----------|-----------|-----------|---------|
| RAM | ~120G | ~916G | 87% free |
| vCPUs | 32 | 328 | 90% free |
| Ceph Fast | ~2TB used | variable | Expandable per-host |
| Ceph Bulk | ~2TB used | variable | Expandable per-host |

### Expansion Options

**Add agents** (r820 has 369G free RAM — can host 20+ more VMs):
1. Add entry to `agents` dict in `proxmox_vm/defaults/main.yml`
2. Add to `agent_vms` inventory group
3. Run `proxmox_vm` role tag + agent stack playbooks

**Add Proxmox nodes**:
- Install PVE, add to inventory under `proxmox_nodes`
- Run `proxmox_base` → `pvecm add` → Ceph install → OSD creation

**Local LLM inference**:
- Ollama installed per-VM for local model execution
- Add GPU server for accelerated inference if needed

---

**Last Updated**: 2026-03-25
**Maintainer**: jeff@infiquetra.com
