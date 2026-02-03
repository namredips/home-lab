# VM Network Diagnostics Guide

## Quick Start

### Option 1: Automated Diagnostics (no console needed)

```bash
# Copy script to hypervisor
scp scripts/diagnose_vm_network.sh jefcox@r420.infiquetra.com:/tmp/

# SSH to hypervisor and run
ssh jefcox@r420.infiquetra.com
chmod +x /tmp/diagnose_vm_network.sh
/tmp/diagnose_vm_network.sh zeus

# Review output and copy back
scp jefcox@r420.infiquetra.com:/tmp/vm-network-diag-zeus.txt ./
```

### Option 2: Manual Console Access

```bash
# SSH to hypervisor
ssh jefcox@r420.infiquetra.com

# Access VM console (use Ctrl+] to exit)
sudo virsh console zeus
```

**Login**: `agent` / `openclaw`

---

## Console Diagnostic Commands

Once logged into the VM console, run these commands in order:

### 1. Check Network Interfaces

```bash
# Show all interfaces and their IPs
ip addr show

# Show interface link status
ip link show

# Expected: Should see an interface (like ens3, enp1s0) with 10.220.1.50
```

### 2. Check Cloud-Init Status

```bash
# Overall status
cloud-init status --long

# Detailed status
sudo cat /run/cloud-init/status.json

# Check which datasource was used
cat /run/cloud-init/ds-identify.log 2>/dev/null || echo "No ds-identify log"
```

### 3. Check Network Configuration Files

```bash
# Check netplan config
cat /etc/netplan/*.yaml

# Check if seed ISO was mounted
ls -la /var/lib/cloud/seed/

# Check NoCloud datasource
ls -la /var/lib/cloud/seed/nocloud*
```

### 4. Check Cloud-Init Logs

```bash
# Recent errors
sudo grep -i error /var/log/cloud-init.log | tail -20

# Network configuration attempts
sudo grep -i network /var/log/cloud-init.log | tail -30

# Full cloud-init output
sudo cat /var/log/cloud-init-output.log
```

### 5. Manual Network Test

```bash
# If interface exists but has no IP, try DHCP
sudo dhclient -v <interface-name>

# Or try to manually apply netplan
sudo netplan apply
```

---

## Common Findings & Fixes

### Scenario A: Cloud-Init Ran But No Network Config

**Symptoms:**
- `cloud-init status` shows "done"
- Interface exists but has no IP or wrong IP
- `/etc/netplan/*.yaml` is empty or has default config

**Likely Cause:** Network-config from seed ISO not applied

**Fix:**
1. Check seed ISO is attached and readable
2. Verify network-config section in seed ISO
3. May need to use different datasource format or add `ds: nocloud-net` to meta-data

### Scenario B: Interface Exists But Wrong Name

**Symptoms:**
- Interface like `ens3` exists but config expects `en*`
- Netplan shows config but no match

**Likely Cause:** Interface naming mismatch

**Fix:**
1. Note actual interface name from `ip addr show`
2. Update `vm-network-config.yml.j2` to match actual interface name
3. Recreate VMs

### Scenario C: Cloud-Init Didn't Run

**Symptoms:**
- `cloud-init status` shows "not run" or "disabled"
- No logs in `/var/log/cloud-init.log`
- Seed ISO not found in `/var/lib/cloud/seed/`

**Likely Cause:** Seed ISO not attached or not recognized

**Fix:**
1. Check `virsh domblklist zeus` - should show seed ISO as CDROM
2. Verify seed ISO file exists on hypervisor
3. May need to recreate seed ISO with correct label

### Scenario D: Libvirt Bridge Misconfigured

**Symptoms:**
- Cloud-init applied network config correctly
- Interface has IP but no connectivity
- ARP incomplete on control machine

**Likely Cause:** `host-bridge` network doesn't route to physical network

**Fix:**
1. Check `virsh net-info host-bridge`
2. Verify bridge on hypervisor: `ip addr show br0`
3. May need to define proper bridge network in libvirt

---

## Expected Working State

### Correct Cloud-Init Status
```bash
$ cloud-init status --long
status: done
```

### Correct Network Interface
```bash
$ ip addr show
2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 10.220.1.50/24 brd 10.220.1.255 scope global ens3
```

### Correct Netplan Config
```yaml
# /etc/netplan/50-cloud-init.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    ens3:
      addresses:
        - 10.220.1.50/24
      routes:
        - to: default
          via: 10.220.1.1
      nameservers:
        addresses:
          - 10.220.1.200
          - 1.1.1.1
```

---

## Data Collection for Claude

After running diagnostics, collect this info:

```bash
# On the VM console
ip addr show > /tmp/diag-ip-addr.txt
cloud-init status --long > /tmp/diag-cloud-init-status.txt
sudo cat /var/log/cloud-init.log > /tmp/diag-cloud-init-log.txt
cat /etc/netplan/*.yaml > /tmp/diag-netplan.txt
ls -la /var/lib/cloud/seed/ > /tmp/diag-seed.txt

# Exit console (Ctrl+])
# Copy files from VM (if SSH works to hypervisor)
# Otherwise, screenshot or manually copy key sections
```

---

## Next Steps After Diagnosis

Based on findings, proceed to:
1. **Fix identified issue** in ansible templates
2. **Recreate VMs** with fixed config
3. **Verify network** with ping/SSH
4. **Commit changes** once working
