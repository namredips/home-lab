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
┌─────────────────────────────────────────────────────────────────────────┐
│                          Physical Layer                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   r420   │  │   r710   │  │  r8202   │  │  r720xd  │  │   r820   │  │
│  │ 32GB RAM │  │ 64GB RAM │  │ 64GB RAM │  │ 128GB RAM│  │ 128GB RAM│  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │             │         │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼─────────────▼─────────┐
│                    Hypervisor Layer (KVM/libvirt)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Athena   │  │ Apollo   │  │ Hermes   │  │ Perseus  │  │Prometheus│  │
│  │ 8GB RAM  │  │ Artemis  │  │ 16GB RAM │  │ 16GB RAM │  │ Ares     │  │
│  │          │  │ 32GB RAM │  │          │  │          │  │ Poseidon │  │
│  │          │  │          │  │          │  │          │  │ 48GB RAM │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  │
└────────┼─────────────┼─────────────┼─────────────┼─────────────┼────────┘
         │             │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼─────────────▼────────┐
│                      Network Layer (10.220.1.0/24)                       │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Agent VMs: 10.220.1.50-57  │  Mattermost: 10.220.1.10:8065      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
         │             │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼─────────────▼────────┐
│                      Application Layer                                   │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  OpenClaw    │  │  Mattermost  │  │   GitHub     │                  │
│  │  Agents      │  │  (Self-host) │  │  (External)  │                  │
│  │              │  │              │  │              │                  │
│  │  - Memory    │  │  - Postgres  │  │  - Repos     │                  │
│  │  - Tasks     │  │  - Chat      │  │  - Issues    │                  │
│  │  - Dashboard │  │  - Webhooks  │  │  - PRs       │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
         │             │             │
┌────────▼─────────────▼─────────────▼────────────────────────────────────┐
│                      External Services Layer                             │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  Anthropic   │  │   OpenAI     │  │   Google     │                  │
│  │  Claude API  │  │   GPT API    │  │  Gemini API  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Physical Infrastructure

| Server | Role | CPU | RAM | Storage | VMs Hosted |
|--------|------|-----|-----|---------|------------|
| **r420** | Light orchestration | Lower | 32GB | 836GB | Athena |
| **r710** | Dev pool | Medium | 64GB | 852GB | Apollo, Artemis |
| **r8202** | Dev pool | Medium | 64GB | 851GB | Hermes |
| **r720xd** | Services + dev | Medium | 128GB | 852GB+ | Perseus, Mattermost |
| **r820** | Heavy compute | High | 128GB | 851GB | Prometheus, Ares, Poseidon |

**Total capacity**: 416GB RAM, 4.2TB storage across 5 servers

**Utilization**: 120GB RAM (29%), 2TB storage (48%)

#### Virtual Machine Layer

| VM | Host | vCPU | RAM | Disk | Role | IP |
|----|------|------|-----|------|------|----|
| Athena | r420 | 4 | 8GB | 250GB | PM, Orchestration | 10.220.1.50 |
| Apollo | r710 | 4 | 16GB | 250GB | Development | 10.220.1.51 |
| Artemis | r710 | 4 | 16GB | 250GB | Development | 10.220.1.52 |
| Hermes | r8202 | 4 | 16GB | 250GB | Development | 10.220.1.53 |
| Perseus | r720xd | 4 | 16GB | 250GB | Development | 10.220.1.54 |
| Prometheus | r820 | 4 | 16GB | 250GB | Development | 10.220.1.55 |
| Ares | r820 | 4 | 16GB | 250GB | Development | 10.220.1.56 |
| Poseidon | r820 | 4 | 16GB | 250GB | Development | 10.220.1.57 |

**OS**: Ubuntu 22.04 LTS (cloud image)
**Provisioning**: Cloud-init with static IPs
**Access**: SSH key authentication (agent user)

#### Application Services

**Mattermost** (r720xd):
- **Purpose**: Self-hosted team communication
- **Components**:
  - PostgreSQL 13 (database)
  - Mattermost Team Edition 9.5 (app)
- **Deployment**: Docker Compose
- **Port**: 8065 (HTTP)
- **Data**: `/opt/mattermost/data`

**OpenClaw** (all VMs):
- **Purpose**: AI agent orchestration
- **Components**:
  - Node.js 22 runtime
  - OpenClaw CLI (npm global package)
  - Systemd service per agent
- **Config**: `~/.openclaw/config.yml`
- **Logs**: `~/.openclaw/logs/`
- **Dashboard**: Port 18789 per agent

**Development Environment** (all VMs):
- Languages: Python 3.12, Node 22, Dart, Rust, Go, C/C++
- Tools: Docker, AWS CLI, AWS CDK, GitHub CLI
- Editors: Neovim (custom config), VS Code
- Shell: Bash with Starship prompt

---

## Design Decisions

### Decision 1: VMs vs Containers

**Chosen**: KVM/libvirt VMs

**Alternatives considered**:
1. Docker containers
2. LXC containers
3. Native installation

**Rationale**:
- **Identity separation**: Each agent needs distinct identity for Slack, Discord, GitHub, etc.
- **Full isolation**: Complete OS environment per agent
- **Snapshot capability**: Easy backup and rollback
- **Desktop support**: Can run GUI apps if needed (VNC/SPICE)

**Trade-offs**:
- Higher resource overhead (~8GB RAM per VM vs ~2GB for containers)
- Slower startup time (minutes vs seconds)
- More complex networking

### Decision 2: AI-Native Team Model

**Chosen**: Generalists with situational "hats"

**Alternatives considered**:
1. Fixed specialization (backend, frontend, QA agents)
2. Single multi-purpose agent
3. Swarm of identical agents

**Rationale**:
- **Modern AI capabilities**: Claude/GPT are full-stack capable
- **Flexible collaboration**: Any agent can review with any lens
- **Realistic team dynamics**: Mirrors human cross-functional reviews
- **Scalability**: Add agents without specialization constraints

**Example**:
```
Apollo writes API code
  → Artemis reviews (infrastructure lens)
  → Hermes reviews (mobile/UX lens)
  → Perseus reviews (security lens)
All capable of writing the same code, different review perspectives
```

### Decision 3: Shared vs Individual LLM Accounts

**Chosen**: Shared API subscriptions (Phase 1)

**Rationale**:
- **Cost savings**: ~$60/month for all agents vs ~$500/month individual
- **Simplicity**: Single set of credentials to manage
- **Rate limiting**: Still need to monitor across all agents
- **Future**: Can migrate to individual accounts as needed

**Migration path**:
- Phase 2: Individual accounts per agent
- Phase 3: Local inference (Ollama) on dedicated hardware

### Decision 4: Communication Platform

**Chosen**: Mattermost (self-hosted)

**Alternatives considered**:
1. Slack (cloud, $8/user/month)
2. Discord (cloud, free but gaming-focused)
3. Matrix (self-hosted, complex)
4. Custom solution

**Rationale**:
- **Cost**: $0 (self-hosted, unlimited users)
- **Control**: Full data ownership
- **Familiarity**: Slack-like UX
- **Integration**: Webhooks, bots, API
- **Realistic**: Mirrors real team collaboration

### Decision 5: Email Strategy

**Chosen**: Google Workspace catch-all routing

**Alternatives considered**:
1. Individual Google Workspace users ($6/user/month)
2. Self-hosted email (Mailcow, Mailu)
3. No email (use Mattermost only)

**Rationale**:
- **Cost**: $0 vs $48/month
- **Simplicity**: Single inbox for all verification emails
- **Reliability**: Google's email infrastructure
- **Trade-off**: Manual checking required

**Savings**: $576/year

### Decision 6: Deployment Automation

**Chosen**: Ansible roles with setup/reset pattern

**Rationale**:
- **Idempotency**: Can re-run safely
- **Modularity**: Each role is independent
- **Rollback**: Reset playbook for cleanup
- **Consistency**: Same pattern across all roles

**Role structure**:
```
role/
├── defaults/main.yml    # reset: False, config
├── tasks/main.yml       # Routes to setup or reset
├── tasks/setup.yml      # Installation
└── tasks/reset.yml      # Cleanup
```

### Decision 7: VM Distribution Strategy

**Chosen**: Balanced distribution across hypervisors

**Distribution**:
- r420: 1 VM (8GB) - lightest server for orchestrator
- r710: 2 VMs (32GB) - balanced dev agents
- r8202: 1 VM (16GB) - balanced
- r720xd: 1 VM + services (16GB) - storage-rich server
- r820: 3 VMs (48GB) - highest capacity, leaves 80GB free

**Rationale**:
- Spreads load across servers
- r820 has headroom for future expansion
- Mattermost on r720xd (separate from heavy compute)
- Orchestrator on r420 (dedicated, always-on)

---

## Network Topology

### IP Allocation

```
Network: 10.220.1.0/24
Gateway: 10.220.1.1
DNS: 8.8.8.8, 8.8.4.4

┌─────────────────────────────────────────────────────────┐
│  Hypervisors (Physical Servers)                         │
│  ├─ r420:    10.220.1.7                                 │
│  ├─ r8202:   10.220.1.8                                 │
│  ├─ r710:    10.220.1.9                                 │
│  ├─ r720xd:  10.220.1.10                                │
│  └─ r820:    10.220.1.11                                │
├─────────────────────────────────────────────────────────┤
│  Agent VMs (Static IPs via cloud-init)                  │
│  ├─ Athena:     10.220.1.50                             │
│  ├─ Apollo:     10.220.1.51                             │
│  ├─ Artemis:    10.220.1.52                             │
│  ├─ Hermes:     10.220.1.53                             │
│  ├─ Perseus:    10.220.1.54                             │
│  ├─ Prometheus: 10.220.1.55                             │
│  ├─ Ares:       10.220.1.56                             │
│  └─ Poseidon:   10.220.1.57                             │
├─────────────────────────────────────────────────────────┤
│  Services                                                │
│  └─ Mattermost: 10.220.1.10:8065 (r720xd)              │
└─────────────────────────────────────────────────────────┘
```

### Connectivity Matrix

| From | To | Protocol | Port | Purpose |
|------|-----|----------|------|---------|
| Agent VMs | Hypervisors | SSH | 22 | Management |
| Agent VMs | Mattermost | HTTP | 8065 | Team communication |
| Agent VMs | Internet | HTTPS | 443 | API calls, git, packages |
| Agent VMs | GitHub | SSH | 22 | Git operations |
| Local workstation | Agent VMs | SSH | 22 | Admin access |
| Local workstation | Mattermost | HTTP | 8065 | Web UI |
| Local workstation | Agent dashboards | HTTP | 18789 | OpenClaw UI |

### Firewall Rules

**Agent VMs** (ufw):
```
Allow 22/tcp (SSH)
Allow 18789/tcp (OpenClaw dashboard)
Allow outbound all
```

**Mattermost host**:
```
Allow 22/tcp (SSH)
Allow 8065/tcp (Mattermost)
Allow outbound all
```

---

## Data Flow

### Work Assignment Flow

```
┌─────────┐
│  Human  │
│  (Jeff) │
└────┬────┘
     │
     │ Mattermost message
     │ "@athena create issue for TODO app"
     │
     ▼
┌──────────┐
│  Athena  │ (Orchestrator)
│   10.220.1.50│
└────┬────┘
     │
     │ GitHub API
     │ Creates issue #123
     │
     ▼
┌─────────────────────┐
│  GitHub Repository  │
│  Issues, PRs        │
└────┬────────────────┘
     │
     │ Notification
     │ or Pull
     │
     ▼
┌──────────┐
│  Apollo  │ (Developer)
│   10.220.1.51│
└────┬────┘
     │
     │ 1. git clone
     │ 2. git checkout -b feature
     │ 3. Code changes
     │ 4. git push
     │ 5. gh pr create
     │
     ▼
┌─────────────────────┐
│  Pull Request #45   │
│  Awaiting review    │
└────┬────────────────┘
     │
     │ Automated reviews
     │
     ▼
┌──────────┬──────────┬──────────┐
│ Artemis  │ Hermes   │ Perseus  │
│ (Infra)  │ (UX)     │ (Sec)    │
└────┬─────┴────┬─────┴────┬─────┘
     │          │          │
     └──────────┼──────────┘
                │
                │ All approvals
                │
                ▼
         ┌─────────────┐
         │  Human      │
         │  Approval   │
         └──────┬──────┘
                │
                │ Merge + Deploy
                │
                ▼
         ┌─────────────┐
         │  Production │
         │  (AWS)      │
         └─────────────┘
```

### Communication Flow

```
Mattermost ◄──┬──► Athena
              │
              ├──► Apollo
              │
              ├──► Artemis
              │
              ├──► Hermes
              │
              ├──► Perseus
              │
              ├──► Prometheus
              │
              ├──► Ares
              │
              └──► Poseidon

Each agent:
  - Listens on Mattermost channels
  - Responds to @mentions
  - Posts updates on task progress
  - Coordinates with other agents
```

---

## Security Model

### Authentication Layers

1. **Hypervisor Access**:
   - SSH key authentication (jefcox user)
   - No password login
   - Limited to local network

2. **VM Access**:
   - SSH key authentication (agent user)
   - Unique keys per admin
   - Sudo with NOPASSWD for agent user

3. **Service Authentication**:
   - Mattermost: Username/password + bot tokens
   - GitHub: SSH keys + personal access tokens
   - AI APIs: API keys in vault

### Secrets Management

**Ansible Vault**:
```
ansible/passwd.yml (encrypted)
├── vault_mattermost_postgres_password
├── vault_mattermost_bot_token
├── vault_openclaw_anthropic_api_key
├── vault_openclaw_openai_api_key
└── vault_openclaw_google_api_key
```

**VM Environment Files**:
```
~/.openclaw/.env (mode 0600)
├── ANTHROPIC_API_KEY
├── OPENAI_API_KEY
├── GOOGLE_API_KEY
└── MATTERMOST_BOT_TOKEN
```

### Isolation Boundaries

1. **VM Isolation**: Full OS separation via KVM
2. **Network Isolation**: Private network (10.220.1.0/24)
3. **Process Isolation**: Systemd services per agent
4. **Data Isolation**: Separate home directories

### Deployment Gates

Human approval required for:
- Production deployments
- Infrastructure changes
- Sensitive data access
- Destructive operations

---

## Scalability

### Current Capacity

| Resource | Used | Available | Utilization |
|----------|------|-----------|-------------|
| RAM | 120GB | 416GB | 29% |
| Disk | 2TB | 4.2TB | 48% |
| vCPUs | 32 | ~100+ | ~30% |
| VMs | 8 | ~40+ | ~20% |

### Expansion Options

**Add more agents** (up to ~40 VMs with current hardware):
- 3-4 VMs per hypervisor
- Each VM: 16GB RAM, 4 vCPUs, 250GB disk

**Add more hypervisors**:
- Additional Dell servers
- Same libvirt/KVM setup
- Join to same network

**Vertical scaling** (per VM):
- Increase vCPUs: 4 → 8
- Increase RAM: 16GB → 32GB
- Increase disk: 250GB → 500GB

**Local LLM inference**:
- Add dedicated GPU server
- Run Ollama for local inference
- Reduce API costs

### Resource Planning

**Per agent VM**:
- Light workload: 8GB RAM, 2 vCPUs
- Medium workload: 16GB RAM, 4 vCPUs
- Heavy workload: 32GB RAM, 8 vCPUs

**Growth scenarios**:
1. **10 agents**: Fits comfortably (160GB RAM)
2. **15 agents**: Still feasible (240GB RAM)
3. **20 agents**: Approaching limit (320GB RAM)
4. **25+ agents**: Need additional hardware

---

## Future Architecture

### Phase 2: Local Inference

```
Current: Agent VMs → Cloud APIs (Anthropic, OpenAI, Google)

Future:
┌─────────────┐
│  Agent VMs  │
└──────┬──────┘
       │
       ├──► Cloud APIs (fallback, high-quality)
       │
       └──► Ollama Server (local, fast, private)
            ├─ RTX 4090 (24GB VRAM)
            ├─ Llama 3 70B (quantized)
            └─ Mixtral 8x7B
```

**Benefits**:
- Lower costs (no per-token charges)
- Faster response (local network)
- Data privacy (no external calls)

**Requirements**:
- Dedicated GPU server
- 48GB+ VRAM for large models
- High-speed storage (NVMe)

### Phase 3: Expanded Team

```
Current: 1 PM + 7 Developers

Future:
├─ Product Team (3)
│  ├─ Athena (PM)
│  ├─ Demeter (Product Designer)
│  └─ Hestia (UX Researcher)
│
├─ Development Team (10)
│  ├─ Apollo, Artemis, Hermes, Perseus,
│  ├─ Prometheus, Ares, Poseidon (existing)
│  └─ Dionysus, Hephaestus, Heracles (new)
│
├─ QA Team (3)
│  ├─ Nike (Test Automation)
│  ├─ Nemesis (Security Testing)
│  └─ Tyche (Performance Testing)
│
└─ DevOps Team (2)
   ├─ Helios (Infrastructure)
   └─ Selene (Monitoring)
```

**Total**: 18 agents (~300GB RAM)

---

**Last Updated**: 2026-01-30
**Maintainer**: jeff@infiquetra.com
