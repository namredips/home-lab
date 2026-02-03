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
zeus:       52:54:00:df:8d:d4 → 10.220.1.50
athena:     52:54:00:da:d4:dd → 10.220.1.51
apollo:     52:54:00:85:f4:03 → 10.220.1.52
artemis:    52:54:00:82:7a:18 → 10.220.1.53
hermes:     52:54:00:13:11:dd → 10.220.1.54
perseus:    52:54:00:d8:c3:78 → 10.220.1.55
prometheus: 52:54:00:d7:2e:60 → 10.220.1.56
ares:       (TBD - will get MAC when VM is created)
```

## DHCP Server Configuration Examples

### ISC DHCP Server (/etc/dhcp/dhcpd.conf)

```
# Agent VMs
host zeus       { hardware ethernet 52:54:00:df:8d:d4; fixed-address 10.220.1.50; }
host athena     { hardware ethernet 52:54:00:da:d4:dd; fixed-address 10.220.1.51; }
host apollo     { hardware ethernet 52:54:00:85:f4:03; fixed-address 10.220.1.52; }
host artemis    { hardware ethernet 52:54:00:82:7a:18; fixed-address 10.220.1.53; }
host hermes     { hardware ethernet 52:54:00:13:11:dd; fixed-address 10.220.1.54; }
host perseus    { hardware ethernet 52:54:00:d8:c3:78; fixed-address 10.220.1.55; }
host prometheus { hardware ethernet 52:54:00:d7:2e:60; fixed-address 10.220.1.56; }
```

### dnsmasq (/etc/dnsmasq.conf)

```
# Agent VMs
dhcp-host=52:54:00:df:8d:d4,zeus,10.220.1.50
dhcp-host=52:54:00:da:d4:dd,athena,10.220.1.51
dhcp-host=52:54:00:85:f4:03,apollo,10.220.1.52
dhcp-host=52:54:00:82:7a:18,artemis,10.220.1.53
dhcp-host=52:54:00:13:11:dd,hermes,10.220.1.54
dhcp-host=52:54:00:d8:c3:78,perseus,10.220.1.55
dhcp-host=52:54:00:d7:2e:60,prometheus,10.220.1.56
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
for ip in 50 51 52 53 54 55 56 57; do
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
