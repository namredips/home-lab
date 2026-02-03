# VM Network Recovery - Implementation Summary

**Date**: 2026-02-03
**Status**: Ready for testing

---

## What Was Changed

### 1. Fixed Seed ISO Regeneration Issue

**File**: `ansible/roles/agent_vm/tasks/create_vm.yml`

**Problem**: Seed ISOs were not regenerated when templates changed because of `creates:` condition.

**Fix**:
- Added task to remove old seed ISO before creating new one
- Removed `creates:` condition so ISO is always regenerated
- Added `--disk-format raw` for better compatibility

**Before**:
```yaml
- name: Create cloud-init ISO for {{ agent_name }}
  shell: |
    cloud-localds --network-config=/tmp/{{ agent_name }}-network-config.yml \
      /var/lib/libvirt/images/{{ agent_name }}-seed.img /tmp/{{ agent_name }}-cloudinit.yml
  become: yes
  args:
    creates: /var/lib/libvirt/images/{{ agent_name }}-seed.img
```

**After**:
```yaml
- name: Remove old cloud-init ISO for {{ agent_name }} if exists
  file:
    path: /var/lib/libvirt/images/{{ agent_name }}-seed.img
    state: absent
  become: yes

- name: Create cloud-init ISO for {{ agent_name }}
  shell: |
    cloud-localds \
      --disk-format raw \
      --network-config=/tmp/{{ agent_name }}-network-config.yml \
      /var/lib/libvirt/images/{{ agent_name }}-seed.img \
      /tmp/{{ agent_name }}-cloudinit.yml
  become: yes
```

### 2. Improved Network Configuration

**File**: `ansible/roles/agent_vm/templates/vm-network-config.yml.j2`

**Changes**:
- Changed interface ID from `id0` to `default` (more standard)
- Changed match pattern from `"en*"` to `"e*"` (catches eth*, ens*, enp*, etc.)
- Explicitly disabled DHCP (`dhcp4: false`, `dhcp6: false`)
- Fixed DNS servers to use local DNS (10.220.1.200) and Cloudflare (1.1.1.1)

**Before**:
```yaml
version: 2
renderer: networkd
ethernets:
  id0:
    match:
      name: "en*"
    addresses:
      - {{ agent_config.ip }}/24
    routes:
      - to: default
        via: 10.220.1.1
    nameservers:
      addresses:
        - 10.220.1.1
        - 8.8.8.8
```

**After**:
```yaml
version: 2
renderer: networkd
ethernets:
  default:
    match:
      name: "e*"
    dhcp4: false
    dhcp6: false
    addresses:
      - {{ agent_config.ip }}/24
    routes:
      - to: default
        via: 10.220.1.1
    nameservers:
      addresses:
        - 10.220.1.200
        - 1.1.1.1
```

### 3. Created Helper Playbook for Quick ISO Regeneration

**Files**:
- `ansible/regenerate_seed_isos.yml`
- `ansible/tasks/regenerate_seed_iso.yml`

**Purpose**: Allows regenerating seed ISOs and rebooting VMs without recreating them from scratch. Useful for testing cloud-init config changes.

**Usage**:
```bash
uv run ansible-playbook regenerate_seed_isos.yml --vault-password-file ~/.vault_pass.txt
```

### 4. Created Diagnostic Tools

**Files**:
- `scripts/diagnose_vm_network.sh` - Automated diagnostics to run on hypervisor
- `docs/VM_NETWORK_DIAGNOSTICS.md` - Manual diagnostic guide
- `docs/NETWORK_FIX_ANALYSIS.md` - Root cause analysis and fix details

---

## Testing Options

### Option 1: Full VM Recreate (Recommended)

Completely recreate all VMs with the fixed configuration:

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Destroy all VMs
uv run ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Recreate with fixed config
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Wait 60 seconds for cloud-init to complete
sleep 60

# Test all VMs
for ip in {50..57}; do
  echo -n "Testing 10.220.1.$ip... "
  ping -c 1 -W 2 10.220.1.$ip >/dev/null 2>&1 && echo "✓" || echo "✗"
done
```

**Pros**: Clean slate, guaranteed to work if config is correct
**Cons**: Takes ~10-15 minutes for all 8 VMs
**Risk**: Low

### Option 2: Quick ISO Regeneration (Faster)

Regenerate seed ISOs and reboot existing VMs:

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Regenerate ISOs and reboot VMs
uv run ansible-playbook regenerate_seed_isos.yml \
  --vault-password-file ~/.vault_pass.txt

# Test connectivity (playbook includes automatic testing)
```

**Pros**: Much faster (~2-3 minutes), preserves VM disks
**Cons**: If VM disk has network config applied during first boot, may not work
**Risk**: Medium - may need to fall back to Option 1

### Option 3: Manual Test on Single VM (Zeus)

Test on one VM before applying to all:

```bash
# SSH to r420
ssh jefcox@r420.infiquetra.com

# Stop Zeus
sudo virsh destroy zeus

# Regenerate seed ISO manually
cd /tmp
# Get the templates (from your control machine)
# Then:
sudo rm /var/lib/libvirt/images/zeus-seed.img
sudo cloud-localds \
  --disk-format raw \
  --network-config=/tmp/zeus-network-config.yml \
  /var/lib/libvirt/images/zeus-seed.img \
  /tmp/zeus-cloudinit.yml

# Start Zeus
sudo virsh start zeus

# Wait and test
sleep 40
ping -c 3 10.220.1.50
```

**Pros**: Safe, test before affecting all VMs
**Cons**: Manual process, requires copying files
**Risk**: Very low

---

## Recommended Workflow

1. **Run diagnostics first** (optional but helpful):
   ```bash
   scp scripts/diagnose_vm_network.sh jefcox@r420.infiquetra.com:/tmp/
   ssh jefcox@r420.infiquetra.com "/tmp/diagnose_vm_network.sh zeus"
   ```

2. **Try Option 2 (Quick Regeneration)**:
   ```bash
   cd ansible
   uv run ansible-playbook regenerate_seed_isos.yml --vault-password-file ~/.vault_pass.txt
   ```

3. **If Option 2 fails, use Option 1 (Full Recreate)**:
   ```bash
   uv run ansible-playbook openclaw_cluster_reset.yml --vault-password-file ~/.vault_pass.txt --tags=agent_vm
   uv run ansible-playbook openclaw_cluster.yml --vault-password-file ~/.vault_pass.txt --tags=agent_vm
   ```

4. **Verify all VMs are online**:
   ```bash
   for ip in {50..57}; do
     echo -n "10.220.1.$ip: "
     ping -c 1 -W 2 10.220.1.$ip >/dev/null 2>&1 && echo "✓ Online" || echo "✗ Offline"
   done
   ```

5. **Once working, commit changes**:
   ```bash
   git add ansible/roles/agent_vm
   git commit -m "fix(agent_vm): fix cloud-init network config application"
   ```

---

## Expected Results

After applying the fix, you should see:

### Successful Ping
```bash
$ ping 10.220.1.50
PING 10.220.1.50 (10.220.1.50): 56 data bytes
64 bytes from 10.220.1.50: icmp_seq=0 ttl=64 time=0.5 ms
```

### Successful SSH
```bash
$ ssh agent@10.220.1.50
agent@zeus:~$
```

### Correct Network Config Inside VM
```bash
$ ip addr show
2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 10.220.1.50/24 brd 10.220.1.255 scope global ens3
```

### Cloud-Init Success
```bash
$ cloud-init status
status: done
```

---

## Files Changed

```
M ansible/roles/agent_vm/tasks/create_vm.yml           # Fixed seed ISO regeneration
M ansible/roles/agent_vm/templates/vm-network-config.yml.j2  # Improved network config
A ansible/regenerate_seed_isos.yml                    # Helper playbook
A ansible/tasks/regenerate_seed_iso.yml               # Task include
A scripts/diagnose_vm_network.sh                      # Diagnostic script
A docs/VM_NETWORK_DIAGNOSTICS.md                      # Diagnostic guide
A docs/NETWORK_FIX_ANALYSIS.md                        # Root cause analysis
A docs/IMPLEMENTATION_SUMMARY.md                      # This file
```

---

## Next Phase

Once network is confirmed working, proceed to **Phase 2: Desktop Installation**:

```bash
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=agent_desktop
```

This will install:
- XFCE desktop environment
- XRDP remote desktop server
- Firefox and basic tools
- Development environment
