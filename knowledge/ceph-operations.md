# Ceph Operations Runbook

## Cluster Health

```bash
# Run on any PVE host as root
ceph status                    # Overall health (HEALTH_OK / HEALTH_WARN / HEALTH_ERR)
ceph osd tree                  # OSD layout with device classes (ssd, hdd)
ceph df                        # Pool usage
ceph osd df                    # Per-OSD usage
ceph pg stat                   # Placement group status
```

## Storage Pools

| Pool | Device Class | Use |
|------|-------------|-----|
| ceph-fast | ssd (NVMe) | VM disks on R640s |
| ceph-bulk | hdd (SAS) | Backups, ISOs on r420/r720xd/r820 |

CRUSH rules ensure `ceph-fast` only uses SSD OSDs and `ceph-bulk` only uses HDD OSDs.

## OSD Management

```bash
# Check OSD status
ceph osd status

# Mark OSD out (before removal)
ceph osd out osd.<id>

# Remove OSD
ceph osd down osd.<id>
ceph osd rm osd.<id>
ceph osd crush rm osd.<id>
ceph auth del osd.<id>

# Add OSD via Proxmox (preferred — handles crush map)
pveceph createosd /dev/<disk> --crush-device-class ssd
```

## Monitoring Capacity

```bash
# Check replication factor (should be 3 for redundancy)
ceph osd pool get ceph-fast size
ceph osd pool get ceph-bulk size

# Raw vs usable space
ceph df detail
```

## Performance

```bash
# Real-time IOPS / throughput
ceph -w

# OSD performance stats
ceph osd perf
```

## Common Issues

### HEALTH_WARN: clock skew

```bash
# Check NTP sync on all hosts
ansible proxmox_hosts -i inventory/hosts.yml -m shell -a "chronyc tracking" \
  --vault-password-file ~/.vault_pass.txt
```

### HEALTH_WARN: too few PGs

Indicates a pool has fewer placement groups than recommended.
```bash
ceph osd pool set ceph-fast pg_num 128
ceph osd pool set ceph-fast pgp_num 128
```

### OSD Down

```bash
# Identify which host has the down OSD
ceph osd tree | grep down

# SSH to that host and check disk
lsblk
journalctl -u ceph-osd@<id>
```

## Ceph Network

Dedicated 10GbE on 10.220.2.0/24 (vmbr1 bridge per host).
All inter-OSD and OSD-to-monitor traffic uses this network.
Management traffic (Proxmox API, SSH) uses 10.220.1.0/24.
