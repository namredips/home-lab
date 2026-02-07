# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a home lab infrastructure repository that uses Ansible to automate the deployment and configuration of a MicroK8s cluster across multiple Dell servers. The setup includes storage (ZFS/OpenEBS), networking (external DNS), databases (PostgreSQL, Redis), API gateway (Kong), and GitOps (ArgoCD).

## Architecture

### Infrastructure Components
- **Cluster**: 5 Dell servers (r420, r710, r720xd, r820, r8202) forming a MicroK8s cluster
- **Master Node**: r420.infiquetra.com (10.220.1.7)
- **Storage**: ZFS pools with OpenEBS for persistent volumes
- **Networking**: External DNS integration, Let's Encrypt certificates
- **Databases**: PostgreSQL cluster, Redis cluster
- **API Gateway**: Kong Gateway with PostgreSQL backend
- **GitOps**: ArgoCD for application deployment

### Ansible Structure
- **Main Playbook**: `ansible/k8_cluster.yml` - orchestrates all roles in dependency order
- **Inventory**: `ansible/inventory/hosts.yml` - defines cluster topology
- **Roles**: Each component is a separate Ansible role with setup/reset tasks
- **Variables**: Encrypted with Ansible Vault in `group_vars/all/all.yml`

### Role Dependencies
1. `baseconfig` - base system configuration
2. `zfs_disk_pools` - storage pool setup
3. `microk8s` - Kubernetes cluster installation
4. `k8_accounts` - user accounts and RBAC
5. `openEBS` - persistent volume management
6. `k8_external_dns` - DNS automation
7. `k8_config` - cluster configuration
8. `k8_certs` - TLS certificate management
9. `redis` - Redis cluster deployment
10. `postgresql` - PostgreSQL cluster deployment
11. `kong` - API gateway setup
12. `argoCD` - GitOps deployment

## Common Commands

### Prerequisites
```bash
# Install Python dependencies
cd ansible && uv sync

# Ensure vault password file exists
# ~/.vault_pass.txt should contain the Ansible Vault password
```

### Cluster Management

#### Full Cluster Deployment
```bash
cd ansible
ansible-playbook -i inventory/hosts.yml k8_cluster.yml -u jefcox --vault-password-file ~/.vault_pass.txt
```

#### Individual Role Deployment
```bash
# Use the helper script for single role execution
./ansible/run_ansible_role.sh -r <role_name> -u jefcox

# Examples:
./ansible/run_ansible_role.sh -r microk8s -u jefcox
./ansible/run_ansible_role.sh -r postgresql -u jefcox -v "reset=true"
```

#### Cluster Reset
```bash
cd ansible
ansible-playbook -i inventory/hosts.yml k8_cluster_reset.yml -u jefcox --vault-password-file ~/.vault_pass.txt
```

### Testing and Validation
```bash
# Test storage with sample PVCs
kubectl apply -f test_storage_pod.yml
kubectl apply -f tests/test-zfs-pvc.yml

# Test external DNS
kubectl apply -f tests/test-external-dns-unifi.yml

# Test certificate issuer
kubectl apply -f tests/test-clusterissuer-letsencrypt-lab.yml
```

### Host Preparation
```bash
# Run on new hosts before joining cluster
./pre_configure.sh
```

## Development Notes

### Ansible Vault
- Sensitive variables are encrypted in `ansible/inventory/group_vars/all/all.yml`
- Vault password should be in `~/.vault_pass.txt`
- Use `ansible-vault edit` to modify encrypted variables

### Adding New Roles
- Follow the existing role structure with `tasks/main.yml`, `tasks/setup.yml`, `tasks/reset.yml`
- Add role to `k8_cluster.yml` in proper dependency order
- Include default variables in `defaults/main.yml`
- Add corresponding reset tasks to `k8_cluster_reset.yml`

### Host Variables
- Individual host configurations in `ansible/inventory/host_vars/`
- Network interfaces and IPs defined per host
- All hosts use `eno1` interface for cluster communication

### MicroK8s Specifics
- Cluster uses MicroK8s instead of standard Kubernetes
- Configuration files and kubectl access handled by `microk8s` role
- Addons managed through MicroK8s addon system