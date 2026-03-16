#!/bin/bash
# ups-shutdown.sh — Gracefully stop all running VMs on this host before poweroff
# Called by NUT upsmon (master) when battery hits the low threshold.
# Slaves receive the FSD signal and run their own "shutdown -h now" independently.

set -euo pipefail

logger -t ups-shutdown "UPS battery critical — starting graceful shutdown"

# Get all running VMIDs on this Proxmox host
RUNNING_VMS=$(qm list 2>/dev/null | awk 'NR>1 && $3=="running" {print $1}' || true)

if [ -n "$RUNNING_VMS" ]; then
    logger -t ups-shutdown "Sending shutdown to VMs: $RUNNING_VMS"
    for VMID in $RUNNING_VMS; do
        qm shutdown "$VMID" --timeout 60 &
    done

    # Wait up to 90 seconds for all VMs to stop
    WAITED=0
    while [ "$WAITED" -lt 90 ]; do
        STILL_RUNNING=$(qm list 2>/dev/null | awk 'NR>1 && $3=="running" {print $1}' || true)
        [ -z "$STILL_RUNNING" ] && break
        sleep 5
        WAITED=$((WAITED + 5))
    done

    STILL_RUNNING=$(qm list 2>/dev/null | awk 'NR>1 && $3=="running" {print $1}' || true)
    if [ -n "$STILL_RUNNING" ]; then
        logger -t ups-shutdown "WARNING: VMs still running after timeout: $STILL_RUNNING — forcing host shutdown"
    else
        logger -t ups-shutdown "All VMs stopped cleanly"
    fi
else
    logger -t ups-shutdown "No running VMs found"
fi

logger -t ups-shutdown "Initiating host shutdown"
/sbin/shutdown -h now "NUT: UPS battery critical"
