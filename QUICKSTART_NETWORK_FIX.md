# VM Network Fix - Quick Start Guide

## TL;DR

Your VMs boot but have no network because seed ISOs weren't regenerated after template changes. Here's how to fix it:

---

## Quick Fix (2-3 minutes)

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Regenerate seed ISOs and reboot VMs
uv run ansible-playbook regenerate_seed_isos.yml --vault-password-file ~/.vault_pass.txt

# Test (automatically done by playbook, but you can verify)
ping 10.220.1.50  # Zeus
ping 10.220.1.51  # Apollo
# etc.
```

---

## Full Recreate (if quick fix doesn't work)

```bash
cd /Users/jefcox/workspace/temp/home-lab/ansible

# Destroy all VMs
uv run ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Recreate with fixed config
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt --tags=agent_vm

# Wait for cloud-init
sleep 60

# Test all
for ip in {50..57}; do
  echo -n "10.220.1.$ip: "
  ping -c 1 -W 2 10.220.1.$ip >/dev/null 2>&1 && echo "✓" || echo "✗"
done
```

---

## What Was Changed

1. **Fixed seed ISO regeneration** - No longer skips if file exists
2. **Improved network config** - Better interface matching and explicit DHCP disable
3. **Fixed DNS servers** - Now uses 10.220.1.200 (local) and 1.1.1.1 (Cloudflare)

---

## Diagnostics (Optional)

```bash
# Run diagnostic script on hypervisor
scp scripts/diagnose_vm_network.sh jefcox@r420.infiquetra.com:/tmp/
ssh jefcox@r420.infiquetra.com "/tmp/diagnose_vm_network.sh zeus"

# Or manual console access
ssh jefcox@r420.infiquetra.com
sudo virsh console zeus
# Login: agent / openclaw
# Check: ip addr show, cloud-init status
# Exit: Ctrl+]
```

---

## After Network is Working

```bash
# Commit changes
git add ansible/roles/agent_vm ansible/regenerate_seed_isos.yml ansible/tasks/
git commit -m "fix(agent_vm): fix cloud-init network config application"

# Continue to desktop installation
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=agent_desktop
```

---

## Detailed Documentation

- **Implementation Summary**: `docs/IMPLEMENTATION_SUMMARY.md`
- **Root Cause Analysis**: `docs/NETWORK_FIX_ANALYSIS.md`
- **Diagnostic Guide**: `docs/VM_NETWORK_DIAGNOSTICS.md`
