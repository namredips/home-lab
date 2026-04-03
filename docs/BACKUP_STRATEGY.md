# Hermes Agent Backup Strategy

## Overview

The backup system provides comprehensive protection for the Hermes agent infrastructure through Proxmox Backup Server (PBS) snapshots, Hermes memory exports, and off-hypervisor redundancy. PBS runs on VM 202 at 10.220.1.62.

## Backup Schedule

### Daily Snapshots

Backups run daily at 2 AM with staggered start times per hypervisor:

| Hypervisor | Agent VMs | Start Time | Stagger |
|------------|-----------|------------|---------|
| r820.infiquetra.com | Zeus (100) | 2:00 AM | +0 min |
| r640-2.infiquetra.com | Athena (101), Prometheus (106) | 2:10 AM | +10 min |
| r640-1.infiquetra.com | Apollo (102), Perseus (105) | 2:20 AM | +20 min |
| r420.infiquetra.com | Artemis (103), Hephaestus (104) | 2:30 AM | +30 min |
| r720xd.infiquetra.com | Ares (107) | 2:40 AM | +40 min |

**Stagger rationale:**
- Reduces network congestion during rsync
- Spreads storage I/O load
- Prevents resource contention
- Enables sequential monitoring

### Retention Policy

- **Local backups**: 7 days on each hypervisor
- **Remote backups**: 7 days on PBS (VM 202, 10.220.1.62)
- **Rotation**: Automatic cleanup of backups older than 7 days
- **Archive**: Manual long-term archives can be created separately

## Backup Components

### 1. VM Snapshots

**Method**: Proxmox Backup Server (PBS) vzdump snapshots

```bash
# Create snapshot via Proxmox
vzdump <vmid> --storage pbs --mode snapshot --compress zstd
```

**What's captured:**
- VM disk state (qcow2 images)
- Current configuration (XML dump)
- Disk layout and specifications

**Quiesce behavior:**
- Uses qemu-guest-agent to flush buffers
- Ensures filesystem consistency
- Falls back to non-quiesced if agent unavailable

### 2. VM Configuration Export

```bash
# Export VM configuration
qm config <vmid> > /backups/<date>/<vm>.conf
```

**What's captured:**
- vCPU allocation
- Memory configuration
- Network interfaces
- Disk attachments
- Device configuration

**Use case**: Recreate VM exactly as configured

### 3. Disk Images

```bash
# Copy disk images during snapshot
cp -a <disk-path> /backups/<date>/<vm>_<disk-name>
```

**What's captured:**
- All VM disk images
- Preserves attributes and permissions
- Point-in-time consistency

### 4. Hermes Memory Export

**Agent VMs only** (IPs 10.220.1.50-57):

```bash
# SSH to agent VM and export Hermes data
ssh agent@<vm-ip> "tar -czf /tmp/hermes-data.tar.gz \
  -C ~/.hermes ."

# Copy back to hypervisor
scp agent@<vm-ip>:/tmp/hermes-data.tar.gz \
  /backups/<date>/<vm>_hermes.tar.gz
```

**What's captured:**
- `memory.db` — primary persistent data (agent memory and context)
- `config.yml` — agent configuration
- `.env` — environment variables and API keys

**Use case**: Restore agent memory and configuration

### 5. Snapshot Management

PBS handles snapshot storage and pruning automatically. Proxmox snapshot cleanup:

```bash
# List snapshots for a VM
qm listsnapshot <vmid>

# Delete old snapshot
qm delsnapshot <vmid> <snapname>
```

**PBS prune rules:**
- Keeps last 7 daily backups
- Automatic garbage collection
- Deduplication via PBS datastore

## Off-Hypervisor Backup

### Proxmox Backup Server (PBS)

All VM backups are stored on PBS (VM 202 at 10.220.1.62), running on r720xd with access to the `ceph-bulk` storage pool.

**PBS Web UI**: https://10.220.1.62:8007

**Backup flow:**
- Each Proxmox host sends vzdump snapshots directly to PBS
- PBS handles deduplication, compression, and retention
- Backups are stored in the PBS datastore on Ceph bulk storage

**Verify backups:**
```bash
# Check PBS backup status from any Proxmox host
pvesm list pbs

# Or via PBS web UI for detailed datastore info
```

## Backup Verification

### Automated Checks

The backup script logs all operations to `/var/log/vm-backup.log`:

```bash
# Check last backup status
tail -n 50 /var/log/vm-backup.log

# Check for errors
grep -i error /var/log/vm-backup.log

# Check backup completion
grep "All backup operations completed" /var/log/vm-backup.log
```

### Manual Verification

**Weekly verification checklist:**

1. **Check PBS datastore status**
   ```bash
   # Via PBS web UI at https://10.220.1.62:8007
   # Or from Proxmox host:
   pvesm status | grep pbs
   ```

2. **Verify recent backups**
   ```bash
   pvesm list pbs | tail -20
   ```

3. **Check backup sizes** (should be similar day-to-day)
   ```bash
   # Via PBS web UI → Datastore → Content
   ```

4. **Verify PBS disk space**
   ```bash
   ssh root@10.220.1.62 "df -h"
   ```

5. **Test restore** (quarterly, in test environment)

## Recovery Procedures

### Restore Single VM

1. **Stop the VM**
   ```bash
   qm stop <vmid>
   ```

2. **Restore from PBS**
   ```bash
   # Via Proxmox web UI: Datacenter → Storage → PBS → Content
   # Select backup → Restore
   # Or via CLI:
   qmrestore <pbs-backup-path> <vmid> --storage ceph-fast
   ```

3. **Start the VM**
   ```bash
   qm start <vmid>
   ```

4. **Restore Hermes data (agent VMs)**
   ```bash
   scp /backups/<date>/<vm>_hermes.tar.gz agent@<vm-ip>:/tmp/

   ssh agent@<vm-ip> "tar -xzf /tmp/hermes-data.tar.gz -C ~/.hermes/"
   sudo systemctl restart hermes-<agent>
   ```

### Restore from PBS

PBS stores all backups centrally. To restore on any Proxmox host:

1. **Browse PBS backups** via Proxmox web UI or:
   ```bash
   pvesm list pbs --vmid <vmid>
   ```

2. **Restore to target host**
   ```bash
   qmrestore <pbs-backup-path> <vmid> --storage ceph-fast
   ```

### Disaster Recovery (Complete Hypervisor Loss)

1. **Reinstall Proxmox VE** on the server (if hardware intact)

2. **Re-join the cluster**
   ```bash
   pvecm add r420.infiquetra.com
   ```

3. **Restore VMs from PBS**
   ```bash
   # List available backups
   pvesm list pbs

   # Restore each VM that was on this host
   qmrestore <pbs-backup-path> <vmid> --storage ceph-fast
   ```

4. **Start VMs**
   ```bash
   for vmid in <list-of-vmids>; do
     qm start $vmid
   done
   ```

## Monitoring and Alerts

### Log Monitoring

Backup logs are written to `/var/log/vm-backup.log` on each hypervisor.

**Check for failures:**
```bash
# On each hypervisor
grep -i "warning\|error\|failed" /var/log/vm-backup.log | tail -n 20
```

**Success indicators:**
```bash
grep "All backup operations completed" /var/log/vm-backup.log | tail -n 7
```

### Disk Space Monitoring

**Check local storage:**
```bash
pvesm status
```

**Check PBS storage:**
```bash
ssh root@10.220.1.62 "df -h"
```

**Warning threshold**: < 20% free space
**Critical threshold**: < 10% free space

### Recommended Alerts

**Setup monitoring for:**
1. Backup script failures (check exit code in cron logs)
2. Disk space < 20% on backup volumes
3. Missing backup entries in PBS for current day (after 3 AM)
4. PBS datastore errors or connectivity failures
5. Log file size (indicates verbosity/errors if growing)

## Backup Security

### Access Control

- **Backup directories**: 755 permissions (root owned)
- **VM images**: 644 permissions
- **Remote backup**: SSH key-based auth only
- **No public access**: Internal network only

### Encryption

Current: **Not encrypted** (internal network, trusted environment)

**To enable encryption** (future enhancement):
```bash
# Encrypt backups before rsync
tar -czf - /var/lib/libvirt/backups/<date> | \
  gpg --encrypt --recipient backup@infiquetra.com > \
  /tmp/backup-<date>.tar.gz.gpg
```

## Maintenance Tasks

### Daily (Automated)
- ✅ Create VM snapshots
- ✅ Export configurations
- ✅ Copy disk images
- ✅ Export Hermes data
- ✅ PBS prune and garbage collection
- ✅ Clean old local backups

### Weekly (Manual)
- Check backup logs for errors
- Verify backup sizes are reasonable
- Check remote backup sync status
- Review disk space on all hypervisors

### Monthly (Manual)
- Test restore procedure on one VM
- Verify Hermes memory.db restores
- Review retention policy effectiveness
- Check for backup script improvements

### Quarterly (Manual)
- Full disaster recovery drill
- Document any issues encountered
- Update runbooks based on learnings
- Review and adjust retention policy

## Troubleshooting

### Backup Script Fails

**Check logs:**
```bash
tail -100 /var/log/vm-backup.log
```

**Common issues:**
1. **Disk full**: Clean old backups, increase retention
2. **qemu-guest-agent not responding**: Check agent service in VM
3. **VM not running**: Verify VM state, adjust script to handle
4. **rsync failure**: Check network, SSH keys, remote disk space

### PBS Backup Fails

**Symptoms**: vzdump errors in Proxmox task log

**Resolution:**
```bash
# Check PBS connectivity
pvesm status | grep pbs

# Check PBS VM is running
ssh root@10.220.1.10 "qm status 202"

# Check PBS datastore space
ssh root@10.220.1.62 "df -h"

# Manual backup attempt
vzdump <vmid> --storage pbs --mode snapshot --compress zstd
```

### Hermes Data Export Fails

**Symptoms**: "Hermes export failed" in logs

**Check:**
1. VM network connectivity
2. SSH access to agent@<vm-ip>
3. Hermes directory exists: `~/.hermes`
4. memory.db is not locked

**Manual export:**
```bash
ssh agent@<vm-ip> "tar -czf /tmp/test.tar.gz -C ~/.hermes . && ls -lh /tmp/test.tar.gz"
```

## Cost Considerations

### Storage Requirements

**Per agent VM (estimated):**
- VM disk: ~20GB (after OS + tools)
- Backup (compressed): ~8GB per snapshot
- Hermes data (~/.hermes/memory.db): ~100MB
- Total per day per VM: ~8.1GB

**Total storage:**
- 8 VMs × 8.1GB × 7 days = ~450GB for 7-day retention
- Local: Stored on Ceph
- Remote: PBS on r720xd (VM 202) with ceph-bulk storage, ~2.25TB estimated

### Network Bandwidth

**Daily transfer to r720xd:**
- Incremental rsync: ~50-100GB/day
- Mostly compressed disk images
- Network: 10GbE internal (sufficient)

## Future Enhancements

### Planned Improvements

1. **Encryption**: GPG encrypt backups before remote sync
2. **Compression**: Better compression for disk images
3. **Deduplication**: Reduce storage with dedup
4. **Monitoring**: Automated alerts on failure
5. **Cloud backup**: Long-term archive to S3/B2
6. **Backup validation**: Automated restore testing
7. **Metrics**: Backup duration, size trends, success rate

### Configuration Management

All backup configuration is managed through Ansible:
- **Service VM playbook**: `service_vms.yml` (deploys PBS)
- **PBS VM**: ID 202, r720xd, 10.220.1.62

To redeploy PBS:

```bash
ansible-playbook service_vms.yml --tags pbs --vault-password-file ~/.vault_pass.txt
```
