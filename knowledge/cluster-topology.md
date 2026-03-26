# Olympus Cluster Topology

## Overview

6-node Proxmox VE 9.1.1 cluster (`olympus`) running on Dell servers. Ceph provides distributed storage. 8 agent VMs + 4 service VMs + 1 planned coordination VM.

## Hardware

| Host | IP | iDRAC | RAM | vCPU | Role |
|------|----|-------|-----|------|------|
| r420 | 10.220.1.7 | 10.220.1.17 | 70G | 24 | Cluster master, ceph-bulk (3x SAS) |
| r640-1 | 10.220.1.8 | 10.220.1.18 | 125G | 72 | ceph-fast (2x NVMe + 4x SAS) |
| r640-2 | 10.220.1.9 | 10.220.1.19 | 125G | 72 | ceph-fast (2x NVMe + 2x SAS) |
| r720xd | 10.220.1.10 | 10.220.1.20 | 94G | 24 | ceph-bulk (11x SAS) |
| r820 | 10.220.1.11 | 10.220.1.21 | 377G | 64 | ceph-bulk (3x RAID VDs), heavy VMs |
| r640-3 | 10.220.1.12 | 10.220.1.22 | 125G | 72 | ceph-fast (1x NVMe + 2x SAS) |

**iDRAC offset rule**: iDRAC IP = server IP + 10

**Credentials**: SSH root / see vault `vault_idrac_password`; iDRAC root / same

## Storage

| Pool | Backing | Use |
|------|---------|-----|
| ceph-fast | NVMe/SSD on R640s | VM disks (IOPS-sensitive workloads) |
| ceph-bulk | SAS HDDs on r420/r720xd/r820 | Backups, ISOs, cold storage |

Ceph network: dedicated 10GbE on 10.220.2.0/24 (vmbr1 per host)

## Agent VMs (10.220.1.50–.57)

| VMID | Name | Host | IP | Role |
|------|------|------|----|------|
| 100 | Zeus | r820 | 10.220.1.50 | Leadership / orchestration |
| 101 | Athena | r640-2 | 10.220.1.51 | Architecture / senior review |
| 102 | Apollo | r640-1 | 10.220.1.52 | Developer |
| 103 | Artemis | r420 | 10.220.1.53 | Developer |
| 104 | Hephaestus | r420 | 10.220.1.54 | Infrastructure / automation (pilot Hermes VM) |
| 105 | Perseus | r640-1 | 10.220.1.55 | Developer |
| 106 | Prometheus | r640-2 | 10.220.1.56 | Developer |
| 107 | Ares | r720xd | 10.220.1.57 | Developer |

## Service VMs (10.220.1.60–.64)

| VMID | Name | Host | IP | Purpose |
|------|------|------|----|---------|
| 200 | RustDesk | r820 | 10.220.1.60 | Remote desktop relay |
| 201 | Dell OME | r820 | 10.220.1.61 | Dell OpenManage Enterprise |
| 202 | PBS | r720xd | 10.220.1.62 | Proxmox Backup Server |
| 203 | Monitoring | r640-3 | 10.220.1.63 | Prometheus + Grafana |
| 204 | olympus-bus | r820 | 10.220.1.64 | Redis + Dolt + Discord bridge (planned) |

## Control Node (Mac Mini)

- **Host**: jeffs-mac-mini.infiquetra.com (10.220.1.2)
- **Role**: Conductor / orchestration node
- **Agents**: Hermes (conductor), Freya
- **Inventory group**: `control_nodes`

## Network

- **Management**: 10.220.1.0/24 (vmbr0, 1GbE)
- **Ceph**: 10.220.2.0/24 (vmbr1, 10GbE)
- **Gateway**: 10.220.1.1 (UniFi Dream Machine)
- **DNS suffix**: .infiquetra.com

## Ansible Access

```bash
cd /Users/jefcox/workspace/infiquetra/home-lab/ansible
ansible proxmox_hosts -i inventory/hosts.yml -m ping --vault-password-file ~/.vault_pass.txt
ansible agent_vms -i inventory/hosts.yml -m ping --vault-password-file ~/.vault_pass.txt
```
