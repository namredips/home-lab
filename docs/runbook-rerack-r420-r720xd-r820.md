# Runbook: Safe Re-Rack of R420, R720xd, R820

**Date written**: 2026-03-16
**Cluster**: olympus (6 nodes)
**Scope**: Physical re-rack of three servers with HDD Ceph OSDs. Zero data loss, minimal VM downtime.

---

## Quick Reference

| Host | IP | iDRAC IP | VMs | Ceph Mon? | HDD OSDs |
|------|----|----------|-----|-----------|----------|
| r820 | 10.220.1.11 | 10.220.1.21 | Zeus (100), RustDesk (200), OME (201) | No | 3 |
| r420 | 10.220.1.7 | 10.220.1.17 | Artemis (103), Hermes (104) | Yes | 3 |
| r720xd | 10.220.1.10 | 10.220.1.20 | Ares (107), PBS (202) | Yes | 11 |

**Re-rack order: R820 → R420 → R720xd**

Reason: R820 has no Ceph monitor so it's the safest to start. R720xd hosts PBS (backup server) and the most OSDs — keep it up as long as possible.

---

## Prerequisites (do once before starting)

### 1. Verify cluster is healthy

```bash
ssh root@10.220.1.8  # Connect to r640-1 (safe host, not being re-racked)
pvecm status         # Should show 6/6 nodes, quorum OK
ceph -s              # Should show HEALTH_OK, all OSDs up
```

Expected output:
```
ceph -s
  cluster:
    id:     <uuid>
    health: HEALTH_OK
  services:
    mon: 3 daemons, quorum r420,r640-1,r720xd
    osd: 17 osds: 17 up, 17 in
```

### 2. Lower min_size to 1 on both pools

This prevents I/O blackouts when a host goes offline. Without this, Ceph halts all reads/writes to affected PGs until re-replication completes (potentially hours).

```bash
# On any PVE host:
ceph osd pool set ceph-fast min_size 1
ceph osd pool set ceph-bulk min_size 1

# Verify:
ceph osd pool get ceph-fast min_size   # Should return: min_size: 1
ceph osd pool get ceph-bulk min_size   # Should return: min_size: 1

ceph -s  # Should still show HEALTH_OK
```

### 3. Trigger a fresh PBS backup

PBS is on r720xd (last to go down). This captures a clean snapshot before any work begins.

```bash
# On any PVE host — backs up all VMs except PBS itself (202):
vzdump --all --exclude 202 --storage pbs-backup --mode snapshot --compress zstd

# Monitor progress in Proxmox web UI or:
journalctl -f -u vzdump
```

Wait for completion before proceeding.

---

## Host 1: R820 (10.220.1.11)

### Step 1: Migrate VMs off R820

```bash
ssh root@10.220.1.8  # Connect to r640-1

# Migrate Zeus (100) to r640-1
qm migrate 100 r640-1 --online

# Migrate RustDesk (200) to r640-2
qm migrate 200 r640-2 --online

# Migrate Dell OME (201) to r640-2 — Windows VM, may take a few minutes
qm migrate 201 r640-2 --online
```

Verify all three are running on their new hosts:
```bash
ssh root@10.220.1.8 "qm list"   # Should show Zeus (100)
ssh root@10.220.1.9 "qm list"   # Should show RustDesk (200) and OME (201)
```

### Step 2: Set Ceph noout

```bash
ceph osd set noout
# Prevents Ceph from marking OSDs as permanently out during the short downtime.
# Without this, Ceph starts rebalancing data away from R820's OSDs immediately.
ceph -s  # Should show: 1 flag(s) set: noout
```

### Step 3: Shut down R820

```bash
ssh root@10.220.1.11 "shutdown -h now"
```

Verify it's off via iDRAC:
```bash
ipmitool -I lanplus -H 10.220.1.21 -U root -P 'ub=19711' power status
# Should return: Chassis Power is off
```

### Step 4: Verify remaining cluster is healthy

```bash
pvecm status   # Should show 5/6 nodes (R820 absent), quorum OK — 6-node clusters maintain quorum with 4+ nodes
ceph -s        # All 3 HDD OSDs from R820 will show "down" — that's expected with noout set
```

### Step 5: Re-rack R820

Physical work: install new rails, slide server in, reconnect all cables (power, IPMI, network).

### Step 6: Power on R820 and wait for rejoin

```bash
ipmitool -I lanplus -H 10.220.1.21 -U root -P 'ub=19711' power on

# Wait for SSH (2-5 minutes):
until ssh root@10.220.1.11 'echo up' 2>/dev/null; do echo "waiting..."; sleep 10; done

# Verify cluster membership:
ssh root@10.220.1.11 "pvecm status"
pvecm nodes  # Should show r820 back
```

### Step 7: Unset noout and verify Ceph recovery

```bash
ceph osd unset noout

# Watch recovery:
watch -n 5 'ceph -s'
# You'll see "recovery" or "degraded" briefly, then it should clear.

# Wait for HEALTH_OK before proceeding to next host.
# With min_size=1, VMs continue running during recovery — no I/O pause.
ceph health   # Wait until this returns: HEALTH_OK
ceph osd tree # Verify R820's 3 HDD OSDs are all "up in"
```

### Step 8: Optional — migrate VMs back to R820

```bash
qm migrate 100 r820 --online   # Zeus back to r820
qm migrate 200 r820 --online   # RustDesk back to r820
qm migrate 201 r820 --online   # OME back to r820
```

### Checkpoint: Before proceeding to R420

- [ ] `ceph health` = HEALTH_OK
- [ ] `pvecm nodes` shows 6/6
- [ ] All R820 OSDs are "up in" in `ceph osd tree`
- [ ] All VMs running (wherever they ended up)

---

## Host 2: R420 (10.220.1.7)

> **Note**: R420 is the Proxmox cluster "master" but this is not special — any node can serve API calls. Proxmox clusters are peer-to-peer. R420 also hosts a Ceph monitor. With R420 offline, quorum is held by r640-1 + r720xd (2/3 — still quorate).

### Step 1: Migrate VMs off R420

```bash
# Artemis (103) to r640-1
qm migrate 103 r640-1 --online

# Hermes (104) to r640-3
qm migrate 104 r640-3 --online
```

Verify:
```bash
ssh root@10.220.1.8 "qm list"   # Should show Artemis (103)
ssh root@10.220.1.12 "qm list"  # Should show Hermes (104)
```

### Step 2: Set noout

```bash
ceph osd set noout
ceph -s  # Confirm flag is set
```

### Step 3: Shut down R420

```bash
ssh root@10.220.1.7 "shutdown -h now"

# Verify off:
ipmitool -I lanplus -H 10.220.1.17 -U root -P 'ub=19711' power status
```

### Step 4: Verify remaining cluster

```bash
pvecm status   # 5/6 nodes, quorum OK (r640-1 + r720xd maintain mon quorum)
ceph -s        # R420's 3 HDD OSDs down — expected with noout
```

### Step 5: Re-rack R420

Physical work.

### Step 6: Power on R420 and wait for rejoin

```bash
ipmitool -I lanplus -H 10.220.1.17 -U root -P 'ub=19711' power on

until ssh root@10.220.1.7 'echo up' 2>/dev/null; do echo "waiting..."; sleep 10; done

pvecm status
pvecm nodes  # r420 should be back
```

### Step 7: Unset noout and verify Ceph recovery

```bash
ceph osd unset noout
watch -n 5 'ceph -s'
ceph health   # Wait for HEALTH_OK
ceph osd tree # All R420 OSDs back up
```

### Step 8: Optional — migrate VMs back to R420

```bash
qm migrate 103 r420 --online   # Artemis back
qm migrate 104 r420 --online   # Hermes back
```

### Checkpoint: Before proceeding to R720xd

- [ ] `ceph health` = HEALTH_OK
- [ ] `pvecm nodes` shows 6/6
- [ ] All R420 OSDs are "up in"
- [ ] All VMs running

---

## Host 3: R720xd (10.220.1.10)

> **Note**: R720xd has 11 HDD OSDs — the most of any host. Recovery after it comes back online will take longer. The `noout` flag prevents unnecessary rebalancing during the downtime.

> **PBS note**: VM 202 (PBS) lives on r720xd. Its disk is on ceph-bulk, accessible from any Proxmox host. Migrate it to r640-1 before shutdown.

### Step 1: Trigger one more PBS backup (optional but recommended)

```bash
vzdump --all --exclude 202 --storage pbs-backup --mode snapshot --compress zstd
```

Wait for completion.

### Step 2: Migrate VMs off R720xd

```bash
# Ares (107) to r640-3
qm migrate 107 r640-3 --online

# PBS (202) to r640-1
qm migrate 202 r640-1 --online
```

Verify:
```bash
ssh root@10.220.1.12 "qm list"  # Should show Ares (107)
ssh root@10.220.1.8 "qm list"   # Should show PBS (202)
```

### Step 3: Set noout

```bash
ceph osd set noout
ceph -s
```

### Step 4: Shut down R720xd

```bash
ssh root@10.220.1.10 "shutdown -h now"

# Verify off:
ipmitool -I lanplus -H 10.220.1.20 -U root -P 'ub=19711' power status
```

### Step 5: Verify remaining cluster

```bash
pvecm status   # 5/6 nodes; quorum held by r420 + r640-1 (2/3 mons)
ceph -s        # 11 HDD OSDs from r720xd down — expected
```

### Step 6: Re-rack R720xd

Physical work.

### Step 7: Power on R720xd and wait for rejoin

```bash
ipmitool -I lanplus -H 10.220.1.20 -U root -P 'ub=19711' power on

until ssh root@10.220.1.10 'echo up' 2>/dev/null; do echo "waiting..."; sleep 10; done

pvecm status
pvecm nodes
```

### Step 8: Unset noout and verify Ceph recovery

```bash
ceph osd unset noout
watch -n 5 'ceph -s'
# R720xd has 11 OSDs — recovery may show "recovering" for a few minutes
ceph health       # Wait for HEALTH_OK
ceph osd tree     # All 11 r720xd OSDs back up
```

### Step 9: Migrate VMs back to R720xd

```bash
qm migrate 107 r720xd --online   # Ares back
qm migrate 202 r720xd --online   # PBS back
```

---

## Final Verification

Run these on any PVE host after all three are done:

```bash
# Full cluster membership
pvecm status
pvecm nodes   # Should show all 6 nodes

# Ceph health
ceph -s       # HEALTH_OK, all 17 OSDs up (3+3+3+11 = wait, actual count varies — verify with ceph osd tree)
ceph osd tree # All OSDs up, correct hosts

# All VMs running
qm list       # On each node, or check Proxmox web UI cluster summary

# Verify pools still have correct min_size
ceph osd pool get ceph-fast min_size   # min_size: 1
ceph osd pool get ceph-bulk min_size   # min_size: 1
```

### Final PBS backup

```bash
vzdump --all --exclude 202 --storage pbs-backup --mode snapshot --compress zstd
```

### Verify monitoring is collecting all hosts

```bash
curl -s 'http://10.220.1.63:9090/api/v1/query?query=instance:ipmi_inlet_temp_celsius' \
  | python3 -c "import sys,json; [print(r['metric']['instance'], r['value'][1]) for r in json.load(sys.stdin)['data']['result']]"
# Should show 6 entries (one per host)
```

---

## Troubleshooting

### Ceph stuck in degraded after host returns

```bash
ceph health detail   # Shows which PGs are degraded and why
ceph osd tree        # Check if OSDs came back "up in" — if they show "down", check the host's ceph-osd@ services
ssh root@<host> "systemctl status ceph-osd@*"
ssh root@<host> "systemctl start ceph-osd.target"
```

### Ceph shows HEALTH_WARN: noout flag set

You forgot to unset it:
```bash
ceph osd unset noout
```

### VM migration fails

```bash
# Check VM status:
qm status <VMID>

# Try stopping and starting instead of live migration:
qm shutdown <VMID>
qm migrate <VMID> <target_host>
qm start <VMID>
```

### Host doesn't rejoin cluster after reboot

```bash
ssh root@<host>
systemctl status pve-cluster   # Should be active
journalctl -u pve-cluster -n 50 # Look for corosync errors
pvecm status                    # Might show split-brain if network wasn't reconnected properly
```

If network issue: verify cables, check `ip addr show` for correct IPs, check `brctl show` for bridge state.

### iDRAC unreachable

If iDRAC doesn't respond after power change:
```bash
# Wait 5 minutes — cold resets take time
# Then try:
ping 10.220.1.2X
# If still no response, physical console access needed
```

---

## Summary

| Phase | Action | Risk |
|-------|--------|------|
| Pre-work | Set min_size=1, take PBS backup | None |
| Each host | Migrate VMs, set noout, shutdown | VMs temporarily on non-native host |
| Each host | Re-rack, power on, unset noout | None |
| Each host | Wait for HEALTH_OK | Short degraded period (min_size=1 means I/O continues) |
| Post-work | Final backup, verify monitoring | None |

Total downtime per VM: ~5 minutes (live migration) × 2 (away + back) = ~10 min per VM.
