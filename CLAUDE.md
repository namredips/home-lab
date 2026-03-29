# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Home lab infrastructure repository using Ansible to automate a **Proxmox VE 9.1.1** cluster across 6 Dell servers. Proxmox hosts 8 Ubuntu 24.04 agent VMs (the OpenClaw AI agent stack), 5 service VMs (RustDesk, Dell OME, PBS, Monitoring, Olympus-Bus), and 3 GitHub Actions runner VMs.

## Architecture

### Infrastructure Components
- **Hypervisor**: Proxmox VE 9.1.1 (Debian Trixie) on all 6 servers
- **Cluster name**: `olympus` (6-node Proxmox cluster via corosync/pvecm)
- **Master node**: r420.infiquetra.com (10.220.1.7)
- **Storage**: Ceph distributed storage — `ceph-fast` (NVMe/SSD on R640s) for VM disks, `ceph-bulk` (SAS HDDs) for backups/ISO
- **Ceph network**: Dedicated 10GbE on 10.220.2.0/24 (vmbr1 bridge per host)
- **VM template**: Ubuntu 24.04 cloud image, VM ID 9000, lives on r420
- **Agent VMs**: 8 VMs (IDs 100–107) distributed across hosts
- **Service VMs**: 5 VMs (IDs 200–204): RustDesk, Dell OME, PBS, Monitoring, Olympus-Bus

### Hardware
| Host | IP | Ceph IP | RAM | vCPU | Ceph Fast Disks | Ceph Bulk Disks |
|------|----|---------|-----|------|-----------------|-----------------|
| r420 | 10.220.1.7 | 10.220.2.7 | 70G | 24 | — | sdb-sdd (3x931G SAS) |
| r640-1 | 10.220.1.8 | 10.220.2.8 | 125G | 72 | nvme0n1+nvme1n1+sdc-sdf (6 disks) | — |
| r640-2 | 10.220.1.9 | 10.220.2.9 | 125G | 72 | nvme0n1+nvme1n1+sdc-sdd (4 disks) | — |
| r720xd | 10.220.1.10 | 10.220.2.10 | 94G | 24 | — | sdb-sdl (11x SAS) |
| r820 | 10.220.1.11 | 10.220.2.11 | 377G | 64 | — | sdb-sdd (3x RAID VDs) |
| r640-3 | 10.220.1.12 | 10.220.2.12 | 125G | 72 | nvme0n1+sdc-sdd (3 disks) | — |

### VM Distribution
| VMID | Name | Host | IP |
|------|------|------|-----|
| 100 | Zeus | r820 | 10.220.1.50 |
| 101 | Athena | r640-2 | 10.220.1.51 |
| 102 | Apollo | r640-1 | 10.220.1.52 |
| 103 | Artemis | r420 | 10.220.1.53 |
| 104 | Hephaestus | r420 | 10.220.1.54 |
| 105 | Perseus | r640-1 | 10.220.1.55 |
| 106 | Prometheus | r640-2 | 10.220.1.56 |
| 107 | Ares | r720xd | 10.220.1.57 |
| 200 | RustDesk | r820 | 10.220.1.60 |
| 201 | Dell OME | r820 | 10.220.1.61 |
| 202 | PBS | r720xd | 10.220.1.62 |
| 203 | Monitoring | r640-3 | 10.220.1.63 |
| 204 | Olympus-Bus | r820 | 10.220.1.64 |
| 205 | Runner-1 | r640-3 | 10.220.1.65 |
| 206 | Runner-2 | r820 | 10.220.1.66 |
| 207 | Runner-3 | r720xd | 10.220.1.67 |

### Ansible Structure
- **Main playbook**: `ansible/proxmox_cluster.yml` — 7 phased roles
- **Service VMs**: `ansible/service_vms.yml`
- **Teardown**: `ansible/proxmox_cluster_reset.yml`
- **Verification**: `ansible/proxmox_verify.yml`
- **Inventory groups**: `proxmox_hosts`, `proxmox_master`, `proxmox_nodes`, `agent_vms`, `control_nodes`
- **Variables**: Encrypted with Ansible Vault in `group_vars/all/all.yml`
- **Host vars**: Per-server Ceph disk and NIC definitions in `inventory/host_vars/`

### Role Pipeline
1. `proxmox_network` — bring up 10GbE Ceph NICs, create vmbr1 bridge, assign 10.220.2.x IPs
2. `proxmox_disk_prep` — wipe non-boot disks (ZFS labels, GPT tables) for Ceph OSD creation
3. `proxmox_base` — disable enterprise repo, add no-sub repo, dist-upgrade, create `ansible@pam` API user/token
4. `proxmox_cluster` — `pvecm create olympus` on master, `pvecm add` on 5 nodes (serial: 1)
5. `proxmox_ceph` — install Ceph Squid, init cluster, create mons/mgrs/OSDs, CRUSH rules, pools
6. `proxmox_template` — download Ubuntu 24.04 cloud image, build VM 9000, convert to template
7. `proxmox_vm` — clone template per agent/service VM, configure resources/cloud-init, start VMs

### Agent Stack Roles (target `agent_vms`)
- `agent_provision` — dev environment, SSH keys, GitHub setup
- `agent_desktop` — Neovim, tmux, shell config
- `ollama` — local LLM inference
- `hermes` — Hermes Agent framework + systemd service (replaced OpenClaw)

### Control Node (mac mini)
- **Host**: jeffs-mac-mini.infiquetra.com (10.220.1.2)
- **Role**: Conductor/orchestration node — runs Hermes natively, manages Ansible deployments
- **Group**: `control_nodes` in inventory
- **Agent playbook**: `ansible/hermes_cluster.yml` — deploys Hermes to all `agent_vms`

### Secret Strategy
| Identity | Vault Key | Notes |
|----------|-----------|-------|
| Mac mini conductor | `vault_hermes_conductor_token` | From `$HERMES_BOT_TOKEN` env var |
| Zeus (VM 100) | `vault_discord_bot_token_zeus` | Existing |
| Athena (VM 101) | `vault_discord_bot_token_athena` | Existing |
| Apollo (VM 102) | `vault_discord_bot_token_apollo` | Existing |
| Artemis (VM 103) | `vault_discord_bot_token_artemis` | Existing |
| Hephaestus (VM 104) | `vault_discord_bot_token_hephaestus` | Renamed from `_hermes` |
| Perseus (VM 105) | `vault_discord_bot_token_perseus` | Existing |
| Prometheus (VM 106) | `vault_discord_bot_token_prometheus` | Existing |
| Ares (VM 107) | `vault_discord_bot_token_ares` | Existing |

## Common Commands

### Prerequisites
```bash
cd ansible
uv sync
ansible-galaxy collection install -r requirements.yml
# Vault password must be in ~/.vault_pass.txt
```

### Proxmox Cluster Management

#### Full deployment
```bash
cd ansible
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```

#### Single-phase runs (using tags)
```bash
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --tags proxmox_network --vault-password-file ~/.vault_pass.txt
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --tags proxmox_ceph --vault-password-file ~/.vault_pass.txt
```

#### Teardown
```bash
ansible-playbook -i inventory/hosts.yml proxmox_cluster_reset.yml \
  -e reset=true --vault-password-file ~/.vault_pass.txt
```

#### Verify cluster health
```bash
ansible-playbook -i inventory/hosts.yml proxmox_verify.yml \
  --vault-password-file ~/.vault_pass.txt
```

### Service VM Management
```bash
# Deploy all service VMs
ansible-playbook -i inventory/hosts.yml service_vms.yml \
  --vault-password-file ~/.vault_pass.txt

# Single service
ansible-playbook -i inventory/hosts.yml service_vms.yml \
  --tags monitoring --vault-password-file ~/.vault_pass.txt
```

### Agent VM Management
```bash
# Deploy agent stack on all VMs
ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt

# Check VM SSH connectivity
ansible agent_vms -i inventory/hosts.yml -m ping
```

### Proxmox CLI (run on any PVE host as root)
```bash
pvecm status     # Cluster quorum status
pvecm nodes      # List cluster nodes
pvesm status     # Storage pool status (shows ceph-fast, ceph-bulk)
ceph status      # Ceph health
ceph osd tree    # OSD layout with device classes
qm list          # VMs on this host
```

## Development Notes

### Ansible Vault
- Sensitive vars in `ansible/inventory/group_vars/all/all.yml`
- Edit: `ansible-vault edit ansible/inventory/group_vars/all/all.yml --vault-password-file ~/.vault_pass.txt`

### Adding New Roles
- Structure: `tasks/main.yml`, `tasks/setup.yml`, `tasks/reset.yml`, `defaults/main.yml`
- Add to `proxmox_cluster.yml` in dependency order
- Add inverse step to `proxmox_cluster_reset.yml`

### Ceph Disk Definitions
- Defined per-host in `inventory/host_vars/<hostname>.yml`
- Each disk needs: `name` (e.g. `nvme0n1`), `device_class` (`ssd` or `hdd`)
- `ceph_nic` defines the 10GbE interface for vmbr1 (e.g. `nic0`, `nic4`)

### Proxmox API Token
- Created during `proxmox_base` run — secret printed in task output
- Manually add to vault as `proxmox_api_token_secret`
- User: `ansible@pam`, Token: `ansible-token`, Role: `PVEAdmin`
