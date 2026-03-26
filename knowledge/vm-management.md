# VM Management Runbook

## Creating a New VM

### Via Ansible (recommended)

Add the VM definition to `ansible/roles/proxmox_vm/defaults/main.yml` under the appropriate group (`agent_vms` or `service_vms`), then run:

```bash
ansible-playbook -i inventory/hosts.yml proxmox_cluster.yml \
  --tags proxmox_vm --vault-password-file ~/.vault_pass.txt
```

### Via Proxmox CLI (quick/manual)

```bash
# Clone from template (on any PVE host)
qm clone 9000 <VMID> --name <hostname> --full --storage ceph-fast

# Configure resources
qm set <VMID> --cores 8 --memory 8192

# Set cloud-init
qm set <VMID> --ciuser agent --sshkeys /root/.ssh/authorized_keys \
  --ipconfig0 ip=10.220.1.XX/24,gw=10.220.1.1 \
  --nameserver 10.220.1.1 --searchdomain infiquetra.com

# Start
qm start <VMID>
```

## Stopping and Starting VMs

```bash
# On the hosting PVE node
qm stop <VMID>
qm start <VMID>
qm reboot <VMID>

# List VMs on this node
qm list

# Status of specific VM
qm status <VMID>
```

## VM Snapshots

```bash
# Create snapshot (qemu-guest-agent must be running for live snapshots)
qm snapshot <VMID> pre-migration --description "Before Hermes migration"

# List snapshots
qm listsnapshot <VMID>

# Rollback to snapshot
qm rollback <VMID> pre-migration
```

## Migrating a VM Between Hosts

```bash
# Online migration (VM stays running)
qm migrate <VMID> <target-node> --online --with-local-disks

# Offline migration
qm migrate <VMID> <target-node>
```

## Destroying a VM

```bash
# Must stop before destroy
qm stop <VMID>
qm destroy <VMID> --purge
```

## Monitoring VMs

```bash
# CPU/RAM across cluster (run on any PVE host)
pvesh get /cluster/resources --type vm

# Disk usage
df -h  # inside VM

# Check qemu-guest-agent connectivity
qm agent <VMID> ping
```

## IP Assignments

| Range | Use |
|-------|-----|
| 10.220.1.1 | Gateway (UniFi DM) |
| 10.220.1.2 | Mac mini (control node) |
| 10.220.1.7–.12 | Proxmox hypervisor nodes |
| 10.220.1.17–.22 | iDRAC management interfaces |
| 10.220.1.50–.57 | Agent VMs (zeus–ares) |
| 10.220.1.60–.64 | Service VMs |

Static DHCP reservations managed in UniFi via MongoDB (see MEMORY.md for procedure).
