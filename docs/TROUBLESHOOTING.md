# Troubleshooting Guide

Common issues and solutions for the Hermes agent infrastructure on the Proxmox "olympus" cluster.

## Table of Contents

1. [VM Issues](#vm-issues)
2. [Network Issues](#network-issues)
3. [Service Issues](#service-issues)
4. [Authentication Issues](#authentication-issues)
5. [Performance Issues](#performance-issues)
6. [Data Recovery](#data-recovery)

---

## VM Issues

### VM Won't Start

**Symptoms**: `qm list` shows VM as "stopped", won't start

**Diagnosis**:
```bash
ssh root@<hypervisor-host>
qm start <vmid>
# Look for error messages

# Check Proxmox logs
journalctl -u pvedaemon -n 50

# View VM console
qm terminal <vmid>
```

**Common causes**:

1. **Ceph storage unavailable**
   ```bash
   ceph status
   pvesm status
   ```

2. **Network bridge issue**
   ```bash
   ip link show vmbr0
   ip link show vmbr1
   ```

3. **Insufficient resources**
   ```bash
   # Check available memory
   free -h

   # Check running VMs
   qm list
   ```

**Solution**: Recreate VM if corrupted
```bash
# Stop and destroy
qm stop <vmid>
qm destroy <vmid>

# Re-run Ansible to recreate
ansible-playbook proxmox_cluster.yml --tags proxmox_vm --limit <host>.infiquetra.com \
  --vault-password-file ~/.vault_pass.txt
```

### VM Unresponsive

**Symptoms**: VM running but not accessible via SSH or console

**Diagnosis**:
```bash
# Check VM is actually running
qm list

# Check VM console via Proxmox web UI or:
qm terminal <vmid>
# Press Enter - should see login prompt

# Check VM resource usage
qm status <vmid> --verbose
```

**Common causes**:

1. **High CPU/memory usage**
   - Reduce VM resources or stop other VMs

2. **Disk I/O bottleneck**
   ```bash
   # Check from Proxmox host
   iostat -x 1
   ```

3. **Cloud-init not finished**
   ```bash
   # Access console
   qm terminal <vmid>
   # Login and check
   sudo cloud-init status
   ```

**Solution**: Force reset (last resort)
```bash
qm reset <vmid>
```

### VM Disk Full

**Symptoms**: Applications fail, errors about "no space left on device"

**Diagnosis**:
```bash
ssh agent@<vm-ip>
df -h
# Check which partition is full

# Check largest directories
sudo du -h --max-depth=1 / | sort -h
```

**Solution**: Expand disk
```bash
# On Proxmox host — resize the VM disk
qm resize <vmid> scsi0 +100G

# On VM — grow the partition
ssh agent@<vm-ip>
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1

# Verify
df -h
```

---

## Network Issues

### Can't Ping VM

**Symptoms**: `ping <vm-ip>` times out

**Diagnosis**:
```bash
# From hypervisor
ssh jefcox@<hypervisor>
sudo virsh console <vm-name>

# Check network interface
ip addr show
# Should see enp1s0 with IP

# Check routing
ip route

# Try ping from VM
ping 8.8.8.8
ping 10.220.1.1  # Gateway
```

**Common causes**:

1. **Network not configured in cloud-init**
   - Check `/tmp/<agent>-cloudinit.yml` on hypervisor
   - Verify IP address is correct

2. **Network interface down**
   ```bash
   # On VM
   sudo ip link set enp1s0 up
   sudo systemctl restart systemd-networkd
   ```

3. **Proxmox bridge not up**
   ```bash
   # On hypervisor
   ip link show vmbr0
   ip link show vmbr1  # Ceph network
   ```

**Solution**: Recreate network config
```bash
# On VM (via console: qm terminal <vmid>)
sudo nano /etc/netplan/50-cloud-init.yaml

# Ensure it contains:
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: false
      addresses:
        - 10.220.1.XX/24
      gateway4: 10.220.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

# Apply
sudo netplan apply
```

### SSH Connection Refused

**Symptoms**: `ssh agent@<vm-ip>` returns "Connection refused"

**Diagnosis**:
```bash
# Check if port 22 is open
nc -zv <vm-ip> 22

# Check from hypervisor console
sudo virsh console <vm-name>
# Login and check SSH service
sudo systemctl status sshd
```

**Common causes**:

1. **SSH service not running**
   ```bash
   sudo systemctl start sshd
   sudo systemctl enable sshd
   ```

2. **Firewall blocking**
   ```bash
   sudo ufw status
   sudo ufw allow 22
   ```

3. **Wrong IP address**
   ```bash
   # Verify actual IP
   ip addr show enp1s0
   ```

### SSH Key Authentication Fails

**Symptoms**: "Permission denied (publickey)"

**Diagnosis**:
```bash
# Try verbose SSH
ssh -v agent@<vm-ip>
# Look for key exchange messages

# Check if key is offered
ssh-add -l
```

**Common causes**:

1. **SSH key not in authorized_keys**
   ```bash
   # Via console
   sudo virsh console <vm-name>
   # Login and check
   cat ~/.ssh/authorized_keys
   ```

2. **Wrong permissions**
   ```bash
   # On VM
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Cloud-init didn't run**
   ```bash
   # Check cloud-init status
   sudo cloud-init status --long
   sudo cat /var/log/cloud-init-output.log
   ```

**Solution**: Manually add key
```bash
# Via console
sudo virsh console <vm-name>
# Login as agent
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
# Paste public key from ~/.ssh/id_rsa.pub on local machine
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## Service Issues

### Hermes Service Won't Start

**Symptoms**: `systemctl status hermes-<agent>` shows failed

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Check service status
sudo systemctl status hermes-<agent>

# View logs
sudo journalctl -u hermes-<agent> -n 100

# Check configuration
cat ~/.hermes/config.yml
```

**Common causes**:

1. **Missing API keys or Discord token**
   ```bash
   cat ~/.hermes/.env
   # Verify DISCORD_BOT_TOKEN and API keys are set
   ```

2. **Invalid configuration**
   ```bash
   cat ~/.hermes/config.yml
   # Check YAML syntax
   yamllint ~/.hermes/config.yml
   ```

3. **Node.js not installed**
   ```bash
   node --version
   # Should be v22+
   ```

**Solution**: Manual start for debugging
```bash
# Stop service
sudo systemctl stop hermes-<agent>

# Check logs for specific errors
sudo journalctl -u hermes-<agent> -n 200 --no-pager

# Fix errors, then restart service
sudo systemctl start hermes-<agent>
```

### Agent Not Responding in Discord

**Symptoms**: Agent doesn't respond in Discord channels

**Diagnosis**:
```bash
# Check Hermes logs
ssh agent@<vm-ip>
sudo journalctl -u hermes-<agent> -f

# Look for Discord connection errors

# Check bot token
cat ~/.hermes/.env | grep DISCORD_BOT_TOKEN
```

**Common causes**:

1. **Invalid Discord bot token**
   - Regenerate token at https://discord.com/developers/applications
   - Update vault: `vault_discord_bot_token_<agent>`
   - Re-run `hermes_cluster.yml` or manually update `~/.hermes/.env`
   - Restart service

2. **Bot not invited to server/channels**
   - Check bot has proper permissions in Discord server settings

3. **Network connectivity**
   ```bash
   # Test outbound HTTPS (Discord API)
   curl -s https://discord.com/api/v10/gateway
   ```

---

## Authentication Issues

### Claude Code Authentication Fails

**Symptoms**: `claude-code auth` doesn't complete, or CLI says not authenticated

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Check auth status
claude-code auth status

# Check if browser is accessible (for OAuth)
# (May need to run on VM with GUI or use port forwarding)
```

**Solution**: Re-authenticate
```bash
# Logout
claude-code auth logout

# Login again
claude-code auth

# If OAuth browser not available, use device code flow
# (Follow instructions from claude-code auth)
```

### OpenAI API Key Invalid

**Symptoms**: Hermes logs show 401 errors for OpenAI

**Diagnosis**:
```bash
# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Should return list of models, not error
```

**Solution**: Update API key
```bash
# Edit environment file
nano ~/.hermes/.env

# Update OPENAI_API_KEY
OPENAI_API_KEY=sk-...

# Restart Hermes
sudo systemctl restart hermes-<agent>
```

### GitHub Authentication Issues

**Symptoms**: `git push` fails with authentication error

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Test SSH to GitHub
ssh -T git@github.com
# Should say "Hi <username>! You've successfully authenticated"

# Check SSH key
cat ~/.ssh/id_ed25519.pub

# Verify key is added to GitHub account
```

**Solution**: Add SSH key to GitHub
```bash
# Generate new key if needed
ssh-keygen -t ed25519 -C "agent@infiquetra.com"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Copy and add to GitHub:
# https://github.com/settings/keys
```

---

## Performance Issues

### High CPU Usage

**Symptoms**: VM sluggish, `htop` shows high CPU

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Check CPU usage
htop
top

# Identify process
ps aux --sort=-%cpu | head -10
```

**Common causes**:

1. **Hermes running intensive task**
   - This is expected during code generation
   - Monitor and wait for completion

2. **Runaway process**
   - Kill process: `kill <pid>`
   - Restart Hermes if needed

3. **Insufficient CPU allocation**
   - Increase VM vCPUs via Proxmox web UI or:
   ```bash
   qm set <vmid> --cores 8
   qm reboot <vmid>
   ```

### High Memory Usage

**Symptoms**: VM slow, `free -h` shows low available memory

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Check memory
free -h

# Identify memory hogs
ps aux --sort=-%mem | head -10
```

**Solution**: Increase VM memory
```bash
# Via Proxmox web UI or CLI:
qm set <vmid> --memory 32768
qm reboot <vmid>
```

### Slow Disk I/O

**Symptoms**: Operations take long time, high `iowait` in `htop`

**Diagnosis**:
```bash
# Check disk I/O
iostat -x 1

# Check disk usage
df -h
du -h --max-depth=1 ~
```

**Solution**: Clean up disk or migrate to SSD
```bash
# Clean Docker
docker system prune -a

# Clean package cache
sudo apt clean
sudo apt autoremove

# Clean logs
sudo journalctl --vacuum-time=7d
```

---

## Data Recovery

### VM Disk Corruption

**Restore from PBS backup**:
```bash
# Stop the VM
qm stop <vmid>

# Restore from PBS (via Proxmox web UI or CLI)
qmrestore <pbs-backup-path> <vmid> --storage ceph-fast

# Start the VM
qm start <vmid>
```

### Hermes Configuration Recovery

**Backup**:
```bash
ssh agent@<vm-ip>
tar czf hermes-backup.tar.gz ~/.hermes/
```

**Restore**:
```bash
tar xzf hermes-backup.tar.gz -C ~/
sudo systemctl restart hermes-<agent>
```

---

## Getting Help

If none of these solutions work:

1. **Check logs systematically**:
   - VM: `sudo journalctl -xe`
   - Hermes: `sudo journalctl -u hermes-<agent>`
   - Proxmox: `journalctl -u pvedaemon`
   - Ceph: `ceph status` / `ceph health detail`

2. **Recreate from scratch**:
   - Destroy affected component
   - Re-run Ansible playbook for that component

3. **Proxmox community**:
   - Proxmox forums: https://forum.proxmox.com/

---

**Last Updated**: 2026-03-28
**Maintainer**: jeff@infiquetra.com
