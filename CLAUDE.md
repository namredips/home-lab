# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Home lab infrastructure repository using Ansible to automate a **Proxmox VE 9.1.1** cluster across 4 Dell servers. Proxmox hosts 8 Ubuntu 24.04 agent VMs that run the OpenClaw AI agent stack.

## Architecture

### Infrastructure Components
- **Hypervisor**: Proxmox VE 9.1.1 (Debian Trixie) on all 4 servers
- **Cluster name**: `olympus` (4-node Proxmox cluster via corosync/pvecm)
- **Master node**: r420.infiquetra.com (10.220.1.7)
- **Storage**: ZFS pools per host (`nvme-fast` for VM disks, `sas-data` for bulk)
- **VM template**: Ubuntu 24.04 cloud image, VM ID 9000, lives on r420
- **Agent VMs**: 8 VMs (IDs 100–107) distributed across hosts

### Hardware
| Host | IP | RAM | vCPU | NVMe pool | SAS pool |
|------|----|-----|------|-----------|----------|
| r420 | 10.220.1.7 | 70G | 24 | nvme-fast | sas-data (raidz1, 3x931G) |
| r8202 | 10.220.1.8 | 51G | 32 | nvme-fast | — |
| r720xd | 10.220.1.10 | 94G | 24 | nvme-fast | sas-data (raidz2 ×2, 11 drives) |
| r820 | 10.220.1.11 | 377G | 64 | nvme-fast | sas-data (raidz2, 8x931G) |

### VM Distribution
| VMID | Agent | Host | IP |
|------|-------|------|-----|
| 100 | Zeus | r820 | 10.220.1.50 |
| 101 | Athena | r820 | 10.220.1.51 |
| 102 | Apollo | r820 | 10.220.1.52 |
| 103 | Artemis | r420 | 10.220.1.53 |
| 104 | Hermes | r420 | 10.220.1.54 |
| 105 | Perseus | r720xd | 10.220.1.55 |
| 106 | Prometheus | r720xd | 10.220.1.56 |
| 107 | Ares | r8202 | 10.220.1.57 |

### Ansible Structure
- **Main playbook**: `ansible/proxmox_cluster.yml` — 5 phased roles
- **Teardown**: `ansible/proxmox_cluster_reset.yml`
- **Verification**: `ansible/proxmox_verify.yml`
- **Inventory groups**: `proxmox_hosts`, `proxmox_master`, `proxmox_nodes`, `agent_vms`
- **Variables**: Encrypted with Ansible Vault in `group_vars/all/all.yml`
- **Host vars**: Per-server ZFS pool definitions in `inventory/host_vars/`

### Role Pipeline
1. `proxmox_base` — disable enterprise repo, add no-sub repo, dist-upgrade, create `ansible@pam` API user/token
2. `proxmox_cluster` — `pvecm create olympus` on master, `pvecm add` on nodes (serial: 1)
3. `proxmox_storage` — create ZFS pools from host_vars, register with `pvesm`
4. `proxmox_template` — download Ubuntu 24.04 cloud image, build VM 9000, convert to template
5. `proxmox_vm` — clone template per agent, configure resources/cloud-init, start VMs

### Agent Stack Roles (target `agent_vms`, unchanged from pre-migration)
- `agent_provision` — dev environment, SSH keys, GitHub setup
- `agent_desktop` — Neovim, tmux, shell config
- `ollama` — local LLM inference
- `openclaw` — OpenClaw agent framework + systemd service

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

#### Single role via helper script (defaults: proxmox_cluster.yml, user=root)
```bash
./ansible/run_ansible_role.sh -r proxmox_base
./ansible/run_ansible_role.sh -r proxmox_storage
./ansible/run_ansible_role.sh -r proxmox_vm
```

#### Single-phase runs (using tags)
```bash
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --tags proxmox_storage --vault-password-file ~/.vault_pass.txt
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
pvesm status     # Storage pool status
qm list          # VMs on this host
zpool status     # ZFS pool health
```

## Development Notes

### Ansible Vault
- Sensitive vars in `ansible/inventory/group_vars/all/all.yml`
- Edit: `ansible-vault edit ansible/inventory/group_vars/all/all.yml --vault-password-file ~/.vault_pass.txt`

### Adding New Roles
- Structure: `tasks/main.yml`, `tasks/setup.yml`, `tasks/reset.yml`, `defaults/main.yml`
- Add to `proxmox_cluster.yml` in dependency order
- Add inverse step to `proxmox_cluster_reset.yml`

### ZFS Pool Definitions
- Defined per-host in `inventory/host_vars/<hostname>.yml`
- Each pool needs: `name`, `mode`, `devices[]`, `options`, `proxmox_storage_type`, `proxmox_content`
- Multi-vdev pools use `custom_create_cmd` (see r720xd host_vars)

### Proxmox API Token
- Created during `proxmox_base` run — secret printed in task output
- Manually add to vault as `proxmox_api_token_secret`
- User: `ansible@pam`, Token: `ansible-token`, Role: `PVEAdmin`
