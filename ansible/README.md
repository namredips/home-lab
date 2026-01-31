# OpenClaw Virtual Employee Infrastructure

**"Mount Olympus" Agent Cluster**

AI-powered virtual employees for software development using OpenClaw, deployed across 5 Dell servers.

## Overview

This infrastructure deploys 8 OpenClaw AI agents that function as virtual software development team members. All agents are full-stack generalists who can wear different "hats" (security, QA, DevOps, etc.) depending on the review context.

### Team Composition

| Agent | Role | Trait | IP | Email |
|-------|------|-------|-----|-------|
| **Athena** | PM, Orchestration | Wisdom & strategy | 10.220.1.50 | athena@infiquetra.com |
| **Apollo** | Development | Light, truth, reason | 10.220.1.51 | apollo@infiquetra.com |
| **Artemis** | Development | Precision, focus | 10.220.1.52 | artemis@infiquetra.com |
| **Hermes** | Development | Speed, communication | 10.220.1.53 | hermes@infiquetra.com |
| **Perseus** | Development | Heroic problem-solver | 10.220.1.54 | perseus@infiquetra.com |
| **Prometheus** | Development | Innovation, foresight | 10.220.1.55 | prometheus@infiquetra.com |
| **Ares** | Development | Strength, determination | 10.220.1.56 | ares@infiquetra.com |
| **Poseidon** | Development | Depth, persistence | 10.220.1.57 | poseidon@infiquetra.com |

## Architecture

### Physical Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mount Olympus Cluster                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  r420 (10.220.1.7)      → Athena (Orchestrator)                 │
│  r710 (10.220.1.9)      → Apollo, Artemis                       │
│  r8202 (10.220.1.8)     → Hermes                                │
│  r720xd (10.220.1.10)   → Perseus + Mattermost                  │
│  r820 (10.220.1.11)     → Prometheus, Ares, Poseidon            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Infrastructure**:
- KVM/libvirt hypervisors
- Ubuntu 22.04 VMs (8 agents)
- Mattermost (self-hosted team communication)

**Development Environment** (per agent):
- Python 3.12, Node.js 22, Dart/Flutter, Rust, Go, C/C++
- Docker, AWS CLI, AWS CDK
- Neovim (custom config), tmux, Starship prompt
- Claude Code CLI, Codex CLI, Gemini CLI

**AI Orchestration**:
- OpenClaw (autonomous agent framework)
- Anthropic Claude (primary LLM)
- OpenAI GPT/Codex (secondary)
- Google Gemini (tertiary)

**Collaboration Tools**:
- GitHub (code, issues, PRs)
- Mattermost (team communication)
- Git (shared repositories)

## Quick Start

### Prerequisites

```bash
# Install Ansible
pip install ansible

# Navigate to ansible directory
cd ~/workspace/temp/home-lab/ansible

# Test connectivity
ansible all -i inventory/hosts.yml -m ping
```

### Deploy Infrastructure

```bash
# Create vault password file
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass

# Create and edit vault for secrets
ansible-vault create passwd.yml --vault-password-file .vault_pass

# Deploy entire infrastructure
ansible-playbook openclaw_cluster.yml --vault-password-file .vault_pass

# Estimated time: 90-120 minutes
```

### Teardown Infrastructure

```bash
# Remove all VMs and services
ansible-playbook openclaw_cluster_reset.yml --vault-password-file .vault_pass

# Optional: Also remove libvirt
ansible-playbook openclaw_cluster_reset.yml \
  -e remove_libvirt=true \
  --vault-password-file .vault_pass
```

## Ansible Roles

| Role | Purpose | Files Created |
|------|---------|---------------|
| **host_prepare** | OS updates, disk provisioning | - |
| **libvirt** | KVM/libvirt hypervisor setup | Networks, storage pools |
| **mattermost** | Team communication platform | Docker containers, database |
| **agent_vm** | VM provisioning | 8 Ubuntu VMs with cloud-init |
| **agent_provision** | Development environment | Languages, tools, configs |
| **openclaw** | OpenClaw agent installation | Service, config, API keys |

## Deployment Phases

1. **Host Preparation** (15-30 min)
   - Update all servers
   - Provision storage for VMs

2. **Infrastructure Setup** (10-15 min)
   - Install libvirt/KVM on hypervisors
   - Deploy Mattermost on r720xd

3. **VM Provisioning** (20-30 min)
   - Create 8 Ubuntu 22.04 VMs
   - Distribute across hypervisors

4. **Agent Environment** (45-60 min)
   - Install development tools
   - Configure neovim, shell, AI CLIs

5. **OpenClaw Setup** (10-15 min)
   - Install OpenClaw
   - Configure systemd services

6. **Manual Configuration** (30-60 min)
   - Authenticate AI tools
   - Create Mattermost accounts
   - Setup GitHub accounts

**Total deployment time**: 2.5-3.5 hours

## Post-Deployment

### Manual Steps Required

1. **Google Workspace**: Configure catch-all email routing
   - See: `docs/GOOGLE_WORKSPACE_SETUP.md`

2. **Mattermost**: Create agent accounts
   - http://10.220.1.10:8065
   - Create account for each agent
   - Generate bot tokens

3. **GitHub**: Create agent accounts
   - Setup SSH keys on each VM
   - Create organization: `infiquetra-agents`

4. **AI Tools**: Authenticate on each VM
   ```bash
   ssh agent@<agent-ip>
   claude-code auth
   # Edit ~/.openclaw/.env for OpenAI/Google keys
   ```

5. **Start Services**: Enable OpenClaw agents
   ```bash
   ansible agent_vms -i inventory/hosts.yml \
     -m systemd \
     -a "name=openclaw-{{ inventory_hostname_short }} state=started" \
     -u agent --become
   ```

### Verification

```bash
# Check all VMs are accessible
ansible agent_vms -i inventory/hosts.yml -m ping -u agent

# Check OpenClaw services
ansible agent_vms -i inventory/hosts.yml \
  -a "systemctl status openclaw-{{ inventory_hostname_short }}" \
  -u agent --become

# Access Mattermost
curl http://10.220.1.10:8065/api/v4/system/ping

# View agent dashboards
open http://10.220.1.50:18789  # Athena
open http://10.220.1.51:18789  # Apollo
# (etc for all agents)
```

## Workflow

```
Human + Athena ──(Mattermost)──► GitHub Issues
                                       │
                                       ▼
              Dev Agents ◄──(assigned)── Issue Queue
                    │
                    ▼
              Shared Git Repos (PRs)
                    │
                    ▼
              Human Approval ──► Deploy to AWS
```

**Key principles**:
- Agents are full-stack generalists
- Reviews use situational "hats" (security, QA, performance, etc.)
- Human collaborates with Athena to define work
- Developers work autonomously or via assignment
- Deployment requires human approval gates

## Documentation

- **[Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)**: Step-by-step deployment guide
- **[Google Workspace Setup](docs/GOOGLE_WORKSPACE_SETUP.md)**: Email configuration
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Architecture Overview](docs/ARCHITECTURE.md)**: System design and decisions

## Project Structure

```
ansible/
├── roles/
│   ├── host_prepare/       # Host OS preparation
│   ├── libvirt/            # KVM/libvirt setup
│   ├── mattermost/         # Team communication
│   ├── agent_vm/           # VM provisioning
│   ├── agent_provision/    # Development environment
│   └── openclaw/           # OpenClaw installation
├── inventory/
│   └── hosts.yml           # Server and VM inventory
├── openclaw_cluster.yml    # Main deployment playbook
├── openclaw_cluster_reset.yml  # Teardown playbook
└── passwd.yml              # Encrypted secrets (vault)
```

## Resource Allocation

| Server | CPU | RAM | Disk | VMs | RAM Used |
|--------|-----|-----|------|-----|----------|
| r420 | Lower | ~32GB | 836GB | 1 | 8GB |
| r710 | Medium | ~64GB | 852GB | 2 | 32GB |
| r8202 | Medium | ~64GB | 851GB | 1 | 16GB |
| r720xd | Medium | ~128GB | 852GB | 1 + Services | 16GB |
| r820 | High | ~128GB | 851GB | 3 | 48GB |

**Total**: 8 VMs, 120GB RAM allocated, 2TB disk

## Cost Analysis

**Hardware**: Existing (no additional cost)

**Software**:
- Mattermost: Free (self-hosted)
- GitHub: Free (public repos) or existing subscription
- LLM APIs:
  - Anthropic Claude: Existing subscription (jefcox)
  - OpenAI GPT: Existing subscription (jefcox)
  - Google Gemini: Existing subscription (jefcox)
- Google Workspace: $0 (catch-all routing, no additional users)

**Total monthly cost**: $0 (using existing subscriptions)

**Savings vs. alternatives**:
- 8 human developers @ $100k/year = $800k/year
- 8 Google Workspace users = $576/year
- Cloud VMs (8× 16GB) = ~$1,200/month

## Future Enhancements

1. **Local LLM inference**: Add Ollama on dedicated hardware
2. **Expanded team**: Add more specialized agents (QA, DevOps, etc.)
3. **Monitoring**: Prometheus/Grafana for agent metrics
4. **CI/CD integration**: GitHub Actions with approval gates
5. **Email automation**: IMAP/SMTP for programmatic email access

## Security Considerations

- All agent emails route to jeff@infiquetra.com (catch-all)
- API keys stored in Ansible vault (encrypted)
- SSH key authentication for VM access
- Deployment gates require human approval
- Sensitive data isolated per agent VM

## Troubleshooting

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for common issues.

Quick checks:
```bash
# VM not starting
ssh jefcox@<hypervisor> "virsh list --all"

# SSH access fails
ping <agent-ip>

# Mattermost down
curl http://10.220.1.10:8065/api/v4/system/ping

# OpenClaw service fails
ssh agent@<agent-ip> "systemctl status openclaw-<agent>"
```

## License

Internal use only - Infiquetra infrastructure.

## Maintainer

**Jeff Cox** (jeff@infiquetra.com)

---

**Last Updated**: 2026-01-30
