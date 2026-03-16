# Plan: Proxmox Cluster, Ceph, and Storage Setup
Date: 2026-03-15

## Overview
6 standalone Proxmox VE nodes → cluster with Ceph tiered storage.
Replaces old ZFS-per-node model. All VMs migrate to Ceph RBD.

## Phases
- [x] Phase 0: proxmox_network role — 10GbE Ceph network (vmbr1 on 10.220.2.0/24)
- [x] Phase 1: proxmox_disk_prep role — wipe non-boot disks for Ceph OSD
- [ ] Phase 2: proxmox_cluster — existing role, 6-node formation
- [x] Phase 3: proxmox_ceph role — Ceph reef, monitors, OSDs, CRUSH rules, pools
- [x] Phase 4: host_vars + stale reference cleanup (r8202/r710 removal)
- [x] Phase 5: proxmox_vm defaults update — ceph-fast storage, rebalanced host distribution
- [ ] Phase 6: Additional service VMs (OME 201, PBS 202, Monitoring 203)

## Key Decisions
- Ceph size=2 (survive 1 node failure)
- Dedicated 10GbE Ceph network: 10.220.2.0/24
- Fast pool (ssd_rule): NVMe + SATA SSD from R640s (~6.7TB usable)
- Bulk pool (hdd_rule): SAS from r420 + r720xd + r820 (~15.5TB usable)
- Monitors on r420, r640-1, r720xd (odd quorum)
- r820 gets sdb/sdc/sdd as bulk OSDs (existing RAID virtual disks, no reconfiguration)

## Files Created/Modified
- NEW: ansible/roles/proxmox_network/{defaults,tasks,templates}
- NEW: ansible/roles/proxmox_disk_prep/{defaults,tasks}
- NEW: ansible/roles/proxmox_ceph/{defaults,tasks}
- EDIT: ansible/proxmox_cluster.yml (new phases, remove proxmox_storage)
- EDIT: ansible/inventory/host_vars/*.yml (replace zfs_pools with ceph_nic/ceph_disks)
- EDIT: ansible/roles/proxmox_vm/defaults/main.yml (ceph-fast storage, new host layout)
- EDIT: ansible/roles/proxmox_template/defaults/main.yml (ceph-fast storage)
- FIX: stale r8202/r710 references in proxmox_vm_fix_network.yml, set_spice.yml, verify.yml, agent_vm, vm_backup, openEBS
