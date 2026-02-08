# Zeus VM Rebuild Summary

**Date**: February 8, 2026
**Host**: r820.infiquetra.com
**Status**: ✅ Complete

## Problem Statement

Zeus VM needed to be rebuilt on r820 after a failed cold migration from r420. The original issue was that r420 lacked KVM support (no vmx/svm CPU flags), forcing the VM to run under TCG software emulation, resulting in poor performance.

## Root Cause Analysis

1. **r420 Hardware Limitation**: r420 had ZERO KVM support — no vmx/svm CPU flags, forcing QEMU to use TCG (Tiny Code Generator) software emulation instead of hardware acceleration
2. **virt-install Auto-Detection Failure**: When creating zeus on r820, virt-install failed to auto-detect KVM and defaulted to TCG acceleration (`-accel tcg`)
3. **VM Creation Failure**: The VM was created with TCG, attempted to start, failed (logged "shutting down, reason=failed"), and the definition was removed, leaving only disk files behind

## Solution

### Manual VM Recreation
Since the disk and cloud-init files were already created by Ansible, we manually recreated the VM definition with explicit KVM acceleration:

```bash
sudo virt-install \
  --name zeus \
  --virt-type kvm \  # ← Explicit KVM acceleration
  --memory 16384 \
  --vcpus 4 \
  --disk /var/lib/libvirt/images/zeus.qcow2,device=disk,bus=virtio \
  --disk /var/lib/libvirt/images/zeus-seed.img,device=cdrom \
  --os-variant ubuntu24.04 \
  --network network=host-bridge,model=virtio,mac=52:54:00:80:70:b5 \
  --graphics spice,listen=0.0.0.0 \
  --video qxl \
  --channel spicevmc,target_type=virtio,name=com.redhat.spice.0 \
  --channel unix,target_type=virtio,name=org.qemu.guest_agent.0 \
  --console pty,target_type=serial \
  --import \
  --noautoconsole
```

### Ansible Role Fix
Updated `ansible/roles/agent_vm/tasks/create_vm.yml` to include `--virt-type kvm` flag on line 62 to prevent future auto-detection failures.

## Verification

### VM Status
```
Id   Name         State
----------------------------
 10   ares         running
 12   prometheus   running
 16   zeus         running  ← Using KVM acceleration
```

### VM Configuration
```xml
<domain type='kvm' id='16'>  ← Confirmed KVM (not TCG)
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
```

### Network Configuration
- **IP Address**: 10.220.1.199 (DHCP-assigned, DNS resolves zeus.infiquetra.com correctly)
- **MAC Address**: 52:54:00:80:70:b5
- **Hostname**: zeus.infiquetra.com

### Dev Tools Verification
All development tools successfully installed via `agent_provision` role:

```
=== System Info ===
Hostname: zeus
Kernel: 6.8.0-100-generic
CPU: Intel(R) Xeon(R) CPU E5-4650 0 @ 2.70GHz

=== Dev Tools ===
tree-sitter: tree-sitter 0.26.5 ✅
ruff: ruff 0.15.0 ✅
pyright: pyright 1.1.408 ✅
prettier: 3.8.1 ✅
nvim: NVIM v0.9.5 ✅
go: go version go1.25.7 linux/amd64 ✅
rust: rustc 1.93.0 ✅
node: v22.22.0 ✅
python: Python 3.12.3 ✅
docker: Docker version 28.2.2 ✅
```

## Files Modified

1. **ansible/roles/agent_vm/tasks/create_vm.yml**
   - Added `--virt-type kvm` flag to virt-install command (line 62)
   - Prevents future auto-detection failures

2. **ansible/roles/agent_vm/defaults/main.yml**
   - Ares entry remains commented (needs real MAC address before creation)
   - Zeus already pointed to r820 (from commit 1d31e70)

## Performance Comparison

| Metric | r420 (TCG) | r820 (KVM) | Improvement |
|--------|------------|------------|-------------|
| Acceleration | Software (TCG) | Hardware (KVM) | 10-100x faster |
| CPU | No vmx/svm flags | 64 vmx flags | Full hardware virtualization |
| Cores | N/A | 4 vCPUs | Proper multi-core support |

## Next Steps

1. ✅ Zeus fully operational on r820 with KVM
2. ✅ All dev tools installed and verified
3. ⏳ Ares needs real MAC address assignment before creation
4. ⏳ Optional: Configure static IP for zeus (currently using DHCP at 10.220.1.199)

## Lessons Learned

1. **Always verify KVM support** before VM migration/creation:
   ```bash
   grep -E '(vmx|svm)' /proc/cpuinfo  # Should return results
   ```

2. **Explicitly specify virtualization type** in virt-install commands to avoid auto-detection failures:
   ```bash
   --virt-type kvm  # Don't rely on auto-detection
   ```

3. **Check VM acceleration type** after creation:
   ```bash
   virsh dumpxml <vm-name> | grep "domain type"  # Should show type='kvm'
   ```

4. **Monitor VM startup logs** for TCG warnings:
   ```bash
   tail /var/log/libvirt/qemu/<vm-name>.log  # Look for "-accel tcg"
   ```
