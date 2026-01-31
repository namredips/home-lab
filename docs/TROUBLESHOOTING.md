# Troubleshooting Guide

Common issues and solutions for the OpenClaw virtual employee infrastructure.

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

**Symptoms**: `virsh list` shows VM as "shut off", won't start

**Diagnosis**:
```bash
ssh jefcox@<hypervisor-host>
sudo virsh start <vm-name>
# Look for error messages

# Check libvirt logs
sudo journalctl -u libvirtd -n 50

# View VM console
sudo virsh console <vm-name>
```

**Common causes**:

1. **Storage permission issues**
   ```bash
   sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/*.qcow2
   sudo chmod 644 /var/lib/libvirt/images/*.qcow2
   ```

2. **Network conflict**
   ```bash
   sudo virsh net-list --all
   sudo virsh net-start default
   ```

3. **Insufficient resources**
   ```bash
   # Check available memory
   free -h

   # Check running VMs
   sudo virsh list --all
   ```

**Solution**: Recreate VM if corrupted
```bash
# Backup VM disk
sudo cp /var/lib/libvirt/images/athena.qcow2 /var/lib/libvirt/images/athena.qcow2.bak

# Destroy and undefine
sudo virsh destroy athena
sudo virsh undefine athena

# Re-run Ansible to recreate
ansible-playbook openclaw_cluster.yml --tags agent_vm --limit r420.infiquetra.com
```

### VM Unresponsive

**Symptoms**: VM running but not accessible via SSH or console

**Diagnosis**:
```bash
# Check VM is actually running
sudo virsh list

# Check VM console
sudo virsh console <vm-name>
# Press Enter - should see login prompt

# Check VM resource usage
sudo virsh dominfo <vm-name>
```

**Common causes**:

1. **High CPU/memory usage**
   - Reduce VM resources or stop other VMs

2. **Disk I/O bottleneck**
   ```bash
   # Check disk usage
   sudo virsh domblklist <vm-name>
   sudo iostat -x 1
   ```

3. **Cloud-init not finished**
   ```bash
   # Access console
   sudo virsh console <vm-name>
   # Login and check
   sudo cloud-init status
   ```

**Solution**: Force reset (last resort)
```bash
sudo virsh reset <vm-name>
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
# On hypervisor
ssh jefcox@<hypervisor>

# Expand QCOW2 image
sudo qemu-img resize /var/lib/libvirt/images/<vm>.qcow2 +100G

# On VM
ssh agent@<vm-ip>

# Grow partition (assuming single partition)
sudo growpart /dev/vda 1
sudo resize2fs /dev/vda1

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

3. **Libvirt network not running**
   ```bash
   # On hypervisor
   sudo virsh net-list --all
   sudo virsh net-start default
   sudo virsh net-autostart default
   ```

**Solution**: Recreate network config
```bash
# On VM (via console)
sudo nano /etc/netplan/50-cloud-init.yaml

# Ensure it contains:
network:
  version: 2
  ethernets:
    enp1s0:
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

### Mattermost Not Accessible

**Symptoms**: Can't access http://10.220.1.10:8065

**Diagnosis**:
```bash
ssh jefcox@10.220.1.10

# Check containers
docker ps

# Should see:
# - mattermost-app
# - mattermost-postgres

# Check container logs
docker logs mattermost-app
docker logs mattermost-postgres
```

**Common causes**:

1. **Containers not running**
   ```bash
   cd /opt/mattermost
   docker-compose up -d

   # Check status
   docker-compose ps
   ```

2. **Database not ready**
   ```bash
   # Check postgres health
   docker exec mattermost-postgres pg_isready -U mmuser

   # Restart Mattermost container
   docker-compose restart mattermost
   ```

3. **Port conflict**
   ```bash
   # Check if port 8065 is in use
   sudo netstat -tlnp | grep 8065
   ```

**Solution**: Restart services
```bash
cd /opt/mattermost
docker-compose down
docker-compose up -d

# Wait for startup
sleep 30

# Test
curl http://localhost:8065/api/v4/system/ping
```

### OpenClaw Service Won't Start

**Symptoms**: `systemctl status openclaw-<agent>` shows failed

**Diagnosis**:
```bash
ssh agent@<vm-ip>

# Check service status
sudo systemctl status openclaw-<agent>

# View logs
sudo journalctl -u openclaw-<agent> -n 100

# Check if openclaw binary exists
which openclaw
openclaw --version
```

**Common causes**:

1. **Missing API keys**
   ```bash
   cat ~/.openclaw/.env
   # Verify all API keys are set
   ```

2. **Invalid configuration**
   ```bash
   cat ~/.openclaw/config.yml
   # Check YAML syntax
   yamllint ~/.openclaw/config.yml
   ```

3. **Node.js not installed**
   ```bash
   node --version
   # Should be v22+
   ```

**Solution**: Manual start for debugging
```bash
# Stop service
sudo systemctl stop openclaw-<agent>

# Run manually to see errors
cd ~/.openclaw
openclaw start --config config.yml --verbose

# Fix errors, then restart service
sudo systemctl start openclaw-<agent>
```

### OpenClaw Not Connecting to Mattermost

**Symptoms**: Agent doesn't respond in Mattermost channels

**Diagnosis**:
```bash
# Check OpenClaw logs
ssh agent@<vm-ip>
tail -f ~/.openclaw/logs/openclaw.log

# Look for Mattermost connection errors

# Test Mattermost API from VM
curl http://10.220.1.10:8065/api/v4/system/ping

# Check bot token
cat ~/.openclaw/.env | grep MATTERMOST_BOT_TOKEN
```

**Common causes**:

1. **Invalid bot token**
   - Regenerate token in Mattermost
   - Update `~/.openclaw/.env`
   - Restart service

2. **Agent not member of team/channel**
   - Add agent to "Mount Olympus" team
   - Add to relevant channels

3. **Network connectivity**
   ```bash
   ping 10.220.1.10
   nc -zv 10.220.1.10 8065
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

**Symptoms**: OpenClaw logs show 401 errors for OpenAI

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
nano ~/.openclaw/.env

# Update OPENAI_API_KEY
OPENAI_API_KEY=sk-...

# Restart OpenClaw
sudo systemctl restart openclaw-<agent>
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

1. **OpenClaw running intensive task**
   - This is expected during code generation
   - Monitor and wait for completion

2. **Runaway process**
   - Kill process: `kill <pid>`
   - Restart OpenClaw if needed

3. **Insufficient CPU allocation**
   - Increase VM vCPUs on hypervisor
   ```bash
   sudo virsh shutdown <vm-name>
   sudo virsh setvcpus <vm-name> 8 --config --maximum
   sudo virsh setvcpus <vm-name> 8 --config
   sudo virsh start <vm-name>
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
# On hypervisor
sudo virsh shutdown <vm-name>
sudo virsh setmaxmem <vm-name> 32G --config
sudo virsh setmem <vm-name> 32G --config
sudo virsh start <vm-name>
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

**Backup VM disk**:
```bash
ssh jefcox@<hypervisor>
sudo cp /var/lib/libvirt/images/<vm>.qcow2 /var/lib/libvirt/images/<vm>.qcow2.bak
```

**Attempt repair**:
```bash
sudo qemu-img check -r all /var/lib/libvirt/images/<vm>.qcow2
```

**Restore from backup**:
```bash
sudo virsh destroy <vm-name>
sudo cp /var/lib/libvirt/images/<vm>.qcow2.bak /var/lib/libvirt/images/<vm>.qcow2
sudo virsh start <vm-name>
```

### Mattermost Data Recovery

**Backup**:
```bash
ssh jefcox@10.220.1.10

# Backup PostgreSQL database
docker exec mattermost-postgres pg_dump -U mmuser mattermost > /opt/mattermost/backup.sql

# Backup data directory
sudo tar czf /opt/mattermost/data-backup.tar.gz /opt/mattermost/data
```

**Restore**:
```bash
# Restore database
cat /opt/mattermost/backup.sql | docker exec -i mattermost-postgres psql -U mmuser -d mattermost

# Restore data
cd /opt/mattermost
sudo tar xzf data-backup.tar.gz

# Restart
docker-compose restart
```

### OpenClaw Configuration Recovery

**Backup**:
```bash
ssh agent@<vm-ip>
tar czf openclaw-backup.tar.gz ~/.openclaw/
```

**Restore**:
```bash
tar xzf openclaw-backup.tar.gz -C ~/
sudo systemctl restart openclaw-<agent>
```

---

## Getting Help

If none of these solutions work:

1. **Check logs systematically**:
   - VM: `sudo journalctl -xe`
   - OpenClaw: `~/.openclaw/logs/openclaw.log`
   - Mattermost: `docker logs mattermost-app`
   - Libvirt: `sudo journalctl -u libvirtd`

2. **Recreate from scratch**:
   - Destroy affected component
   - Re-run Ansible playbook for that component

3. **Ask in community**:
   - OpenClaw GitHub: https://github.com/openclaw/openclaw/issues
   - Mattermost community: https://mattermost.com/community

---

**Last Updated**: 2026-01-30
**Maintainer**: jeff@infiquetra.com
