# home-lab

Ansible automation for a 6-node Proxmox VE 9.1.1 cluster running the OpenClaw AI agent stack.

## Hardware

| Host | IP | RAM | vCPU | Role |
|------|----|-----|------|------|
| r420 | 10.220.1.7 | 70G | 24 | Cluster master, Ceph HDD (3x 931G SAS) |
| r640-1 | 10.220.1.8 | 125G | 72 | Ceph SSD (2x NVMe + 4x SATA SSD) |
| r640-2 | 10.220.1.9 | 125G | 72 | Ceph SSD (2x NVMe + 2x SATA SSD) |
| r720xd | 10.220.1.10 | 94G | 24 | Ceph HDD (11x SAS) |
| r820 | 10.220.1.11 | 377G | 64 | Ceph HDD (3x RAID VDs) |
| r640-3 | 10.220.1.12 | 125G | 72 | Ceph SSD (1x NVMe + 2x SATA SSD) |

## Storage

Ceph distributed storage (Squid 19.x), replication size 2:
- **ceph-fast** — NVMe + SATA SSD OSDs on R640s → VM disks
- **ceph-bulk** — SAS HDD OSDs on r420/r720xd/r820 → backups, ISOs

Dedicated Ceph cluster network: `10.220.2.0/24` (10GbE via vmbr1)

## VMs

| VMID | Name | Host | IP | Purpose |
|------|------|------|----|---------|
| 100 | Zeus | r820 | 10.220.1.50 | OpenClaw PM / orchestration |
| 101 | Athena | r640-2 | 10.220.1.51 | OpenClaw architecture |
| 102 | Apollo | r640-1 | 10.220.1.52 | OpenClaw code quality |
| 103 | Artemis | r420 | 10.220.1.53 | OpenClaw testing |
| 104 | Hermes | r420 | 10.220.1.54 | OpenClaw integrations |
| 105 | Perseus | r640-1 | 10.220.1.55 | OpenClaw complex problems |
| 106 | Prometheus | r640-2 | 10.220.1.56 | OpenClaw innovation |
| 107 | Ares | r720xd | 10.220.1.57 | OpenClaw performance |
| 200 | RustDesk | r820 | 10.220.1.60 | Remote desktop relay |
| 201 | Dell OME | r820 | 10.220.1.61 | iDRAC/server management |
| 202 | PBS | r720xd | 10.220.1.62 | VM backups (ceph-bulk) |
| 203 | Monitoring | r640-3 | 10.220.1.63 | Prometheus + Grafana |

## Quick Start

```bash
cd ansible
uv sync
ansible-galaxy collection install -r requirements.yml
# Vault password must be in ~/.vault_pass.txt

# Full cluster deployment (phases run sequentially via tags)
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --vault-password-file ~/.vault_pass.txt

# Service VMs (RustDesk, PBS, Monitoring)
ansible-playbook -i inventory/hosts.yml service_vms.yml \
  --vault-password-file ~/.vault_pass.txt
```

See `CLAUDE.md` for detailed commands and development notes.
