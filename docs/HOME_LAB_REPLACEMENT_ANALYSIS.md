# Home Lab Replacement Analysis
**Date**: February 2026
**Status**: Planning
**Goal**: Replace 5 aging Dell PowerEdge servers (2009–2012 era) with modern, energy-efficient hardware running Proxmox VE

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Hardware Inventory](#current-hardware-inventory)
3. [Pain Points](#pain-points)
4. [Power & Cost Analysis — Current Setup](#power--cost-analysis--current-setup)
5. [Reusable Components](#reusable-components)
6. [Replacement Options](#replacement-options)
   - [Option A — Beelink SER8 Cluster](#option-a--beelink-ser8-cluster-budget-mini-pc)
   - [Option B — Beelink SER9 Max Cluster](#option-b--beelink-ser9-max-cluster-10gbe-mini-pc)
   - [Option C — Minisforum MS-01 Cluster](#option-c--minisforum-ms-01-cluster-workstation-mini-pc)
   - [Option D — Minisforum MS-02 Ultra Cluster](#option-d--minisforum-ms-02-ultra-cluster-gpu-ready-workstation)
   - [Option E — Modern 1U Server-Class Machines](#option-e--modern-1u-server-class-machines)
   - [Option F — DIY 2U Rack Build](#option-f--diy-2u-rack-build-custom-desktop-components)
7. [Comparison Tables](#comparison-tables)
8. [Rack Mounting Solutions for Mini PCs](#rack-mounting-solutions-for-mini-pcs)
9. [Power & Cabling in Rack Environments](#power--cabling-in-rack-environments)
10. [Out-of-Band Management — JetKVM](#out-of-band-management--jetkvm)
11. [Proxmox Architecture per Option](#proxmox-architecture-per-option)
12. [Migration Plan](#migration-plan)
13. [Recommendation](#recommendation)

---

## Executive Summary

The current home lab runs 8 AI agent VMs (Mount Olympus / OpenClaw) across 5 Dell PowerEdge servers that are 12–17 years old. These servers collectively consume ~930W at idle (~$1,060/year in electricity), produce significant noise, and have critical limitations including: no KVM hardware virtualization on the r420, no NVMe boot support on older RAID controllers, and decade-old memory controllers that bottleneck performance.

A 3-node cluster of modern mini PCs would match or exceed current compute capacity, reduce idle power draw by ~95% ($50–100/year), eliminate noise, and cost $1,500–$6,000+ depending on configuration. Reselling current hardware (especially the r820 with 384GB RAM) can recover $1,000–$3,000, significantly offsetting the replacement cost.

**Key finding**: The r820 has 384GB of installed RAM — far exceeding the 128GB in documentation. This server alone has significant resale value and is the biggest asset in the current fleet.

---

## Current Hardware Inventory

Data collected via SSH inspection (February 28, 2026). Note: r420 was unreachable via SSH during inspection; its specs are taken from repository documentation.

### Per-Server Breakdown

#### Dell PowerEdge R420 — r420.infiquetra.com (10.220.1.7)
| Attribute | Value |
|-----------|-------|
| Model | Dell PowerEdge R420 (2U) |
| CPU | Intel Xeon Sandy Bridge / Ivy Bridge, ~12–16 vCPUs (SSH unavailable) |
| RAM | 32 GB DDR3 ECC |
| Boot Storage | Unknown |
| Data Storage | 2× SAS drives (sdc, sdd), striped — ~836GB usable |
| Network | 4× 1GbE onboard |
| KVM Support | **None** — vmx/svm flags absent; all VMs ran under software emulation (TCG) |
| VMs | None currently running (virsh list shows empty) |
| Year | ~2012 |

**Status**: Currently idle and providing no value to the VM cluster. The root cause of the Zeus VM relocation.

---

#### Dell PowerEdge R710 — r710.infiquetra.com (10.220.1.9)
| Attribute | Value |
|-----------|-------|
| Model | Dell PowerEdge R710 (2U) |
| CPU | 2× Intel Xeon X5570 @ 2.93GHz — 4 cores/socket, HT = **16 vCPUs** |
| RAM | **72 GB** DDR3 ECC 1333MT/s (verified via SSH `free`) |
| Boot Storage | WD Black SN750 SE 1TB NVMe (nvme0n1) |
| Data Storage | 5× 1.82TB SAS + 1× 931GB SAS (PERC 6/i RAID controller) |
| Network | 4× 1GbE onboard (eno1–eno4) |
| KVM Support | Yes (VT-x) |
| VMs | Apollo (16GB), Artemis (16GB) — confirmed via virsh |
| Year | ~2009 (Nehalem-era Xeons) |

---

#### Dell PowerEdge R820 (2-socket) — r8202.infiquetra.com (10.220.1.8)
| Attribute | Value |
|-----------|-------|
| Model | Dell PowerEdge R820 (2U, 2 sockets populated) |
| CPU | 2× Intel Xeon E5-4650 @ 2.70GHz — 8 cores/socket, HT = **32 vCPUs** |
| RAM | **52 GB** DDR3 ECC 1333MT/s (verified via SSH `free`) |
| Boot Storage | WD Black SN750 SE 1TB NVMe (nvme0n1) |
| Data Storage | 1× 1.1TB SAS (PERC H710) |
| Network | 4× 1GbE onboard; 2× macvtap bridges active for VMs |
| KVM Support | Yes (VT-x) |
| VMs | Artemis, Hermes — confirmed active via macvtap bridges |
| Year | ~2012 |

---

#### Dell PowerEdge R720xd — r720xd.infiquetra.com (10.220.1.10)
| Attribute | Value |
|-----------|-------|
| Model | Dell PowerEdge R720xd (2U, 12-bay LFF) |
| CPU | 2× Intel Xeon E5-2620 @ 2.00GHz — 6 cores/socket, HT = **24 vCPUs** |
| RAM | **96 GB** DDR3 ECC 1066MT/s (verified via SSH `free`) |
| Boot Storage | WD Black SN750 SE 1TB NVMe (nvme0n1) |
| Data Storage | 4× 2.73TB + 8× 1.82TB SAS (PERC H710), 12 drives total = ~25TB raw |
| Network | 4× 1GbE onboard |
| KVM Support | Yes (VT-x) |
| VMs | Perseus (16GB) |
| Services | Mattermost (Docker Compose) — PostgreSQL 16 + Mattermost 11.3 |
| Disk Usage | /dev/nvme0n1 = 916GB, 54GB used (7%) |
| Year | ~2012 |

This is the storage-rich server. Its 12 SAS bays hold the most drives and represent the largest reusable storage asset.

---

#### Dell PowerEdge R820 (4-socket) — r820.infiquetra.com (10.220.1.11)
| Attribute | Value |
|-----------|-------|
| Model | Dell PowerEdge R820 (4U, 4 sockets) |
| CPU | 4× Intel Xeon E5-4650 @ 2.70GHz — 8 cores/socket, HT = **64 vCPUs** |
| RAM | **384 GB** DDR3 ECC 1066MT/s (verified via SSH: `Mem: 377Gi total`) |
| Boot Storage | WD Black SN750 SE 1TB NVMe (nvme0n1) |
| Data Storage | 9× 931GB + 1× 2.18TB SAS (PERC H710P) |
| Network | 4× 1GbE onboard |
| KVM Support | Yes (VT-x) |
| VMs | Zeus, Prometheus, Ares (confirmed; ~48GB RAM committed) |
| Year | ~2012 |

**Note**: The documentation says 128GB RAM but the actual SSH measurement shows 384GB. This server has been upgraded with significant RAM and is the most valuable piece of hardware for resale.

---

### Cluster Totals (Actual, from SSH)

| Metric | Value | Notes |
|--------|-------|-------|
| Total Servers | 5 | All Dell PowerEdge |
| Total vCPUs | ~152 | r420 estimated; r710:16, r8202:32, r720xd:24, r820:64 |
| Total RAM | ~636 GB | SSH-verified; docs significantly understate actual |
| Total NVMe | 5× 1TB | WD Black SN750 SE, one per server |
| Total SAS | ~38TB raw | r720xd: 25TB, r820: ~10TB, r710: ~10TB, r8202: ~1TB |
| Total Network | 20× 1GbE | 4 ports per server, only eno1 used per node |
| Active VMs | 8 | Apollo, Athena, Artemis, Hermes, Perseus, Zeus, Prometheus, Ares |
| Active Services | 1 | Mattermost + PostgreSQL on r720xd |

### VM Workload Summary

| VM | Host | vCPU | RAM | Role |
|----|------|------|-----|------|
| Zeus | r820 | 4 | 16GB | PM, Orchestration |
| Athena | r710 | 4 | 8GB | Senior Dev (Architecture) |
| Apollo | r710 | 4 | 16GB | Developer (Code Quality) |
| Artemis | r8202 | 4 | 16GB | Developer (Testing) |
| Hermes | r8202 | 4 | 16GB | Developer (Integrations) |
| Perseus | r720xd | 4 | 16GB | Developer (Complex Problems) |
| Prometheus | r820 | 4 | 16GB | Developer (Innovation) |
| Ares | r820 | 4 | 16GB | Developer (Performance) |

**Total committed**: 32 vCPUs, 120GB RAM

---

## Pain Points

1. **r420 has no hardware virtualization**: The primary master node cannot run VMs efficiently. All VMs that were placed on it ran via software emulation (TCG), which is 5–10× slower than hardware-accelerated KVM. Zeus had to be migrated off it for this reason.

2. **No NVMe boot on PERC RAID controllers**: The PERC 6/i and H710 controllers don't support booting from NVMe. Each server had to have a WD Black SN750 NVMe installed separately (USB or PCIe adapter) to bypass this limitation.

3. **Power consumption**: ~930W idle for 5 servers that are running 8 VMs with <30% CPU utilization. At $0.13/kWh this costs ~$1,060/year.

4. **Noise**: Enterprise rack servers run fans at 5,000–12,000 RPM. These are loud enough to require a dedicated room or serious soundproofing.

5. **Form factor**: 5× 2U–4U servers occupy 10–18U of rack space. Modern mini PCs can host the same workload in 3–5 units that fit on a shelf.

6. **Ancient memory controllers**: DDR3 at 1066–1333MHz severely bottlenecks AI workloads that are memory-bandwidth sensitive. Modern DDR5 is 3–4× faster in bandwidth.

7. **No PCIe 4.0/5.0**: Future GPU passthrough for local LLM inference (Ollama) requires modern PCIe lanes. The 2012-era servers have PCIe 2.0/3.0 with limited bandwidth.

8. **Limited I/O for Proxmox clustering**: Only 1GbE available for cluster interconnect. Live VM migration at 1GbE is slow (~30-90 seconds for a 16GB RAM VM). Ceph distributed storage requires 10GbE minimum.

---

## Power & Cost Analysis — Current Setup

### Estimated Idle Power Draw

| Server | Idle Draw | Basis |
|--------|-----------|-------|
| r420 | ~60W | Community-reported R420 idle (40–80W typical) |
| r710 | ~150W | Community-measured; Xeon X5570 is 95W TDP × 2, plus memory/drives |
| r8202 | ~220W | R820 with 2× E5-4650 (130W TDP) plus memory + RAID drives |
| r720xd | ~150W | R720 ~80W + 12 SAS drives @ ~5–8W each |
| r820 | ~350W | 4× E5-4650 (130W TDP × 4) + 48 DIMM slots populated + 10 drives |
| **Total** | **~930W** | |

### Annual Electricity Cost

```
930W × 8,760 hours × $0.13/kWh = ~$1,060/year
```

At typical home electric rates, the current setup costs over **$1,000/year** in electricity alone, before any cooling overhead.

### Noise Level

All 5 servers run enterprise server fans that target specific CFM requirements. At idle:
- R710: ~55 dB (comparable to a dishwasher)
- R820: ~60–65 dB (comparable to a vacuum cleaner at distance)

These are not compatible with living spaces or home offices without soundproofing.

---

## Reusable Components

### High Value — Keep and Reuse

| Component | Quantity | Notes |
|-----------|----------|-------|
| WD Black SN750 SE 1TB NVMe (M.2 2280) | 5 | Excellent drives (~2021–2022 vintage); fit directly in mini PC M.2 slots |

The NVMe drives are the most directly reusable component. Each WD Black SN750 SE is an M.2 2280 PCIe Gen3 NVMe drive. Every mini PC option below has at least one M.2 2280 slot, so these slot directly in and save ~$70–90 each.

**Value**: 5 × ~$70 market value = ~$350 in reusable storage if kept, or sell them.

### Moderate Value — Possible Reuse with Adapter

| Component | Quantity | Notes |
|-----------|----------|-------|
| SAS hard drives (r720xd) | 12 drives (25TB raw) | Need SAS HBA to use; could connect to a TrueNAS VM or NAS device. Older SAS, not fast, but good for archive storage |
| SAS hard drives (r820, r710) | ~10 drives | Similar; older SAS 2.5" and 3.5" |

To reuse the SAS drives, you'd need an HBA card (like a Broadcom 9300-8i, ~$50 used) and an external SAS enclosure or a small NAS chassis. This is optional — the drives hold bulk storage that could be replaced with a consumer NAS.

### Low / No Value — Sell or Discard

| Component | Notes |
|-----------|-------|
| DDR3 ECC RAM | Not compatible with any modern system; DDR3 market saturated |
| PERC H710/H710P RAID cards | Dell-proprietary firmware; not reusable in non-Dell hardware |
| Server chassis / power supplies | Heavy, specialized for rack use; no value outside another Dell chassis |
| Dual-port 1GbE onboard NICs | Already at network limit; not worth extracting |

### Resale Value of Current Hardware

This is the biggest opportunity to offset upgrade costs:

| Server | Estimated Resale (eBay, Feb 2026) | Notes |
|--------|-----------------------------------|-------|
| r420 | $50–150 | No KVM support reduces value; sell with drives |
| r710 | $150–350 | X5570s are still in demand; sell with drives |
| r8202 (R820, 2-socket) | $200–500 | E5-4650s with 52GB RAM |
| r720xd | $300–700 | 12 drive bays + 96GB RAM; storage servers hold value |
| r820 (4-socket, 384GB) | **$800–2,000** | 4× E5-4650, 384GB RAM is rare; high demand on eBay |

**Potential resale total**: $1,500–$3,700

The 4-socket r820 with 384GB of RAM is the standout. This much DDR3 ECC RAM is hard to find; homelab buyers and small business owners pay a premium. Listing it for $1,200–1,500 with RAM is realistic.

---

## Replacement Options

All options target Proxmox VE 8.x as the hypervisor, replace all 5 servers, and are designed to run at least 8 VMs (the current load) with headroom for growth. Each option includes 3× JetKVM ($69 each, $207 total) for remote KVM access — see [Out-of-Band Management](#out-of-band-management--jetkvm).

---

### Option A — Beelink SER8 Cluster (Budget Mini PC)

**Configuration**: 3-node cluster of Beelink SER8 mini PCs

The SER8 is the most affordable path to a modern cluster. Good per-core performance, DDR5, and near-silent operation. Networking is 2.5GbE — capable for VM traffic but insufficient for Ceph distributed storage.

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Beelink SER8 (AMD Ryzen 7 8745HS, 32GB DDR5-5600, 1TB NVMe) | 3 | $360 | $1,080 |
| Crucial 64GB DDR5-5600 SODIMM kit (2×32GB, replaces stock) | 3 | $110 | $330 |
| 8-port 2.5GbE switch (TRENDnet TEG-S380) | 1 | $60 | $60 |
| CAT6 patch cables (3-pack) | 1 | $15 | $15 |
| Small shelf or drawer for mini PCs | 1 | $30 | $30 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$1,722** |

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | AMD Ryzen 7 8745HS (8C/16T, up to 4.9GHz, Zen 4) |
| Total cores | 24 cores / 48 threads |
| RAM per node | 64GB DDR5-5600 |
| Total RAM | 192GB |
| Storage per node | 1TB boot NVMe + optional 2nd NVMe |
| Network | 2.5GbE per node |
| PCIe slot | None |
| Idle power per node | ~15W |
| Total idle power | ~45W |
| Noise | Near-silent (<30 dB at idle) |
| Form factor | Mini PC (~140mm × 126mm × 60mm) |
| Rack format | 1U shelf (2-4 units) or racknex NUC-style tray |
| Power cabling | External DC brick → NEMA 5-15 PDU strip |

**Annual electricity**: 45W × 8,760h × $0.13 = ~$51/year
**Savings vs current**: ~$1,009/year

**Limitations**:
- 2.5GbE networking means Ceph distributed storage is not practical (needs 10GbE)
- Live VM migration is slower (~10–30s for a 16GB VM)
- No PCIe slot for GPU passthrough
- RAM maxes at 64GB per node (128GB kits exist but are expensive and less tested)

---

### Option B — Beelink SER9 Max Cluster (10GbE Mini PC)

**Configuration**: 3-node cluster of Beelink SER9 Max mini PCs with 10GbE

The SER9 Max adds native 10GbE networking, which unlocks Proxmox Ceph distributed storage and fast live migration. This is the sweet spot for a capable home lab cluster.

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Beelink SER9 Max (AMD Ryzen 7 H255, 32GB DDR5, 1TB NVMe, 10GbE) | 3 | $670 | $2,010 |
| Crucial 64GB DDR5-5600 SODIMM kit (2×32GB, upgrade to 64GB) | 3 | $110 | $330 |
| Samsung 990 Pro 2TB NVMe (2nd M.2 slot, VM storage) | 3 | $110 | $330 |
| 8-port 10GbE switch (Mikrotik CRS309-1G-8S+IN) | 1 | $290 | $290 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| CAT6 patch cables | 1 | $15 | $15 |
| Small shelf or 1U tray | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$3,262** |

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | AMD Ryzen 7 H255 (8C/16T, up to 4.9GHz, Zen 5) |
| Total cores | 24 cores / 48 threads |
| RAM per node | 64GB DDR5-5600 |
| Total RAM | 192GB |
| Storage per node | 1TB boot + 2TB VM NVMe |
| Network | 10GbE per node (SFP+) + 2.5GbE management |
| PCIe slot | None |
| Idle power per node | ~25W |
| Total idle power | ~75W |
| Noise | Near-silent (<30 dB) |
| Form factor | Mini PC |
| Rack format | 1U shelf or racknex tray |
| Power cabling | External DC brick → NEMA 5-15 PDU strip |

**Annual electricity**: 75W × 8,760h × $0.13 = ~$85/year
**Savings vs current**: ~$975/year

**Advantages over Option A**:
- 10GbE enables Proxmox Ceph — distributed storage across all 3 nodes
- Live VM migration in seconds (not minutes)
- Zen 5 architecture is the latest AMD laptop silicon

**Limitations**:
- Still no PCIe slot for GPU passthrough
- 64GB per node limit
- Ryzen H255 is a laptop chip; sustained all-core loads throttle slightly vs desktop

---

### Option C — Minisforum MS-01 Cluster (Workstation Mini PC)

**Configuration**: 3-node cluster of Minisforum MS-01 with dual 10GbE SFP+, plus a shared NAS for VM storage

The MS-01 is purpose-built for home lab cluster use. It has dual 10GbE SFP+ ports (ideal for Ceph + management on separate networks), a PCIe 4.0 x4 slot (limited GPU passthrough), and 3 NVMe slots.

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-01 (i9-13900H, 64GB DDR5, 2TB NVMe) | 3 | $950 | $2,850 |
| Crucial 32GB DDR5 SODIMM (upgrade 3rd slot if supported) | 3 | $55 | $165 |
| Samsung 990 Pro 2TB NVMe (2nd M.2 slot) | 3 | $110 | $330 |
| 8-port 10GbE switch (Mikrotik CRS309-1G-8S+IN) | 1 | $290 | $290 |
| SFP+ DAC cables (1m, 3-pack) | 1 | $40 | $40 |
| Synology DS423+ NAS (4-bay, for shared VM storage) | 1 | $450 | $450 |
| 4× WD Red Plus 4TB NAS HDD | 4 | $90 | $360 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$4,692** |

> **Alternative to NAS**: Use Ceph directly on the 3 MS-01 nodes (no separate NAS). Ceph with 3× 2TB NVMe = 2TB usable (3-way replicated). This works well with dual 10GbE — one port for Ceph replication, one for VM traffic.

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Intel Core i9-13900H (6P+8E = 14 cores, 20 threads, up to 5.4GHz) |
| Total cores | 42 cores / 60 threads (P-cores only count) |
| RAM per node | 64GB DDR5-5200 (96GB possible) |
| Total RAM | 192GB–288GB |
| Boot storage | 2TB NVMe per node (6TB total) |
| VM storage | Ceph on local NVMe, or Synology NAS (NFS) |
| Network | 2× 10GbE SFP+ per node + 2× 2.5GbE RJ45 |
| PCIe slot | 1× PCIe 4.0 x4 slot per node (single-slot low-profile GPU only) |
| Idle power per node | ~30W |
| Total idle power | ~90W |
| Noise | Very quiet (<30 dB) |
| Form factor | Mini PC (209mm × 195mm × 43mm) |
| Rack format | racknex UM-MIN-201 (2× per 1.33U) or thingsINrack 2U dual mount |
| Power cabling | External DC brick → NEMA 5-15 PDU strip or velcro'd in racknex tray |

**Annual electricity**: 90W × 8,760h × $0.13 = ~$102/year
**Savings vs current**: ~$958/year

**Advantages**:
- Dual 10GbE for dedicated Ceph + VM traffic lanes
- PCIe 4.0 slot: add a single-slot GPU for local LLM inference (RTX 3050 / A2000 12GB)
- 3 NVMe slots (one included + two more M.2)
- Intel vPro platform (AMT remote management — headless access even if OS crashes)
- Better sustained performance than mobile Ryzen chips under heavy load

**Limitations**:
- PCIe slot is x4 electrically, not x16 — limits GPU to single-slot, low-profile cards
- i9-13900H is 13th gen Intel — newer Intel Core Ultra is faster
- External power brick still requires rack PDU adapter approach

---

### Option D — Minisforum MS-02 Ultra Cluster (GPU-Ready Workstation)

**Configuration**: 3-node cluster of Minisforum MS-02 Ultra — the only mini PC option with a full PCIe 5.0 x16 slot, 256GB ECC RAM support, and an internal IEC C14 PSU.

This is the right choice if you want GPU passthrough for local LLM inference (Ollama / llama.cpp), need more than 64GB RAM per node, or want rack-native power cabling without adapter kits.

#### Hardware Specs

| Attribute | Value |
|-----------|-------|
| CPU | Intel Core Ultra 9 285HX (24C/24T, up to 5.5GHz, Arrow Lake-HX) |
| RAM | 4× DDR5 SODIMM slots, up to **256GB ECC DDR5** |
| Storage | 4× M.2 NVMe slots (1× PCIe 5.0, others PCIe 4.0) |
| GPU slot | **PCIe 5.0 x16** — supports dual-slot low-profile GPU (RTX 4060 Ti LP, RTX 4070 LP, etc.) |
| Network | 2× 25GbE SFP28 + 1× 10GbE + 1× 2.5GbE (Intel i226-LM) |
| PSU | **Internal 350W AC** with **IEC C14 inlet** — plugs directly into rack PDU |
| Size | 4.8L chassis |
| Noise | ≤36 dB (6 heatpipes, dual fan) |
| Barebone price | ~$949 (Core Ultra 5) / ~$1,119 (Core Ultra 9 285HX) |

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| MS-02 Ultra barebone (Core Ultra 9 285HX) | 3 | $1,119 | $3,357 |
| 128GB DDR5 ECC SODIMM kit (4×32GB) | 3 | $400 | $1,200 |
| 2TB NVMe Gen4 (boot + VM storage) | 3 | $110 | $330 |
| 25GbE SFP28 switch (e.g., Mikrotik CRS312) | 1 | $600 | $600 |
| DAC cables 25GbE (3-pack) | 1 | $60 | $60 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total (no GPU)** | | | **~$5,754** |

Add optional GPUs per node:
- RTX 4060 Ti 16GB Low Profile: ~$400–450 per card → +$1,200–$1,350 for 3 nodes
- **Total with GPU inference**: ~$7,000–8,000

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Intel Core Ultra 9 285HX (24C/24T, 5.5GHz, Arrow Lake-HX) |
| Total cores | 72 cores / 72 threads |
| RAM per node | Up to 256GB ECC DDR5 (128GB in parts list) |
| Total RAM | 384GB (with 128GB per node) |
| Storage per node | 4× M.2 NVMe slots (1× PCIe 5.0 x4, others 4.0) |
| Network | 2× 25GbE SFP28 + 10GbE + 2.5GbE per node |
| PCIe slot | **PCIe 5.0 x16** — full dual-slot GPU support |
| PSU | Internal 350W AC, **IEC C14 inlet** (rack PDU native) |
| Idle power per node | ~35–45W (without GPU) |
| Total idle power | ~100–120W (no GPU); ~200–300W with GPUs |
| Noise | ≤36 dB |
| Form factor | 4.8L chassis |
| Rack format | racknex UM-MIN-207 (2.33U per unit) or Etsy 3U mounts |
| Power cabling | IEC C14 → rack PDU C13 directly (no adapter needed) |

**Annual electricity (no GPU)**: 110W × 8,760h × $0.13 = ~$125/year
**Savings vs current**: ~$935/year

**Advantages over MS-01 (Option C)**:
- **PCIe 5.0 x16 vs 4.0 x4** — supports full dual-slot GPUs, not just single-slot low-profile cards
- **256GB ECC RAM per node** — enterprise-grade memory protection, 4× the capacity of MS-01
- **25GbE vs 10GbE** — future-proof networking; 2× 25GbE for dedicated Ceph + VM traffic
- **Internal IEC C14 PSU** — no external power brick, plugs directly into rack PDU; cleanest rack integration of any mini PC option
- **4 M.2 NVMe slots vs 3** — more local storage without external NAS
- **Arrow Lake-HX** — newer CPU architecture (2024) vs 13th gen Intel (MS-01)

**Cons vs MS-01**:
- More expensive: ~$1,100+ barebone vs ~$500 for MS-01 barebone
- Larger chassis: 4.8L vs ~1L for smaller mini PCs
- 2.33U per unit in rack — a 3-node cluster takes ~7U vs ~4U for MS-01
- Overkill if GPU inference is not a priority

---

### Option E — Modern 1U Server-Class Machines

**Configuration**: 3-node cluster of purpose-built 1U rack servers

This option is included for completeness. Server-class hardware offers advantages in out-of-band management (iDRAC/iLO/IPMI), hot-swap PSU redundancy, and native rack rails — but these advantages now have mini PC equivalents (JetKVM for remote KVM, IEC C14 on MS-02 Ultra for power). The power and cost trade-offs generally favor mini PCs for a home lab context.

#### Evaluated Models

**Dell PowerEdge R360** (1U, single socket):
| Attribute | Value |
|-----------|-------|
| CPU | Intel Xeon E-2400 series (up to 8C, 95W TDP) |
| RAM | Up to 128GB DDR5 UDIMM (4 DIMM slots) |
| PSU | 600W Platinum or 700W Titanium hot-swap redundant |
| Dimensions | 1.68" × 18.97" × 24.57" (short-depth 1U) |
| GPU | 1× NVIDIA A2 60W single-width (optional) |
| iDRAC | iDRAC9 with full remote KVM |
| Estimated idle | ~60–80W |
| Price | ~$1,500–2,500 new (configured) |

**HPE ProLiant DL20 Gen11** (1U, single socket):
| Attribute | Value |
|-----------|-------|
| CPU | Intel Xeon E-2400 series (up to 8C, 95W TDP) |
| RAM | Up to 128GB DDR5 UDIMM (4 DIMM slots) |
| PSU | 290W standard, up to 1000W options |
| iLO | iLO 6 with full remote KVM |
| Short-depth 1U | Yes |
| Price | ~$1,200–2,000 new |

**Refurbished Dell R660 / R760** (1U/2U, dual socket):

Not recommended. Even refurbished these are $3,000–11,000+, idle at 150–250W per node, and far exceed the power and cost targets of a home lab replacement.

#### Full Cluster Parts List (R360-based)

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Dell PowerEdge R360 (Xeon E-2474G, 64GB DDR5, 2TB NVMe) | 3 | $2,000 | $6,000 |
| 8-port 10GbE switch (Mikrotik CRS309-1G-8S+IN) | 1 | $290 | $290 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| **Total** | | | **~$6,330** |

> Note: iDRAC remote KVM is built in — no JetKVM required for this option.

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Intel Xeon E-2474G (8C/16T, 3.6GHz) |
| Total cores | 24 cores / 48 threads |
| RAM per node | 64GB DDR5 UDIMM (upgradeable to 128GB) |
| Total RAM | 192GB |
| Storage | 2TB NVMe per node (standard drive bays available) |
| Network | Dual 10GbE onboard + optional 25GbE PCIe NIC |
| PCIe slot | 1× PCIe 4.0 x8 (GPU or NIC) |
| PSU | Hot-swap redundant (600W Platinum) |
| Remote management | iDRAC9 (full remote KVM, virtual media, power control) |
| Idle power per node | ~60–80W |
| Total idle power | ~180–240W |
| Noise | **40–55 dB** (enterprise 40mm fans at 8,000–15,000 RPM) |
| Form factor | 1U rack, 24.57" depth |
| Rack format | Standard 19" rack rails (included) |
| Power cabling | IEC C14 → rack PDU C13 (native, no adapters) |

**Annual electricity**: 210W × 8,760h × $0.13 = ~$239/year
**Savings vs current**: ~$821/year (significantly less than mini PC options)

**Advantages**:
- iDRAC/iLO out-of-band management built in (full remote KVM even when OS is down)
- Hot-swap redundant PSUs — replace without powering down
- ECC RAM standard
- Purpose-built for 24/7 MTBF-rated operation
- Standard rack rails included
- IEC C14 power (native rack PDU compatible)

**Why server-class is not recommended for this use case**:
- Fan noise is 40–55 dB — likely louder than current servers at idle, not quieter
- Idle power is 180–240W total vs 45–120W for mini PC options — 2–4× higher
- Cost is similar to or greater than Option D (MS-02 Ultra) but with fewer cores and no GPU path
- The iDRAC/IPMI advantage is eliminated by JetKVM ($69/node)
- The IEC C14 advantage is matched by the MS-02 Ultra's internal PSU

**When server-class IS the right choice**:
- You specifically need iDRAC/IPMI for automated lights-out operations (not just JetKVM)
- You need hot-swap PSU redundancy for SLA reasons
- You need standard rack rails without any adapter kits
- You need more than 128GB RAM per node without paying MS-02 Ultra prices

---

### Option F — DIY 2U Rack Build (Custom Desktop Components)

**Configuration**: 3-node cluster built from standard desktop components in 2U rack chassis — a middle ground between mini PCs and enterprise servers. Full ATX motherboard, desktop-class CPU (AM5 socket), standard DDR5 UDIMM, and standard ATX PSU in a purpose-built 2U rack case.

Two sub-configurations:

---

#### F1: Standard DIY (Silverstone RM23-502)

The Silverstone RM23-502 is a full ATX 2U rack chassis with 80mm fan mounts, 2.5"/3.5" drive bays, and multiple PCIe slot openings. It accepts any standard ATX motherboard and ATX PSU — no proprietary components.

##### CPU Variant Table

| CPU | Cores / Threads | TDP | Per Node Price | 3-Node Total | Cluster Cores |
|-----|----------------|-----|----------------|-------------|---------------|
| Ryzen 7 9700X | 8C / 16T | 65W | ~$280 | ~$4,944 | 24C / 48T |
| **Ryzen 9 9900X** *(recommended)* | **12C / 24T** | **120W (Eco: 65W)** | **~$410** | **~$5,334** | **36C / 72T** |
| Ryzen 9 9950X | 16C / 32T | 170W (Eco: 105W) | ~$550 | ~$5,754 | 48C / 96T |

> **9700X**: Natively 65W — easiest to cool, even viable in 1U. Best for power-constrained setups.
> **9900X (Eco Mode)**: Caps at 65W, making it as cool-friendly as the 9700X but with 50% more cores. Best all-around choice.
> **9950X**: Needs PBO tuning or 105W Eco Mode; stays within 2U thermal envelope but pushes it.

##### Full Cluster Parts List (F1 — Ryzen 9 9900X)

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Silverstone RM23-502 (full ATX 2U chassis) | 3 | $219 | $657 |
| ASUS Prime X670E-PRO WiFi or similar AM5 ATX board | 3 | $280 | $840 |
| Ryzen 9 9900X | 3 | $410 | $1,230 |
| 128GB DDR5-5600 (2× 64GB UDIMM) | 3 | $300 | $900 |
| Noctua NH-L9a-AM5 (37mm cooler, fits 2U with margin) | 3 | $45 | $135 |
| 2TB NVMe Gen4 (Samsung 990 Pro) | 3 | $160 | $480 |
| Corsair RM850x ATX PSU (IEC C14 native) | 3 | $130 | $390 |
| Mellanox ConnectX-3 dual 10GbE SFP+ (used) | 3 | $25 | $75 |
| Generic 2U sliding rack rails | 3 | $40 | $120 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total (Ryzen 9 9900X variant)** | | | **~$5,034** |

> Reusing the WD SN750 SE 1TB NVMe drives from the current servers saves ~$480 (3× NVMe line item).

---

#### F2: ASRock Rack Barebone (2U1G-B650)

The ASRock Rack 2U1G-B650 is a purpose-built 2U server barebone with AM5 socket, full IPMI/BMC out-of-band management, redundant 1200W PSU, and a PCIe 5.0 x16 slot verified for full-height GPU use (RTX A6000, etc.). This bridges the gap between DIY and enterprise: server-grade management features with a desktop-class CPU platform.

##### Full Cluster Parts List (F2)

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| ASRock Rack 2U1G-B650 barebone (chassis + board + redundant PSU + IPMI) | 3 | $1,825 | $5,475 |
| Ryzen 9 9900X | 3 | $410 | $1,230 |
| 128GB DDR5-5600 ECC (2× 64GB UDIMM) | 3 | $300 | $900 |
| 2TB NVMe Gen4 | 3 | $50 | $150 |
| Mellanox ConnectX-3 dual 10GbE SFP+ (onboard is 1GbE only) | 3 | $25 | $75 |
| **Total** | | | **~$7,830** |

> No JetKVM needed — IPMI/BMC is built in. PCIe 5.0 x16 supports full-height GPU with verified compatibility.

---

#### F1 Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Ryzen 9 9900X (12C / 24T, Zen 5, AM5) |
| Total cores | 36C / 72T (24–48C depending on CPU variant) |
| RAM per node | 128GB DDR5 UDIMM (optionally ECC — AM5 supports ECC) |
| Total RAM | 384GB |
| Storage | 2TB NVMe per node + 2.5" / 3.5" drive bays for SAS/SATA |
| Network | 10GbE via Mellanox ConnectX-3 PCIe NIC (upgradeable to 25GbE ConnectX-4 Lx for ~$60–80 used) |
| PCIe slots | 4–7 low-profile slots in RM23-502; full-height via 90° riser |
| GPU | LP PCIe cards native; full-height via riser |
| PSU | Standard ATX (Corsair RM850x), **IEC C14 inlet** — rack PDU native |
| Remote management | JetKVM ($69/node) |
| Idle power per node | ~35–45W (community-measured Ryzen 9000-series) |
| Total idle power | ~105–135W |
| Noise | ~25–35 dB (80mm Noctua fans at low RPM) |
| Form factor | 2U rack × 3 = 6U total |
| Rack format | Standard 19" rails (generic 2U rails) |
| Power cabling | IEC C14 → rack PDU C13 (native, no adapters) |

**Annual electricity (F1)**: ~120W × 8,760h × $0.13 = ~$136/year
**Savings vs current**: ~$924/year

---

#### Advantages over Mini PCs (Options A–D)

- **Full desktop CPUs (AM5)** — upgradeable to Zen 5 / Zen 6, not locked to one chip at purchase
- **128GB+ RAM per node** using standard DDR5 UDIMM (not SODIMM — better availability and pricing)
- **Standard ATX PSU with IEC C14** — native rack PDU, no external brick required
- **Multiple PCIe slots** — 4–7 LP slots in RM23-502; dedicated Ceph NIC + VM NIC + GPU in the same node
- **Standard parts** — any component (board, CPU, PSU, cooler) is individually replaceable; no proprietary adapters
- **Drive bays** — 2.5" and 3.5" bays for adding SAS/SATA storage alongside NVMe
- **AM5 socket longevity** — AMD committed to AM5 through 2027+; future CPU upgrades don't require a new board

#### Advantages over Enterprise Servers (Option E)

- **2–3× better per-core performance** — Zen 5 vs Xeon E-2400 (~4,000+ vs ~2,800 Passmark/core)
- **Quieter** — 80mm Noctua fans in 2U vs enterprise 40mm fans running at 8,000–15,000 RPM
- **Lower idle power** — ~35–45W vs 60–80W per node
- **Cheaper** — ~$1,700 per node (F1, 9900X) vs $2,000+ per node (R360)
- **Better upgradability** — AM5 platform vs dead-end Xeon E series
- **Full-height GPU path** via riser (vs single-width A2 only in R360)

#### Cons

- **Assembly required** — you build 3 PCs, not unbox and power on
- **6U rack space** — more than 1U servers or mini PC shelves (3U vs 1U shelf for Options A/B)
- **Higher idle power than mini PCs** — ~35–45W per node vs 15–30W for Options A/B
- **No IPMI/BMC in F1** — JetKVM provides remote KVM but not automated power control; F2 variant has full IPMI
- **No hot-swap PSU in F1** — standard ATX PSU; F2 variant has redundant PSU
- **More components to go wrong** — standard PC failure modes vs tested appliance (but also individually replaceable)

---

#### Why 1U Is Not Recommended for Home Lab

A 1U DIY build is technically possible but comes with significant noise and thermal compromises:

- **40mm fans required** at 1U height → 45–60 dB even at idle with desktop CPUs
- **CPU cooler clearance ~37mm** → limits to 65W TDP maximum (Noctua NH-L9a-AM5 barely fits)
- **Thermal throttling risk** under sustained load with limited airflow
- **Only viable** if rack is in a basement or dedicated noise-isolated closet

If 1U is a hard requirement, the **ASRock Rack 1U4LW-B650/2L2T** is the best turnkey option — tested AM5 in 1U with IPMI — but it's $900–1,100 barebone, totals ~$1,800/node, and is still loud. At that price, F2 (2U1G-B650) is the better value.

---

## Comparison Tables

### Full Option Comparison

| | **Option A** | **Option B** | **Option C** | **Option D** | **Option E** | **Option F** |
|---|---|---|---|---|---|---|
| **Hardware** | Beelink SER8 | Beelink SER9 Max | Minisforum MS-01 | Minisforum MS-02 Ultra | Dell R360 | DIY 2U (Silverstone RM23-502) |
| **CPU per node** | Ryzen 7 8745HS (8C, Zen 4) | Ryzen 7 H255 (8C, Zen 5) | i9-13900H (14C, 13th gen) | Core Ultra 9 285HX (24C, Arrow Lake) | Xeon E-2474G (8C) | Ryzen 9 9900X (12C, Zen 5, AM5) |
| **Total cores** | 24C / 48T | 24C / 48T | 42C / 60T | 72C / 72T | 24C / 48T | 36C / 72T (24–48C by CPU variant) |
| **Max RAM / node** | 64GB DDR5 | 64GB DDR5 | 96GB DDR5 | **256GB ECC DDR5** | 128GB DDR5 | 128GB DDR5 UDIMM (ECC optional) |
| **PCIe slot** | None | None | PCIe 4.0 x4 (single-slot LP) | **PCIe 5.0 x16** (dual-slot) | PCIe 4.0 x8 | 4–7 LP slots + full-height via riser |
| **GPU capable?** | No | No | Single-slot LP only | Yes (RTX 4060 Ti LP, etc.) | Single-width (A2) | LP native; full-height via riser |
| **Network** | 2.5GbE | 10GbE | 2× 10GbE SFP+ | 2× 25GbE SFP28 + 10GbE | 2× 10GbE | 10GbE PCIe NIC (upgradeable to 25GbE) |
| **Ceph capable?** | No (too slow) | Yes | Yes | Yes | Yes | Yes |
| **PSU / power in** | External DC brick | External DC brick | External DC brick | **Internal 350W, IEC C14** | Hot-swap, IEC C14 | **Standard ATX, IEC C14** |
| **Rack power** | NEMA PDU strip | NEMA PDU strip | NEMA PDU strip | **Direct to C13 PDU** | Direct to C13 PDU | **Direct to C13 PDU** |
| **Noise** | <30 dB | <30 dB | <30 dB | ≤36 dB | **40–55 dB** | ~25–35 dB (2U w/ Noctua 80mm) |
| **Idle power (cluster)** | ~45W | ~75W | ~90W | ~110W | ~210W | ~120W |
| **Rack format** | 1U shelf | 1U shelf | racknex 1.33U–2U | racknex 2.33U or Etsy 3U | Standard 1U rails | Standard 2U rails × 3 = 6U |
| **iDRAC/IPMI** | No (JetKVM instead) | No (JetKVM instead) | No (JetKVM instead) | No (JetKVM instead) | Yes (built-in) | No (JetKVM) — IPMI in F2 variant |
| **Total cost** | ~$1,722 | ~$3,262 | ~$4,692 | ~$5,754 (no GPU) | ~$6,330 | ~$5,034–5,754 (F1) / ~$7,830 (F2) |

### Compute Comparison (vs Current)

| Setup | Cores / Threads | RAM | Per-Core Speed (approx) | NVMe Gen |
|-------|----------------|-----|------------------------|----------|
| **Current (5 servers)** | ~152 vCPUs | 636GB | 1× (baseline) | Gen3 |
| **Option A (3× SER8)** | 24C / 48T | 192GB | **~4×** | Gen3/4 |
| **Option B (3× SER9 Max)** | 24C / 48T | 192GB | **~4.5×** | Gen4 |
| **Option C (3× MS-01)** | 42C / 60T | 192–288GB | **~5×** | Gen4 |
| **Option D (3× MS-02 Ultra)** | 72C / 72T | 384GB | **~5.5×** | Gen5/4 |
| **Option E (3× R360)** | 24C / 48T | 192GB | **~3×** | Gen4 |
| **Option F1 (3× DIY 2U, 9900X)** | 36C / 72T | 384GB | **~4.5×** | Gen4 |

Per-core speed: Modern mobile chips (Ryzen 8745HS, H255, i9-13900H, Core Ultra 9 285HX) all score 3,000–4,500+ Passmark per core vs ~1,800–2,000 for the Xeon E5-4650. The Xeon E-2474G in the R360 is ~2,800 per core — newer than the Dell servers but behind mobile silicon in single-threaded performance.

### Power & Noise Comparison

| Setup | Idle Watts | $/year electricity | Noise (dB) | Rack Space |
|-------|-----------|-------------------|------------|------------|
| **Current (5 servers)** | ~930W | ~$1,060 | 55–65 dB | 10–18U |
| **Option A (3× SER8)** | ~45W | ~$51 | <30 dB | ~1U shelf |
| **Option B (3× SER9 Max)** | ~75W | ~$85 | <30 dB | ~1U shelf |
| **Option C (3× MS-01)** | ~90W | ~$102 | <30 dB | ~4U (racknex) |
| **Option D (3× MS-02 Ultra)** | ~110W | ~$125 | ≤36 dB | ~7U (racknex) |
| **Option E (3× R360)** | ~210W | ~$239 | 40–55 dB | 3U (1U each) |
| **Option F1 (3× DIY 2U, 9900X)** | ~120W | ~$136 | ~25–35 dB | 6U (2U each) |

### Cost Comparison (net of resale)

| Setup | Hardware Cost | Est. Resale | Net Cost | Annual Power Savings |
|-------|--------------|-------------|----------|----------------------|
| **Option A** | ~$1,722 | $1,500–$3,700 | **-$1,978 to +$222** | ~$1,009/yr |
| **Option B** | ~$3,262 | $1,500–$3,700 | **-$438 to +$1,762** | ~$975/yr |
| **Option C** | ~$4,692 | $1,500–$3,700 | **$992–$3,192** | ~$958/yr |
| **Option D** | ~$5,754 | $1,500–$3,700 | **$2,054–$4,254** | ~$935/yr |
| **Option E** | ~$6,330 | $1,500–$3,700 | **$2,630–$4,830** | ~$821/yr |
| **Option F1** | ~$5,034–5,754 | $1,500–$3,700 | **$1,334–$4,254** | ~$924/yr |

> At the high end of resale ($3,700), Options A and B effectively pay for themselves. Option D becomes the right economic choice only if GPU inference is a priority — the inference cost savings can dwarf the hardware premium within months of use.

---

## Rack Mounting Solutions for Mini PCs

Mini PCs require 19" rack adapter kits since they weren't designed for rack deployment. The ecosystem has matured significantly — purpose-built solutions exist for the most popular home lab mini PCs.

### For Minisforum MS-01 / MS-A1 / MS-A2

| Product | Format | Capacity | Source | Est. Price |
|---------|--------|----------|--------|-----------|
| racknex UM-MIN-201 | 1.33U | 2× MS-01 + PSU bricks alongside | racknex.com | ~$80–120 |
| racknex UM-MIN-205 | 2U | 2× MS-01 with keystone front panel for cable routing | racknex.com | ~$100–150 |
| thingsINrack Dual Mount | 2U | 2× MS-01 (injection molded front panel) | Amazon | ~$60–100 |
| STRONG CLUB 2U Mount | 2U | 2× MS-01 / MS-A2 | Etsy / strongclub.com | ~$50–80 |
| Hive Tech Solutions | 2U | 1–2× MS-01 with keystone panel | hivets.au | ~$80–120 |

**Typical 3-node MS-01 rack layout**: 2× MS-01 in first 2U tray + 1× MS-01 in second 2U tray = **~4U total** for all 3 nodes.

### For Minisforum MS-02 Ultra

| Product | Format | Capacity | Source | Est. Price |
|---------|--------|----------|--------|-----------|
| racknex UM-MIN-207 | 2.33U | 1× MS-02 Ultra, keystone front-panel cable routing | racknex.com | ~$120–180 |
| Etsy 3U Mount | 3U | 1× MS-02 Ultra + cable management space | Etsy | ~$80–150 |

**Typical 3-node MS-02 Ultra rack layout**: 3× 2.33U ≈ **~7U total** (racknex) or 3× 3U = **9U** (Etsy mounts).

### For Beelink SER8 / SER9 Max / Generic Mini PCs

| Product | Format | Capacity | Source | Est. Price |
|---------|--------|----------|--------|-----------|
| RackSolutions 1U Universal Shelf | 1U | 2–4 mini PCs side by side | racksolutions.com | ~$80–120 |
| Amazon NUC 1U rack mount kit | 1U | 1–3 NUCs or similarly sized mini PCs | Amazon | ~$40–60 |
| Amazon NUC 3U mount (multi-bay) | 3U | Up to 8–12 NUCs | Amazon | ~$60–100 |
| JINGCHENGMEI 1U mount | 1U | Dell OptiPlex / generic mini PC | Amazon | ~$40–60 |

**Note**: Beelink SER8/SER9 units are roughly 140mm × 126mm × 60mm — they fit 2–3 per 1U shelf, depending on shelf depth and connector orientation.

---

## Power & Cabling in Rack Environments

### The Problem

Enterprise racks use IEC C13/C14 connectors on PDU outputs. Most mini PCs use external DC power bricks with barrel connectors — these don't plug directly into a rack PDU. This is a real-world operational challenge that the spec sheets don't address.

### By Hardware Type

#### DIY 2U (Option F1) and Enterprise Servers (Option E) — Best Case

Standard ATX PSUs use an IEC C14 inlet natively. Both the Silverstone RM23-502 DIY build (Option F1) and enterprise 1U servers (Option E) plug directly into a rack PDU C13 outlet with a standard IEC C13 cable. No adapters, no bricks, no cable management heroics.

For Option F1, the Corsair RM850x (and any ATX PSU) has this by default — it's a fundamental property of the ATX spec, not a premium feature. Any ATX PSU in any 2U chassis connects directly to a rack PDU.

#### MS-02 Ultra — Best Case Among Mini PCs

The MS-02 Ultra has an **internal 350W AC power supply with an IEC C14 inlet**. This is the exception among mini PCs — it connects directly to any rack PDU C13 outlet with a standard IEC C13 cable. No adapters, no bricks, no cable management heroics. If rack-native power cabling is a priority among mini PC options, this alone is a significant advantage.

#### MS-01, Beelink SER8, Beelink SER9 Max — External DC Brick

These units ship with an external AC/DC adapter (brick). In a rack environment you have four options:

1. **Consumer power strip in rack** (~$15–30): Mount a Tripp Lite or CyberPower strip behind the rack. Power bricks plug into NEMA 5-15 outlets. Works but is messy — you're mixing consumer and rack infrastructure.

2. **1U rackmount PDU with NEMA outlets** (~$100–200): An APC AP7900B or similar rackmount PDU with standard US NEMA 5-15 outlets. Power bricks plug in cleanly. Takes 1U of rack space but provides a clean, organized solution.

3. **Velcro bricks into rack tray** (~$0 extra): The racknex UM-MIN-201/205 kits and thingsINrack mounts include space alongside the mini PCs to velcro-mount power bricks. Bricks stay inside the tray, cable runs are short, and the front panel has keystone jacks to route connectors neatly. This is the intended solution for these mount kits.

4. **DC power bus (future)** (~TBD): Jeff Geerling's mini-rack project is developing a standardized DC power distribution system — a high-efficiency central PSU feeds DC barrel jacks to multiple mini PCs. This eliminates individual bricks entirely. Not production-ready as of early 2026.

### Cable Management Strategies

- Racknex kits include keystone jacks at the front panel — rear connectors route through to the front for clean patch-panel-style organization
- thingsINrack mounts support both forward and rear connector orientation — choose based on your rack's cable routing
- Use short (0.5m) patch cables or DAC cables for 10GbE/25GbE connections within the rack
- Bundle power bricks with velcro ties behind the mini PC tray
- Label power bricks at the AC inlet so you know which brick belongs to which node

---

## Out-of-Band Management — JetKVM

One of the traditional advantages of server-class hardware (Dell R360, HPE DL20) is iDRAC/IPMI: full remote KVM access including BIOS, boot screens, OS installer, and power control — even when the OS is completely down. Mini PCs lack this natively.

**JetKVM** solves this for mini PCs at $69 per unit.

### Specs

| Feature | Value |
|---------|-------|
| Video | HDMI input, 1080p60, H.264 hardware encoding |
| Latency | 30–60ms |
| Input emulation | USB keyboard, mouse, mass storage (mount ISOs remotely) |
| Network | 10/100 Ethernet |
| Cloud access | JetKVM Cloud via WebRTC (no port forwarding needed) |
| Software | Open-source (Golang on Linux) |
| Body | Die-cast zinc alloy |
| Price | $69 at jetkvm.com |

### What JetKVM Enables

- Access BIOS/UEFI settings on a headless mini PC remotely
- Mount an ISO to reinstall the OS without physically touching the machine
- Debug boot failures and kernel panics from anywhere
- Power control (requires a smart PDU or outlet, or physical access for initial setup)

### Cluster Cost

3× JetKVM = **$207** — included in the parts lists for Options A through D.

With JetKVM, the iDRAC/IPMI advantage of Option E (server-class) is largely eliminated for the remote KVM use case. The remaining server-class advantages are hot-swap PSU redundancy and automated lights-out power control via IPMI (power on/off via API) — JetKVM does not provide the latter without an additional smart PDU.

---

## Proxmox Architecture per Option

### Shared Architecture (all options)

```
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox VE Cluster                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │      │
│  │  olympus-1   │  │  olympus-2   │  │  olympus-3   │      │
│  │              │  │              │  │              │      │
│  │  VMs:        │  │  VMs:        │  │  VMs:        │      │
│  │  - Zeus      │  │  - Apollo    │  │  - Hermes    │      │
│  │  - Athena    │  │  - Artemis   │  │  - Perseus   │      │
│  │  - Prometheus│  │              │  │  - Ares      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         └─────────────────┼──────────────────┘              │
│                           │                                  │
│              Cluster Network (10GbE, 25GbE, or 2.5GbE)     │
└─────────────────────────────────────────────────────────────┘
```

**Quorum**: 3 nodes means any single node failure maintains quorum. VMs can be configured to migrate automatically with HA groups.

**Proxmox clustering requirements**:
- All nodes reachable on same subnet ✓
- NTP synchronized ✓
- SSH key trust between nodes ✓
- Corosync UDP ports 5404/5405 open ✓

### Option A: Local Storage, Manual Migration

```
Storage Model: Local-LVM per node
├── Node 1: local-lvm (zeus, athena, prometheus)
├── Node 2: local-lvm (apollo, artemis)
└── Node 3: local-lvm (hermes, perseus, ares)

Migration: Dead (planned downtime) — shut VM, copy disk, start
Backup: Proxmox Backup Server (PBS) on one node or external NAS
HA: Not practical without shared storage
```

Recommendation: Run PBS on one node with the reused WD SN750 1TB drives as backup storage.

### Option B / C / D / E: Ceph Distributed Storage

```
Storage Model: Ceph (3-way replicated)
├── Each node contributes 1× 2TB NVMe as OSD
├── Total raw: 6TB
├── Usable (3x replication): 2TB
├── All VMs migrate live between nodes
└── One node failure: cluster continues, no data loss

Ceph network: 10GbE or 25GbE (dedicated NIC/port)
VM network: separate NIC/port
Management: 2.5GbE or 1GbE
```

With 2TB usable for 8 VMs at 250GB each = 2TB exactly. Tight. Add a 4th NVMe per node (all options have spare slots) or external NAS for breathing room.

### Option D: Ceph + Full GPU Passthrough (LLM Inference)

```
Storage Model: Ceph on 3× 2TB NVMe = 2TB usable
               + optional 4th NVMe per node for overflow

GPU Path:
├── Node 1: RTX 4060 Ti LP via PCIe 5.0 x16 → Passthrough to LLM VM
├── Ollama container on GPU-enabled VM
└── All agent VMs call local Ollama endpoint (10.220.1.x:11434)

Network:
├── 25GbE port 1: Ceph replication traffic
├── 25GbE port 2: VM traffic + Ollama API
└── 2.5GbE: Management / Proxmox web UI

Proxmox HA:
├── zeus, athena: high-priority, fail over immediately
├── developer VMs: auto-restart (restart policy)
└── mattermost: migrate to dedicated LXC container
```

### Option F: Ceph + Dedicated NICs + Optional GPU (DIY 2U)

Option F follows the same Ceph + 10GbE model as Options B/C/D, with an added advantage: the Silverstone RM23-502 has 4–7 low-profile PCIe slots per node, so dedicated NICs for each traffic class don't compete for the same slot.

```
Storage Model: Ceph on 3× 2TB NVMe = 2TB usable (same as B/C/D)

Network (per node — 4-7 LP PCIe slots available):
├── Slot 1: Mellanox ConnectX-3 10GbE SFP+ → Ceph replication
├── Slot 2: Mellanox ConnectX-3 10GbE SFP+ → VM traffic
└── Onboard 1GbE: Management / Proxmox web UI
    (upgrade to ConnectX-4 Lx 25GbE for ~$60–80 used, same slots)

GPU Path (optional, F1 with riser or F2 native):
├── Full-height GPU via 90° riser in F1 chassis
├── PCIe 5.0 x16 native in F2 (ASRock Rack 2U1G-B650)
└── GPU passthrough to LLM VM (same Ollama setup as Option D)

AM5 Upgrade Path:
├── Ryzen 9 9900X → Ryzen 9 9950X3D (drop-in, same socket)
└── Zen 6 CPUs (2026+) will use AM5 — no board replacement needed
```

---

## Migration Plan

### Pre-Migration Checklist

- [ ] Take full disk image backups of all 8 VMs (using `virsh dumpxml` + `qemu-img convert`)
- [ ] Document current VM configs (vCPU, RAM, disk, network MACs)
- [ ] Export Mattermost data (`docker exec mattermost-postgres pg_dumpall`)
- [ ] Confirm all SSH keys work for agent VMs
- [ ] Test Ansible `agent_provision` and `openclaw` roles against a fresh VM

### Phase 1: Set Up New Cluster (parallel with old)

1. Receive and configure hardware
2. Install Proxmox VE on all 3 nodes
3. Create cluster and verify quorum
4. Set up storage (local-lvm or Ceph depending on option)
5. Configure network bridges (vmbr0 for VMs)
6. Assign IPs in same subnet (10.220.1.0/24) for DHCP compatibility
7. Set up JetKVM on each node (HDMI + USB, configure cloud access)

### Phase 2: Migrate VMs

The existing Ansible roles (`agent_provision`, `openclaw`) configure VMs post-boot. Migration options:

**Option A (cleanest)**: Reprovision fresh
- Create new VMs from cloud-init images in Proxmox
- Run existing Ansible playbooks against new VMs
- Restore agent data from backup (`~/.openclaw/`, GitHub SSH keys)
- Reconfigure DHCP reservations for new VM MAC addresses

**Option B (lift and shift)**: Convert and import
- Export each VM: `qemu-img convert -f raw -O qcow2 vm.img vm.qcow2`
- Import into Proxmox: `qm importdisk <vmid> vm.qcow2 local-lvm`
- Update cloud-init / networking if needed

Fresh provisioning is recommended since the existing Ansible automation handles it.

### Phase 3: Cutover

1. Stand up Mattermost on new node (LXC container or VM)
2. Verify all agent VMs connect to Mattermost
3. Test Claude Code / OpenClaw on new VMs
4. Update DNS/DHCP reservations to new MAC addresses
5. Decommission old servers (one at a time)

### Phase 4: Decommission and Sell

1. Wipe drives (shred or DBAN)
2. List on eBay (r820 first — highest value)
3. Remove servers from rack
4. Reconfigure rack with new mini PC shelf / rack mount kit

**Estimated migration time**: 2–4 hours of active work, 1–2 weekend days total

---

## Recommendation

There is no single "best" option — the right choice depends on what you plan to do with the cluster. Use this decision matrix:

### Decision Matrix

| Priority | Best Choice | Why |
|----------|-------------|-----|
| **Lowest power / quietest** | Option A (SER8) | ~45W idle, near-silent, lowest cost |
| **Best balance of performance + networking** | Option B (SER9 Max) | 10GbE unlocks Ceph and fast live migration; Zen 5 is current-gen |
| **GPU inference (single-slot)** | Option C (MS-01) | PCIe 4.0 x4 supports RTX 3050 / A2000 12GB for Ollama passthrough |
| **GPU inference (full dual-slot GPU)** | Option D (MS-02 Ultra) | PCIe 5.0 x16 supports RTX 4060 Ti LP or better; 256GB ECC RAM per node |
| **Rack-native power cabling (no bricks)** | Option D (MS-02 Ultra) | Only mini PC with internal IEC C14 PSU |
| **iDRAC/IPMI + hot-swap PSU** | Option E (1U server) | Built-in iDRAC9; JetKVM is sufficient for most KVM needs but not IPMI power control |
| **Maximum RAM capacity** | Option D (MS-02 Ultra) | 256GB ECC DDR5 per node (768GB cluster) |
| **Maximum flexibility / repairability** | Option F1 (DIY 2U) | Standard desktop parts, AM5 socket through 2027+, any component individually replaceable |
| **IPMI + GPU + desktop CPU (server-grade features)** | Option F2 (ASRock Rack) | IPMI/BMC + PCIe 5.0 x16 + AM5 Zen 5 — server management with desktop-class performance |

### Key Trade-offs at a Glance

**Option A vs B**: The $1,500 premium for SER9 Max buys you 10GbE (Ceph + fast migration). If you ever want live migration to be seamless, pay it.

**Option B vs C**: The $1,400 premium for MS-01 buys you a PCIe slot for a GPU. If local LLM inference is on the roadmap (even 12 months out), this is worth it. If not, SER9 Max is the better value.

**Option C vs D**: The $1,000+ premium for MS-02 Ultra buys you PCIe 5.0 x16 (full GPU vs limited single-slot), 256GB ECC RAM, 25GbE, and no external power brick. If GPU inference is the primary motivation, Option D is the right choice. If the MS-01's PCIe x4 is sufficient for your GPU plans, Option C saves money.

**Option D vs E**: Server-class hardware costs as much as or more than the MS-02 Ultra cluster, uses 2–4× more power, and is significantly louder. The only remaining advantage is hot-swap PSU redundancy and IPMI-level power control. For a home lab, these don't justify the trade-offs.

**Option D vs F1**: The MS-02 Ultra gives you Arrow Lake-HX + 256GB ECC + 25GbE in a 4.8L chassis for ~$5,754. Option F1 with the 9900X gives you Zen 5 + 128GB + 10GbE in a 2U rack chassis for ~$5,034, but with full ATX upgradability, 4–7 PCIe slots, and every component individually replaceable. F1 costs less for similar performance, but MS-02 Ultra wins on RAM density (256GB ECC) and network speed (25GbE). DIY wins on PCIe flexibility (multiple slots vs one), long-term repairability, and AM5 upgrade path. If you ever want to swap the CPU for a Zen 6 chip without buying a new system, F1 is the right call.

**Option E vs F2**: The Dell R360 at ~$6,330 gives you Xeon E-2474G (8C) + iDRAC9 + hot-swap PSU in a tested 1U appliance. The ASRock Rack 2U1G-B650 at ~$7,830 gives you Ryzen 9 9900X (12C) + IPMI/BMC + redundant PSU + PCIe 5.0 x16 for full GPU. F2 costs more but delivers 50% more cores, significantly better per-core performance (Zen 5 vs Xeon E), and a full GPU passthrough path. Choose F2 if you want server-grade out-of-band management with desktop-class compute and a real GPU option.

### Action Items

1. **Confirm r820 RAM** — SSH in and verify the 384GB measurement: `free -h`. If confirmed, list on eBay immediately. This server funds most of the upgrade.
2. **Decide on GPU path** — If local Ollama inference is a 6–12 month goal, go Option C or D. If not, Option B is the sweet spot.
3. **Decide on rack vs shelf** — If you want clean rack integration, Options C/D (with racknex mounts) or Option D (native IEC C14) are better than A/B with brick adapters.
4. **Order hardware** — Current lead times are 2–5 days for all items (Amazon Prime eligible). MS-02 Ultra may ship from Minisforum with 1–2 week lead time.
5. **Keep the NVMe drives** — Pull all 5 WD SN750 1TB drives before selling servers. They fit directly in mini PC M.2 slots and are worth ~$350 total.

---

*Analysis based on SSH inspection (Feb 28, 2026), repository review, and current market pricing as of February 2026. Prices may vary; verify before purchasing.*
