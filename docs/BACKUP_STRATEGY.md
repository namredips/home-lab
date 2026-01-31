# OpenClaw Backup Strategy

## Overview

The backup system provides comprehensive protection for the OpenClaw virtual employee infrastructure through automated VM snapshots, OpenClaw memory exports, and off-hypervisor redundancy.

## Backup Schedule

### Daily Snapshots

Backups run daily at 2 AM with staggered start times per hypervisor:

| Hypervisor | Agent VMs | Start Time | Stagger |
|------------|-----------|------------|---------|
| r420.infiquetra.com | Zeus | 2:00 AM | +0 min |
| r710.infiquetra.com | Athena, Apollo | 2:10 AM | +10 min |
| r8202.infiquetra.com | Artemis, Hermes | 2:20 AM | +20 min |
| r720xd.infiquetra.com | Perseus | 2:30 AM | +30 min |
| r820.infiquetra.com | Prometheus, Ares | 2:40 AM | +40 min |

**Stagger rationale:**
- Reduces network congestion during rsync
- Spreads storage I/O load
- Prevents resource contention
- Enables sequential monitoring

### Retention Policy

- **Local backups**: 7 days on each hypervisor
- **Remote backups**: 7 days on r720xd
- **Rotation**: Automatic cleanup of backups older than 7 days
- **Archive**: Manual long-term archives can be created separately

## Backup Components

### 1. VM Snapshots

**Method**: Live snapshots with qemu-guest-agent

```bash
# Create snapshot (with quiesce for filesystem consistency)
virsh snapshot-create-as --domain <vm> \
  --name backup-<timestamp> \
  --disk-only --atomic --quiesce
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
# Export VM definition
virsh dumpxml <vm> > /backups/<date>/<vm>.xml
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

### 4. OpenClaw Memory Export

**Agent VMs only** (IPs 10.220.1.50-57):

```bash
# SSH to agent VM and export workspace
ssh agent@<vm-ip> "tar -czf /tmp/openclaw-workspace.tar.gz \
  -C ~/.openclaw/workspace ."

# Copy back to hypervisor
scp agent@<vm-ip>:/tmp/openclaw-workspace.tar.gz \
  /backups/<date>/<vm>_openclaw.tar.gz
```

**What's captured:**
- SOUL.md, IDENTITY.md, AGENTS.md (personality files)
- BOOTSTRAP.md, USER.md (configuration)
- Any workspace state/context files
- Agent-specific memory and learning

**Use case**: Restore agent personality and learned context

### 5. Snapshot Merge

After backup, snapshots are merged back to base:

```bash
# Merge snapshot into base image
virsh blockcommit <vm> --active --pivot <disk>

# Clean up snapshot metadata
virsh snapshot-delete <vm> <snapshot-name> --metadata
```

**Why merge:**
- Prevents snapshot chain growth
- Maintains single base image per VM
- Reduces complexity
- Preserves performance

## Off-Hypervisor Backup

### Remote Sync to r720xd

```bash
rsync -avz --delete-after \
  /var/lib/libvirt/backups/ \
  root@r720xd.infiquetra.com:/mnt/backups/vm-snapshots/<hypervisor>/
```

**Target location**: `/mnt/backups/vm-snapshots/`

**Directory structure:**
```
/mnt/backups/vm-snapshots/
├── r420.infiquetra.com/
│   └── 2026-01-30/
│       ├── zeus.xml
│       ├── zeus_ubuntu-22.04.qcow2
│       └── zeus_openclaw.tar.gz
├── r710.infiquetra.com/
│   └── 2026-01-30/
│       ├── athena.xml
│       ├── athena_ubuntu-22.04.qcow2
│       ├── athena_openclaw.tar.gz
│       ├── apollo.xml
│       ├── apollo_ubuntu-22.04.qcow2
│       └── apollo_openclaw.tar.gz
└── ...
```

**Sync behavior:**
- Run after local backup completes
- `--delete-after` removes old backups post-transfer
- Compressed transfer to save bandwidth
- Preserves permissions and timestamps

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

1. **Check backup directories exist**
   ```bash
   ls -lh /var/lib/libvirt/backups/
   ```

2. **Verify recent backups**
   ```bash
   find /var/lib/libvirt/backups/ -type d -mtime -1
   ```

3. **Check backup sizes** (should be similar day-to-day)
   ```bash
   du -sh /var/lib/libvirt/backups/*
   ```

4. **Verify remote backups**
   ```bash
   ssh root@r720xd.infiquetra.com "ls -lh /mnt/backups/vm-snapshots/"
   ```

5. **Test restore** (quarterly, in test environment)

## Recovery Procedures

### Restore Single VM

1. **Stop the VM**
   ```bash
   virsh shutdown <vm>
   # Or force: virsh destroy <vm>
   ```

2. **Restore disk image**
   ```bash
   cp /var/lib/libvirt/backups/<date>/<vm>_<disk> \
      /var/lib/libvirt/images/<vm>.qcow2
   ```

3. **Restore configuration (if needed)**
   ```bash
   virsh define /var/lib/libvirt/backups/<date>/<vm>.xml
   ```

4. **Start the VM**
   ```bash
   virsh start <vm>
   ```

5. **Restore OpenClaw workspace (agent VMs)**
   ```bash
   scp /var/lib/libvirt/backups/<date>/<vm>_openclaw.tar.gz \
       agent@<vm-ip>:/tmp/

   ssh agent@<vm-ip> "tar -xzf /tmp/openclaw-workspace.tar.gz \
       -C ~/.openclaw/workspace/"
   ```

### Restore from Remote Backup

If local backups are lost:

1. **Sync from r720xd to hypervisor**
   ```bash
   rsync -avz root@r720xd.infiquetra.com:/mnt/backups/vm-snapshots/<hypervisor>/ \
       /var/lib/libvirt/backups/
   ```

2. **Follow normal restore procedure** (above)

### Disaster Recovery (Complete Hypervisor Loss)

1. **Reinstall hypervisor** (if hardware intact) or **migrate to new hardware**

2. **Run host_prepare role**
   ```bash
   ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
     --tags host_prepare --limit <hypervisor>
   ```

3. **Run libvirt role**
   ```bash
   ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
     --tags libvirt --limit <hypervisor>
   ```

4. **Restore backups from r720xd**
   ```bash
   rsync -avz root@r720xd.infiquetra.com:/mnt/backups/vm-snapshots/<hypervisor>/ \
       /var/lib/libvirt/backups/
   ```

5. **Restore each VM** (see "Restore Single VM" above)

6. **Recreate VM definitions if needed**
   ```bash
   for xml in /var/lib/libvirt/backups/<date>/*.xml; do
     virsh define "$xml"
   done
   ```

7. **Start VMs**
   ```bash
   for vm in zeus athena apollo artemis hermes perseus prometheus ares; do
     virsh start "$vm"
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

**Check local backup space:**
```bash
df -h /var/lib/libvirt/backups/
```

**Check remote backup space:**
```bash
ssh root@r720xd.infiquetra.com "df -h /mnt/backups/"
```

**Warning threshold**: < 20% free space
**Critical threshold**: < 10% free space

### Recommended Alerts

**Setup monitoring for:**
1. Backup script failures (check exit code in cron logs)
2. Disk space < 20% on backup volumes
3. Missing backup directories for current day (after 3 AM)
4. rsync failures to r720xd
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
- ✅ Export OpenClaw workspaces
- ✅ Merge snapshots
- ✅ Clean old backups
- ✅ Sync to r720xd

### Weekly (Manual)
- Check backup logs for errors
- Verify backup sizes are reasonable
- Check remote backup sync status
- Review disk space on all hypervisors

### Monthly (Manual)
- Test restore procedure on one VM
- Verify OpenClaw workspace restores
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

### Snapshot Won't Merge

**Symptoms**: "blockcommit failed" in logs

**Resolution:**
```bash
# Check snapshot chain
virsh snapshot-list <vm>

# Manual merge attempt
virsh blockcommit <vm> --domain <vm> --path <disk> --active --pivot --verbose

# If still fails, may need to consolidate manually
```

### Remote Backup Not Syncing

**Check SSH key:**
```bash
ssh root@r720xd.infiquetra.com "echo test"
```

**Check disk space:**
```bash
ssh root@r720xd.infiquetra.com "df -h /mnt/backups/"
```

**Manual sync:**
```bash
/usr/local/bin/backup_vms.sh
```

### OpenClaw Workspace Export Fails

**Symptoms**: "OpenClaw export failed" in logs

**Check:**
1. VM network connectivity
2. SSH access to agent@<vm-ip>
3. Workspace directory exists: `~/.openclaw/workspace`
4. Agent user has read permissions

**Manual export:**
```bash
ssh agent@<vm-ip> "tar -czf /tmp/test.tar.gz -C ~/.openclaw/workspace . && ls -lh /tmp/test.tar.gz"
```

## Cost Considerations

### Storage Requirements

**Per agent VM (estimated):**
- VM disk: ~20GB (after OS + tools)
- Backup (compressed): ~8GB per snapshot
- OpenClaw workspace: ~100MB
- Total per day per VM: ~8.1GB

**Total storage:**
- 8 VMs × 8.1GB × 7 days = ~450GB for 7-day retention
- Local: ~450GB per hypervisor
- Remote: ~450GB × 5 hypervisors = ~2.25TB on r720xd

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
- **Role**: `vm_backup`
- **Variables**: `roles/vm_backup/defaults/main.yml`
- **Templates**: `roles/vm_backup/templates/backup_vms.sh.j2`

To modify backup behavior, update Ansible variables and re-run playbook:

```bash
ansible-playbook openclaw_cluster.yml --tags vm_backup
```
