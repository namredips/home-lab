# Network Configuration Fix Analysis

## Issues Identified

### 1. Seed ISO Not Regenerated After Template Changes
**Problem**: The `create_vm.yml` task uses `creates:` condition:
```yaml
args:
  creates: /var/lib/libvirt/images/{{ agent_name }}-seed.img
```

**Impact**: If you modified `vm-network-config.yml.j2` after VMs were created, the old seed ISO with the old config is still attached. The new config never made it into the VMs.

**Evidence**: Your uncommitted changes show you added `renderer: networkd` to the template, but VMs were already created with the old ISO.

### 2. Network Config Match Pattern May Be Too Generic
**Problem**: Current config uses:
```yaml
ethernets:
  id0:
    match:
      name: "en*"
```

**Issue**:
- If VM has multiple interfaces matching `en*`, cloud-init may not apply config
- Some Ubuntu cloud images use predictable names like `ens3`, `enp1s0` which should match, but better to be specific

**Better approach**: Use `macaddress` match or specific interface name

### 3. NoCloud Datasource May Need Explicit Label
**Problem**: `cloud-localds` creates ISO with default label, but some cloud-init versions require specific volume label to detect NoCloud datasource.

**Fix**: Add explicit label to seed ISO creation

---

## Recommended Fixes (in priority order)

### Fix #1: Force Regeneration of Seed ISOs (IMMEDIATE)

Since you've modified the network config template, you need to regenerate the seed ISOs:

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Option A: Delete existing seed ISOs and recreate VMs
uv run ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Option B: Just regenerate and reattach seed ISOs (faster, but riskier)
# (Requires custom playbook - see below)
```

### Fix #2: Improve Network Config Template

**Change from:**
```yaml
version: 2
renderer: networkd
ethernets:
  id0:
    match:
      name: "en*"
    addresses:
      - {{ agent_config.ip }}/24
```

**Change to (more explicit):**
```yaml
version: 2
renderer: networkd
ethernets:
  default:
    match:
      name: "e*"  # Match en*, eth*, enp*, ens*
    dhcp4: false
    dhcp6: false
    addresses:
      - {{ agent_config.ip }}/24
```

**Or even better (if we can get MAC addresses):**
```yaml
version: 2
renderer: networkd
ethernets:
  default:
    match:
      macaddress: "{{ agent_config.mac }}"  # Most reliable
    addresses:
      - {{ agent_config.ip }}/24
```

### Fix #3: Improve Cloud-Init Seed ISO Creation

**Change from:**
```yaml
- name: Create cloud-init ISO for {{ agent_name }}
  shell: |
    cloud-localds --network-config=/tmp/{{ agent_name }}-network-config.yml \
      /var/lib/libvirt/images/{{ agent_name }}-seed.img /tmp/{{ agent_name }}-cloudinit.yml
  become: yes
  args:
    creates: /var/lib/libvirt/images/{{ agent_name }}-seed.img
```

**Change to:**
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

**Why**:
- Remove `creates:` so ISO is regenerated on every run
- Add `--disk-format raw` for better compatibility
- Ensure network-config is properly embedded

### Fix #4: Add Meta-Data File for NoCloud Datasource

Some cloud-init versions require a `meta-data` file in addition to user-data:

**Create new template: `vm-metadata.yml.j2`:**
```yaml
instance-id: {{ agent_name }}-{{ ansible_date_time.epoch }}
local-hostname: {{ agent_name }}
```

**Update seed ISO creation:**
```bash
cloud-localds \
  --meta-data=/tmp/{{ agent_name }}-metadata.yml \
  --network-config=/tmp/{{ agent_name }}-network-config.yml \
  /var/lib/libvirt/images/{{ agent_name }}-seed.img \
  /tmp/{{ agent_name }}-cloudinit.yml
```

---

## Testing Plan

### Step 1: Manual Test on One VM (Zeus)

Before recreating all 8 VMs, test the fix on one:

```bash
# SSH to r420 hypervisor
ssh jefcox@r420.infiquetra.com

# Stop Zeus VM
sudo virsh destroy zeus

# Regenerate configs with new template
cd /tmp
# Copy updated templates from control machine

# Recreate seed ISO
sudo rm /var/lib/libvirt/images/zeus-seed.img
sudo cloud-localds \
  --disk-format raw \
  --network-config=/tmp/zeus-network-config.yml \
  /var/lib/libvirt/images/zeus-seed.img \
  /tmp/zeus-cloudinit.yml

# Start VM
sudo virsh start zeus

# Wait 30 seconds for cloud-init
sleep 30

# Test connectivity
ping -c 3 10.220.1.50

# If successful, SSH in
ssh agent@10.220.1.50
```

### Step 2: Apply to All VMs

Once Zeus works:

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Reset all VMs
uv run ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Recreate with fixed config
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Verify all VMs
for ip in {50..57}; do
  echo "Testing 10.220.1.$ip..."
  ping -c 1 10.220.1.$ip && echo "✓ Success" || echo "✗ Failed"
done
```

---

## Root Cause Summary

**Most Likely**: Seed ISOs were not regenerated after you modified the network config template. VMs are running with old seed ISOs that don't have the `renderer: networkd` directive.

**Secondary**: The `match: name: "en*"` pattern combined with arbitrary interface ID `id0` may cause issues on some cloud-init versions.

**Tertiary**: Missing explicit datasource detection hints (no meta-data file, no volume label).

---

## Immediate Action

Run the diagnostic script on r420 to confirm:

```bash
scp scripts/diagnose_vm_network.sh jefcox@r420.infiquetra.com:/tmp/
ssh jefcox@r420.infiquetra.com "/tmp/diagnose_vm_network.sh zeus"
```

Then based on diagnostics, apply fixes in this order:
1. Fix seed ISO regeneration in ansible tasks
2. Recreate VMs
3. Test connectivity
4. Commit changes
