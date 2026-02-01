# Sudo Access Bug Fix - Applied

**Date**: 2026-01-31
**Status**: Ready for Deployment

---

## What Was Fixed

### 1. Broken User Group Removal (libvirt/tasks/reset.yml)

**Before** (lines 22-29):
```yaml
- name: Remove user from libvirt groups
  user:
    name: "{{ libvirt_user }}"
    groups:
      - libvirt
      - kvm
    append: no  # BUG: This SETS groups, doesn't remove
```

**After**:
```yaml
- name: Remove user from libvirt group
  shell: gpasswd -d {{ libvirt_user }} libvirt 2>/dev/null || true
  become: yes
  when: running_vms.stdout_lines | length == 0

- name: Remove user from kvm group
  shell: gpasswd -d {{ libvirt_user }} kvm 2>/dev/null || true
  become: yes
  when: running_vms.stdout_lines | length == 0
```

**Why This Matters**: The `user` module with `append: no` REPLACES all groups with the specified list. This removed jefcox from sudo, adm, and all other groups. The `gpasswd -d` command only removes from the specified group.

---

### 2. Sudo Safeguards Added (host_prepare/tasks/sudo_safeguard.yml)

**New File Created** with triple protection:

```yaml
# 1. Permanent sudoers file (survives any group changes)
- name: Create permanent sudo access for jefcox
  copy:
    content: "jefcox ALL=(ALL) NOPASSWD:ALL"
    dest: /etc/sudoers.d/jefcox-permanent
    mode: '0440'
    validate: 'visudo -cf %s'

# 2. Ensure sudo group membership (belt AND suspenders)
- name: Ensure jefcox is in sudo group
  user:
    name: jefcox
    groups: sudo
    append: yes  # CRITICAL: append, never replace

# 3. Emergency recovery tool
- name: Install polkit for emergency recovery
  apt:
    name: policykit-1
    state: present
```

**Updated**: `host_prepare/tasks/main.yml` to include sudo_safeguard.yml

---

### 3. Pre-flight Safety Check (openclaw_cluster_reset.yml)

**Added Before Any Destructive Operations**:

```yaml
- name: Pre-flight safety check
  hosts: hypervisors
  gather_facts: no
  tasks:
    - name: Verify sudo access before proceeding
      command: sudo whoami
      changed_when: false

    - name: Verify sudoers.d backup exists
      stat:
        path: /etc/sudoers.d/jefcox-permanent
      register: sudo_backup

    - name: ABORT if no sudo safeguard
      fail:
        msg: "SAFETY: /etc/sudoers.d/jefcox-permanent missing. Run host_prepare first."
      when: not sudo_backup.stat.exists
```

---

## Deployment Instructions

### Step 1: Deploy Sudo Safeguards to All Hypervisors

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Deploy safeguards first
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=host_prepare
```

### Step 2: Verify Safeguards Are In Place

```bash
# Check all hypervisors have the permanent sudoers file
uv run ansible hypervisors \
  -m shell \
  -a "cat /etc/sudoers.d/jefcox-permanent" \
  -b
```

Expected output on each host:
```
jefcox ALL=(ALL) NOPASSWD:ALL
```

### Step 3: Reset Existing VMs (Now Safe)

```bash
# The pre-flight check will verify safeguards before proceeding
uv run ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=agent_vm
```

### Step 4: Full Deployment

```bash
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```

---

## Verification After Deployment

### 1. Verify Sudo Safeguards on All Hypervisors

```bash
for host in r420 r710 r8202 r720xd r820; do
  echo "=== Checking ${host} ==="
  ssh jefcox@${host}.infiquetra.com "cat /etc/sudoers.d/jefcox-permanent"
  ssh jefcox@${host}.infiquetra.com "groups jefcox"
  echo ""
done
```

Expected:
- `/etc/sudoers.d/jefcox-permanent` contains: `jefcox ALL=(ALL) NOPASSWD:ALL`
- Groups include: `sudo`, `adm`, `libvirt`, `kvm`

### 2. Check All VMs Running

```bash
for host in r420 r710 r8202 r720xd r820; do
  echo "=== ${host} VMs ==="
  ssh jefcox@${host}.infiquetra.com \
    "LIBVIRT_DEFAULT_URI=qemu:///system virsh list --all"
done
```

### 3. Check VMs Accessible on Physical Network

```bash
# Test all 8 agent VMs (10.220.1.50-57)
for ip in 50 51 52 53 54 55 56 57; do
  ping -c 1 10.220.1.$ip && echo "✓ 10.220.1.$ip" || echo "✗ 10.220.1.$ip"
done
```

### 4. SSH to an Agent

```bash
# Zeus VM should be at 10.220.1.50
ssh agent@10.220.1.50
```

### 5. Verify Mattermost

```bash
curl -s http://10.220.1.10:8065/api/v4/system/ping
```

Expected: `{"status":"OK"}`

---

## Safety Mechanisms Now in Place

| Protection | Location | Purpose |
|------------|----------|---------|
| **Permanent sudoers file** | `/etc/sudoers.d/jefcox-permanent` | Survives any group changes |
| **Sudo group membership** | `user: append=yes` | Maintained even if other tasks run |
| **Pre-flight check** | Reset playbook | Verifies safeguards before destructive ops |
| **Fixed reset task** | `libvirt/tasks/reset.yml` | Only removes specific groups |
| **Polkit installed** | Emergency recovery | `pkexec` available if SSH sudo fails |

---

## What Can't Go Wrong Now

1. **No more sudo lockout**: The `/etc/sudoers.d/jefcox-permanent` file gives sudo access independent of group membership
2. **Pre-flight detection**: Reset playbook checks for safeguards before running
3. **Safe group removal**: `gpasswd -d` only touches specific groups
4. **Emergency recovery**: `pkexec` available for local console access

---

## Files Modified

```
ansible/roles/libvirt/tasks/reset.yml              # Fixed group removal bug
ansible/roles/host_prepare/tasks/sudo_safeguard.yml # NEW: Sudo protection
ansible/roles/host_prepare/tasks/main.yml          # Include safeguard tasks
ansible/openclaw_cluster_reset.yml                  # Pre-flight safety check
```

---

## Next Steps

1. ✅ **Fixes applied** (all code changes complete)
2. ⏳ **Deploy safeguards** (Step 1 above)
3. ⏳ **Verify safeguards** (Step 2 above)
4. ⏳ **Reset VMs** (Step 3 above)
5. ⏳ **Full deployment** (Step 4 above)
6. ⏳ **Final verification** (All verification checks)

---

## Root Cause Analysis

**Why did the original bug exist?**

The Ansible `user` module's `append` parameter is confusing:
- `append: yes` → Add to groups (safe)
- `append: no` → **Replace all groups** with specified list (dangerous)

The intention was to remove from libvirt/kvm groups, but the implementation replaced ALL groups with just libvirt/kvm, removing sudo, adm, and everything else.

**How to prevent this in the future?**

1. Always use `append: yes` when adding groups
2. Use `gpasswd -d` to remove from specific groups
3. Never use `user` module with `append: no` for group removal
4. Maintain permanent sudo access via `/etc/sudoers.d/` files
5. Add pre-flight checks before destructive operations
