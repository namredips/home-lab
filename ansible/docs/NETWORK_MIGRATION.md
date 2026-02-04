# Network Configuration Migration

**Date**: 2026-02-03
**Status**: Migrated from systemd-networkd static IPs to NetworkManager with DHCP

## Summary

We pivoted from fighting NetworkManager with complex pre-masking to embracing the standard Ubuntu Desktop networking approach. VMs now use DHCP with static reservations.

## Why We Changed

**Previous Approach (systemd-networkd with static IPs):**
- ❌ Complex configuration fighting Ubuntu Desktop defaults
- ❌ NetworkManager installation broke network connectivity
- ❌ Required pre-masking services before package installation
- ❌ Multiple installation failures
- ❌ High maintenance burden

**New Approach (NetworkManager with DHCP):**
- ✅ Standard Ubuntu Desktop configuration
- ✅ Simple, maintainable setup
- ✅ No fighting with package manager
- ✅ Works with desktop tools and GUI
- ✅ VMs get same IP every time (via DHCP reservation)

## DHCP Reservations Required

Configure these MAC→IP mappings on your DHCP server:

```
zeus:       52:54:00:80:70:b5 → 10.220.1.199
athena:     52:54:00:78:c4:0f → 10.220.1.123
apollo:     52:54:00:64:b0:5e → 10.220.1.153
artemis:    52:54:00:80:1a:26 → 10.220.1.194
hermes:     52:54:00:05:26:d8 → 10.220.1.198
perseus:    52:54:00:58:86:1c → 10.220.1.113
prometheus: 52:54:00:7c:57:d6 → 10.220.1.156
```

## DHCP Server Configuration Examples

### ISC DHCP Server (/etc/dhcp/dhcpd.conf)

```
# Agent VMs
host zeus       { hardware ethernet 52:54:00:80:70:b5; fixed-address 10.220.1.199; }
host athena     { hardware ethernet 52:54:00:78:c4:0f; fixed-address 10.220.1.123; }
host apollo     { hardware ethernet 52:54:00:64:b0:5e; fixed-address 10.220.1.153; }
host artemis    { hardware ethernet 52:54:00:80:1a:26; fixed-address 10.220.1.194; }
host hermes     { hardware ethernet 52:54:00:05:26:d8; fixed-address 10.220.1.198; }
host perseus    { hardware ethernet 52:54:00:58:86:1c; fixed-address 10.220.1.113; }
host prometheus { hardware ethernet 52:54:00:7c:57:d6; fixed-address 10.220.1.156; }
```

### dnsmasq (/etc/dnsmasq.conf)

```
# Agent VMs
dhcp-host=52:54:00:80:70:b5,zeus,10.220.1.199
dhcp-host=52:54:00:78:c4:0f,athena,10.220.1.123
dhcp-host=52:54:00:64:b0:5e,apollo,10.220.1.153
dhcp-host=52:54:00:80:1a:26,artemis,10.220.1.194
dhcp-host=52:54:00:05:26:d8,hermes,10.220.1.198
dhcp-host=52:54:00:58:86:1c,perseus,10.220.1.113
dhcp-host=52:54:00:7c:57:d6,prometheus,10.220.1.156
```

## Migration Steps

### 1. Configure DHCP Reservations
Add the MAC→IP mappings to your DHCP server using one of the formats above.

### 2. Recreate VMs (Recommended)
This gives them fresh cloud-init with the new DHCP configuration:

```bash
cd ~/workspace/temp/home-lab/ansible

# Recreate all VMs
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=agent_vm
```

### 3. Install Desktop Environment
Using the simplified approach (no NetworkManager fighting):

```bash
# Install desktops on all VMs
uv run ansible-playbook openclaw_cluster.yml \
  --vault-password-file ~/.vault_pass.txt \
  --tags=agent_desktop
```

## Verification

After migration, verify each VM:

```bash
# Check IP and NetworkManager status
for ip in 199 123 153 194 198 113 156; do
  echo "=== 10.220.1.$ip ==="
  ssh agent@10.220.1.$ip "hostname && ip addr show | grep '10.220.1' && systemctl status NetworkManager | grep Active"
done
```

Expected output:
- VM has correct IP address (from DHCP reservation)
- NetworkManager is active and running
- No systemd-networkd configuration

## Files Changed

- `roles/agent_vm/templates/vm-network-config.yml.j2`: Changed to DHCP with NetworkManager renderer
- `roles/agent_desktop/tasks/main.yml`: Removed all NetworkManager masking/pre-masking logic

## Rollback (if needed)

If you need to revert to the old approach:

```bash
git revert ae65a42  # Revert "pivot to NetworkManager with DHCP"
```

Then recreate VMs with the old static IP configuration.
