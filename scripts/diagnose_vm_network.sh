#!/bin/bash
# VM Network Diagnostics Script
# Run this on the hypervisor (e.g., r420.infiquetra.com)
# Usage: ./diagnose_vm_network.sh <vm-name>

VM_NAME="${1:-zeus}"
OUTPUT_FILE="/tmp/vm-network-diag-${VM_NAME}.txt"

echo "=== VM Network Diagnostics for ${VM_NAME} ===" | tee "$OUTPUT_FILE"
echo "Timestamp: $(date)" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check VM status
echo "--- VM Status ---" | tee -a "$OUTPUT_FILE"
sudo virsh domstate "$VM_NAME" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check attached devices
echo "--- Attached Devices (looking for seed ISO) ---" | tee -a "$OUTPUT_FILE"
sudo virsh domblklist "$VM_NAME" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check network configuration
echo "--- VM Network Configuration ---" | tee -a "$OUTPUT_FILE"
sudo virsh domiflist "$VM_NAME" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Run commands inside VM via console (requires virsh-guest-agent or qemu-guest-agent)
echo "--- Attempting to gather info via guest agent ---" | tee -a "$OUTPUT_FILE"
if sudo virsh qemu-agent-command "$VM_NAME" '{"execute":"guest-ping"}' 2>/dev/null; then
    echo "Guest agent available" | tee -a "$OUTPUT_FILE"
    sudo virsh qemu-agent-command "$VM_NAME" '{"execute":"guest-network-get-interfaces"}' 2>/dev/null | tee -a "$OUTPUT_FILE"
else
    echo "Guest agent not available - manual console access needed" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Check libvirt network configuration
echo "--- Libvirt host-bridge Network Info ---" | tee -a "$OUTPUT_FILE"
sudo virsh net-info host-bridge 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "host-bridge network not found" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

echo "--- Bridge Configuration on Host ---" | tee -a "$OUTPUT_FILE"
ip addr show br0 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "br0 not found" | tee -a "$OUTPUT_FILE"
brctl show 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "brctl not available" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# Check if seed ISO is readable
echo "--- Seed ISO Content Check ---" | tee -a "$OUTPUT_FILE"
SEED_ISO=$(sudo virsh domblklist "$VM_NAME" | grep -i seed | awk '{print $2}')
if [ -n "$SEED_ISO" ]; then
    echo "Seed ISO path: $SEED_ISO" | tee -a "$OUTPUT_FILE"
    if [ -f "$SEED_ISO" ]; then
        echo "File exists, checking content:" | tee -a "$OUTPUT_FILE"
        sudo isoinfo -l -i "$SEED_ISO" 2>/dev/null | head -20 | tee -a "$OUTPUT_FILE" || echo "isoinfo not available" | tee -a "$OUTPUT_FILE"
    else
        echo "Seed ISO file not found!" | tee -a "$OUTPUT_FILE"
    fi
else
    echo "No seed ISO found attached to VM" | tee -a "$OUTPUT_FILE"
fi
echo "" | tee -a "$OUTPUT_FILE"

echo "=== Diagnostics complete ===" | tee -a "$OUTPUT_FILE"
echo "Output saved to: $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Review the output above"
echo "2. If you need console access, run: sudo virsh console $VM_NAME"
echo "   (Login: agent / openclaw, Exit: Ctrl+])"
echo "3. Once at console, run these commands:"
echo "   ip addr show"
echo "   cloud-init status --long"
echo "   cat /etc/netplan/*.yaml"
echo "   sudo cat /var/log/cloud-init.log | tail -50"
