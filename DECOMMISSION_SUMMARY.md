# Kubernetes Cluster Decommissioning Summary

**Date**: 2026-01-30
**Status**: ✅ **COMPLETE**

## Cluster Teardown Results

The MicroK8s Kubernetes cluster has been successfully decommissioned across all 5 Dell servers.

### Server Status (Post-Teardown)

| Server | IP | MicroK8s | ZFS Pools | SSH | Storage Available |
|--------|-----|----------|-----------|-----|-------------------|
| r420.infiquetra.com | 10.220.1.7 | ✅ Removed | ✅ Destroyed | ✅ Active | 836 GB |
| r710.infiquetra.com | 10.220.1.9 | ✅ Removed | ✅ Destroyed | ✅ Active | 852 GB |
| r8202.infiquetra.com | 10.220.1.8 | ✅ Removed | ✅ Destroyed | ✅ Active | 851 GB |
| r720xd.infiquetra.com | 10.220.1.10 | ✅ Removed | ✅ Destroyed | ✅ Active | 852 GB |
| r820.infiquetra.com | 10.220.1.11 | ✅ Removed | ✅ Destroyed | ✅ Active | 851 GB |

## What Was Removed

### Services (in order)
1. ✅ **ArgoCD** - GitOps platform removed
2. ✅ **PostgreSQL** - Database cluster removed
3. ✅ **Redis** - 12-node cache cluster removed
4. ✅ **External-DNS** - DNS automation removed
5. ✅ **OpenEBS** - Storage provisioner removed
6. ✅ **MicroK8s** - Kubernetes orchestration removed from all nodes
7. ✅ **ZFS Pools** - All storage pools destroyed
8. ✅ **Base Configuration** - Cluster-specific configurations removed

### Infrastructure Components Removed
- MicroK8s cluster (1 master + 4 workers)
- All Kubernetes namespaces and resources
- OpenEBS persistent volume management
- ZFS storage pools on all nodes
- MetalLB IP allocations (10.220.1.201-245 range)
- Kong API Gateway
- cert-manager and TLS certificates
- Helm charts and repositories

## Current Server State

Each server now has:
- ✅ Base Ubuntu/Debian OS (preserved)
- ✅ Network configuration intact
- ✅ SSH access functional
- ✅ Clean filesystem (~850 GB available)
- ✅ No Kubernetes components
- ✅ No ZFS pools
- ✅ Ready for standalone workloads

### System Resources (Example from r710)
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1    916G   18G  852G   3% /
```

## Suggested Server Assignments

| Server | Recommended Use | Notes |
|--------|-----------------|-------|
| **r420** (10.220.1.7) | Lightweight services | Former master node |
| **r710** (10.220.1.9) | General purpose compute | Standard worker |
| **r8202** (10.220.1.8) | General purpose compute | Standard worker |
| **r720xd** (10.220.1.10) | Storage-heavy workloads | Has extensive disk bays |
| **r820** (10.220.1.11) | Compute-heavy workloads | High CPU capacity |

## Domain & DNS

- **Domain**: `infiquetra.com` - Still registered, available for non-K8s use
- **AWS Route53**: Zone Z1O01CFQNOUU7X - May contain stale `_acme-challenge` records (optional cleanup)
- **UniFi Controller**: 10.220.1.1 - May have stale DNS records (optional cleanup)
- **Available IP Range**: 10.220.1.201-245 (formerly MetalLB pool)

## Manual Cleanup (Optional)

### 1. UniFi Controller DNS Records
Login to UniFi at `10.220.1.1` and remove any stale `*.infiquetra.com` A records created by external-dns.

### 2. AWS Route53 TXT Records
Check for and remove `_acme-challenge.*.infiquetra.com` TXT records used for Let's Encrypt validation.

### 3. Repository Archival
Consider archiving or deleting this repository (`/Users/jefcox/workspace/infiquetra/home-lab`) if no longer needed.

## Verification Commands

To verify the current state of any server:

```bash
# SSH to a server
ssh jefcox@<server-ip>

# Verify MicroK8s is gone
which microk8s  # Should return nothing

# Verify ZFS pools are removed
zpool list  # Should show "no pools available"

# Check system resources
df -h
free -h
uptime

# Verify SSH is working
systemctl status sshd
```

## Rollback (If Needed)

To rebuild the Kubernetes cluster, the original deployment playbook is still available:

```bash
cd /Users/jefcox/workspace/infiquetra/home-lab/ansible
ansible-playbook -i inventory/hosts.yml k8_cluster.yml \
  -u jefcox \
  --vault-password-file ~/.vault_pass.txt
```

## Next Steps

1. **Decide on new workloads** for each server
2. **Clean up DNS records** in UniFi and Route53 (optional)
3. **Archive this repository** if cluster won't be rebuilt
4. **Document new server assignments** when workloads are deployed

---

**Decommissioned by**: Claude Code
**Teardown playbook**: `ansible/k8_cluster_reset.yml`
**All servers verified**: 2026-01-30
