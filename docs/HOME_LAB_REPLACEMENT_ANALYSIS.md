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
6. [DDR5 Pricing Crisis — March 2026](#ddr5-pricing-crisis--march-2026)
7. [Replacement Options](#replacement-options)
   - [Option A — Beelink SER8 Cluster](#option-a--beelink-ser8-cluster-budget-mini-pc)
   - [Option B — Beelink SER9 Max Cluster](#option-b--beelink-ser9-max-cluster-10gbe-mini-pc)
   - [Option C — Minisforum MS-01 Cluster](#option-c--minisforum-ms-01-cluster-workstation-mini-pc)
   - [Option D — Minisforum MS-02 Ultra Cluster](#option-d--minisforum-ms-02-ultra-cluster-gpu-ready-workstation)
   - [Option E — Modern 1U Server-Class Machines](#option-e--modern-1u-server-class-machines)
   - [Option F — DIY 2U Rack Build](#option-f--diy-2u-rack-build-custom-desktop-components)
   - [Option G — Minisforum MS-A2 Cluster](#option-g--minisforum-ms-a2-cluster-zen-5-workstation)
   - [Option H — GEEKOM GT15 Max Cluster](#option-h--geekom-gt15-max-cluster-intel-ai-mini-pc)
   - [Option I — Minisforum MS-S1 Max Cluster](#option-i--minisforum-ms-s1-max-cluster-ai-workstation)
   - [Option J — Refurbished 14th/15th Gen Dell Servers](#option-j--refurbished-1415th-gen-dell-servers-crisis-era-value)
8. [Hybrid Cluster Configurations](#hybrid-cluster-configurations)
9. [Buy Now vs Wait Analysis](#buy-now-vs-wait-analysis)
10. [Additional Mini PCs Evaluated](#additional-mini-pcs-evaluated)
11. [Comparison Tables](#comparison-tables)
12. [Rack Mounting Solutions for Mini PCs](#rack-mounting-solutions-for-mini-pcs)
13. [Power & Cabling in Rack Environments](#power--cabling-in-rack-environments)
14. [Out-of-Band Management — JetKVM](#out-of-band-management--jetkvm)
15. [Proxmox Architecture per Option](#proxmox-architecture-per-option)
16. [Migration Plan](#migration-plan)
17. [Recommendation](#recommendation)

---

## Executive Summary

The current home lab runs 8 AI agent VMs (Mount Olympus / OpenClaw) across 5 Dell PowerEdge servers that are 12–17 years old. These servers collectively consume ~930W at idle (~$1,060/year in electricity), produce significant noise, and have critical limitations including: no KVM hardware virtualization on the r420, no NVMe boot support on older RAID controllers, and decade-old memory controllers that bottleneck performance.

A 3-node cluster of modern mini PCs would match or exceed current compute capacity, reduce idle power draw by ~95% ($50–100/year), eliminate noise, and cost $3,500–$10,000+ depending on configuration.

> **⚠ March 2026 pricing alert**: DDR5 memory is in a global supply crisis. The AI hardware boom shifted DRAM manufacturing capacity to HBM, causing consumer DDR5 prices to spike 300–400% since mid-2025. A 64GB DDR5 SODIMM kit that cost $130 in early 2025 now costs ~$630. All prices in this document reflect March 2026 crisis pricing — see [DDR5 Pricing Crisis](#ddr5-pricing-crisis--march-2026) for full context. Reselling current hardware (especially the r820 with 384GB RAM) can recover $1,000–$3,000, significantly offsetting the replacement cost.

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

## DDR5 Pricing Crisis — March 2026

### What Happened

Between mid-2025 and March 2026, consumer DDR5 prices surged 300–400%. The root cause is a structural DRAM manufacturing shift: AI infrastructure demand (HBM3/HBM3e for GPUs and accelerators) absorbed the wafer capacity that previously supplied consumer DDR5. Samsung, SK Hynix, and Micron all reallocated capacity to higher-margin HBM production. Consumer DDR5 supply tightened severely while demand remained flat or grew.

### DDR5 Price Trajectory

| Component | Early 2025 | March 2026 | Change |
|-----------|-----------|------------|--------|
| 64GB DDR5-5600 SODIMM (2×32GB) | ~$110–130 | **~$630** | ~+400% |
| 128GB DDR5-5600 UDIMM (2×64GB) | ~$295 | **~$1,243** | ~+320% |
| 128GB DDR5 ECC SODIMM (4×32GB) | ~$400 | **~$1,300–1,500** | ~+250% |
| Samsung 990 Pro 2TB NVMe | ~$115–133 | **~$230** | ~+73% |

NAND prices (NVMe) also rose, though less severely — supply is constrained but not as structurally disrupted as DRAM.

### Strategic Impact

The DDR5 shortage changes the fundamental economics of this analysis:

1. **Configured units now beat barebone + upgrade**: A SER9 Max 64GB/1TB configured at $779 is substantially cheaper than SER9 Max 32GB/1TB ($699) + 64GB DDR5 SODIMM kit ($630) = $1,329. When RAM is at crisis pricing, paying for factory-installed RAM is the smart move.

2. **128GB options are hit hardest**: Options requiring 128GB UDIMM or ECC SODIMM (D, F1, F2) see the biggest cost increases — RAM now represents 40–50% of per-node cost.

3. **Refurbished servers with DDR4 become competitive**: DDR4 ECC is not affected by the DDR5 shortage. A refurbished 14th-gen Dell server with 128GB DDR4 ECC included in the purchase price is now cost-competitive with mini PC options that require buying expensive DDR5. See [Option J](#option-j--refurbished-1415th-gen-dell-servers-crisis-era-value).

4. **Soldered/integrated RAM options gain relative value**: Options I (MS-S1 Max with 128GB soldered LPDDR5x) and H (GT15 Max with RAM in unit price) are relatively more attractive — you're not exposed to spot DDR5 pricing.

### When Will This Normalize?

Memory market analysts project DDR5 consumer prices will not fully normalize until late 2027, when new HBM-dedicated fabs come online and free up conventional DRAM capacity. If you are buying a 64GB cluster option, the current price premium over "normal" DDR5 is roughly $1,500 for a 3-node cluster (3 × $500 premium per kit). That premium is recovered through electricity savings in approximately 18 months. For 128GB options, the RAM premium is $3,000–$4,500 — waiting for normalization is economically rational if you can tolerate the current hardware for 18–24 more months.

See [Buy Now vs Wait Analysis](#buy-now-vs-wait-analysis) for the break-even calculation.

---

## Replacement Options

All options target Proxmox VE 8.x as the hypervisor, replace all 5 servers, and are designed to run at least 8 VMs (the current load) with headroom for growth. Each option includes 3× JetKVM ($69 each, $207 total) for remote KVM access — see [Out-of-Band Management](#out-of-band-management--jetkvm).

---

### Option A — Beelink SER8 Cluster (Budget Mini PC)

**Configuration**: 3-node cluster of Beelink SER8 mini PCs

The SER8 is the most affordable path to a modern cluster. Good per-core performance, DDR5, and near-silent operation. Networking is 2.5GbE — capable for VM traffic but insufficient for Ceph distributed storage.

#### Retailer Price Reference (Option A Key Components)

| Component | Amazon | eBay (new) | Newegg | Beelink Direct | Best Price |
|-----------|--------|-----------|--------|----------------|-----------|
| Beelink SER8 (32GB/1TB) | ~$479 | ~$460–479 | ~$489 | ~$479 | **$479** |
| Crucial 64GB DDR5-5600 SODIMM (2×32GB) | ~$630 | ~$580–620 | ~$649 | crucial.com ~$630 | **$630** |
| TRENDnet TEG-S380 8-port 2.5GbE | ~$122 | ~$100–115 | ~$130 | trendnet.com ~$140 | **$122** |
| JetKVM | jetkvm.com $69 | N/A | N/A | jetkvm.com $69 | **$69** |

> **⚠ DDR5 pricing note**: 64GB SODIMM kits that cost ~$130 in early 2025 are now ~$630 (March 2026) due to the global memory shortage. See [DDR5 Pricing Crisis](#ddr5-pricing-crisis--march-2026).

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Beelink SER8 (AMD Ryzen 7 8745HS, 32GB DDR5-5600, 1TB NVMe) | 3 | $479 | $1,437 |
| Crucial 64GB DDR5-5600 SODIMM kit (2×32GB, replaces stock) | 3 | $630 | $1,890 |
| 8-port 2.5GbE switch (TRENDnet TEG-S380) | 1 | $122 | $122 |
| CAT6 patch cables (3-pack) | 1 | $15 | $15 |
| Small shelf or drawer for mini PCs | 1 | $30 | $30 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$3,701** |

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

#### Retailer Price Reference (Option B Key Components)

| Component | Amazon | eBay (new) | Newegg | Manufacturer | Best Price |
|-----------|--------|-----------|--------|--------------|-----------|
| Beelink SER9 Max (32GB/1TB, 10GbE) | ~$699 | ~$640–699 | ~$699 | beelink-store.com ~$699 | **$699** |
| **Beelink SER9 Max (64GB/1TB, 10GbE) — recommended** | ~$779 | ~$740–779 | ~$789 | beelink-store.com ~$779 | **$779** |
| Crucial 64GB DDR5-5600 SODIMM (2×32GB) | ~$630 | ~$580–620 | ~$649 | crucial.com ~$630 | **$630** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | ~$230 | ~$200–220 | ~$230 | mikrotik.com ~$230 | **$230** |
| JetKVM | jetkvm.com $69 | N/A | N/A | jetkvm.com $69 | **$69** |

> **Crisis-era buying note**: At current DDR5 pricing, buying the SER9 Max 64GB/1TB configured SKU ($779) is far cheaper than buying the 32GB/1TB SKU ($699) and upgrading with a 64GB SODIMM kit ($630) = $1,329 total. The parts list below uses the 64GB configured SKU.

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Beelink SER9 Max (AMD Ryzen 7 H255, **64GB** DDR5, 1TB NVMe, 10GbE) | 3 | $779 | $2,337 |
| Samsung 990 Pro 2TB NVMe (2nd M.2 slot, VM storage) | 3 | $230 | $690 |
| 8-port 10GbE switch (MikroTik CRS309-1G-8S+IN) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| CAT6 patch cables | 1 | $15 | $15 |
| Small shelf or 1U tray | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$3,559** |

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

#### Retailer Price Reference (Option C Key Components)

| Component | Amazon | eBay (new) | Newegg | Minisforum Direct | Best Price |
|-----------|--------|-----------|--------|-------------------|-----------|
| Minisforum MS-01 barebone (i9-13900H) | ~$539 | ~$480–539 | ~$559 | minisforum.com ~$539 | **$539** |
| MS-01 configured (32GB/1TB) | ~$699 | ~$640–699 | ~$699 | minisforum.com ~$699 | **$699** |
| Crucial 64GB DDR5-5600 SODIMM (2×32GB) | ~$630 | ~$580–620 | ~$649 | crucial.com ~$630 | **$630** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | ~$230 | ~$200–220 | ~$230 | mikrotik.com ~$230 | **$230** |
| Synology DS423+ (4-bay NAS) | ~$450 | ~$380–430 | ~$460 | synology.com ~$450 | **$450** |
| WD Red Plus 4TB NAS HDD | ~$85 | ~$70–80 | ~$88 | — | **$85** |

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-01 barebone (i9-13900H) | 3 | $539 | $1,617 |
| Crucial 64GB DDR5-5600 SODIMM kit (2×32GB) | 3 | $630 | $1,890 |
| Samsung 990 Pro 2TB NVMe (boot/OS) | 3 | $230 | $690 |
| Samsung 990 Pro 2TB NVMe (2nd M.2, VM storage) | 3 | $230 | $690 |
| 8-port 10GbE switch (MikroTik CRS309-1G-8S+IN) | 1 | $230 | $230 |
| SFP+ DAC cables (1m, 3-pack) | 1 | $40 | $40 |
| Synology DS423+ NAS (4-bay, for shared VM storage) | 1 | $450 | $450 |
| 4× WD Red Plus 4TB NAS HDD | 4 | $85 | $340 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$6,154** |

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
| Barebone price | ~$949 (Core Ultra 5) / ~$1,199 (Core Ultra 9 285HX) |

#### Retailer Price Reference (Option D Key Components)

| Component | Amazon | eBay (new) | Newegg | Minisforum Direct | Best Price |
|-----------|--------|-----------|--------|-------------------|-----------|
| MS-02 Ultra barebone (Core Ultra 9 285HX) | ~$1,199 | ~$1,100–1,199 | ~$1,219 | minisforum.com ~$1,199 | **$1,199** |
| 128GB DDR5 ECC SODIMM kit (4×32GB) | ~$1,300 | ~$1,200–1,300 | ~$1,349 | OWC/NEMIX ~$1,300 | **$1,300** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| MikroTik CRS312-4C+8XG (25GbE switch) | ~$580 | ~$530–580 | ~$590 | mikrotik.com ~$580 | **$580** |
| JetKVM | jetkvm.com $69 | N/A | N/A | jetkvm.com $69 | **$69** |

> **⚠ DDR5 pricing note**: 128GB DDR5 ECC SODIMM kits (4×32GB) that cost ~$400 in early 2025 are now ~$1,300 (March 2026). See [DDR5 Pricing Crisis](#ddr5-pricing-crisis--march-2026).

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| MS-02 Ultra barebone (Core Ultra 9 285HX) | 3 | $1,199 | $3,597 |
| 128GB DDR5 ECC SODIMM kit (4×32GB) | 3 | $1,300 | $3,900 |
| Samsung 990 Pro 2TB NVMe (boot + VM storage) | 3 | $230 | $690 |
| 25GbE SFP28 switch (MikroTik CRS312-4C+8XG) | 1 | $580 | $580 |
| DAC cables 25GbE (3-pack) | 1 | $60 | $60 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total (no GPU)** | | | **~$9,034** |

Add optional GPUs per node:
- RTX 4060 Ti 16GB Low Profile: ~$400–450 per card → +$1,200–$1,350 for 3 nodes
- **Total with GPU inference**: ~$10,300–11,400

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
| Ryzen 7 9700X | 8C / 16T | 65W | ~$260 | ~$4,548 | 24C / 48T |
| **Ryzen 9 9900X** *(recommended)* | **12C / 24T** | **120W (Eco: 65W)** | **~$374** | **~$4,782** | **36C / 72T** |
| Ryzen 9 9950X | 16C / 32T | 170W (Eco: 105W) | ~$530 | ~$5,172 | 48C / 96T |

> **9700X**: Natively 65W — easiest to cool, even viable in 1U. Best for power-constrained setups.
> **9900X (Eco Mode)**: Caps at 65W, making it as cool-friendly as the 9700X but with 50% more cores. Best all-around choice.
> **9950X**: Needs PBO tuning or 105W Eco Mode; stays within 2U thermal envelope but pushes it.

##### Retailer Price Reference (Option F1 Key Components)

| Component | Amazon | eBay (new) | Newegg | B&H / Micro Center | Best Price |
|-----------|--------|-----------|--------|--------------------|-----------|
| Silverstone RM23-502 (2U ATX chassis) | ~$176 | ~$155–175 | ~$180 | B&H ~$176 | **$176** |
| ASUS Prime X670E-PRO WiFi (AM5 ATX) | ~$280 | ~$245–275 | ~$285 | Micro Center ~$270 | **$270** |
| AMD Ryzen 9 9900X | ~$374 | ~$340–370 | ~$379 | Micro Center ~$349 | **$349** |
| 128GB DDR5-5600 UDIMM (2×64GB) | ~$1,243 | ~$1,150–1,243 | ~$1,289 | Best Buy ~$1,243 | **$1,243** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | B&H ~$235 | **$230** |
| Corsair RM850x ATX PSU | ~$136 | ~$120–130 | ~$140 | B&H ~$135 | **$136** |
| Mellanox ConnectX-3 dual 10GbE SFP+ (used) | ~$25 | ~$20–30 | ~$28 | — | **$22** (eBay) |

> **⚠ DDR5 pricing note**: 128GB DDR5-5600 UDIMM kits (2×64GB) that cost ~$295 in early 2025 are now ~$1,243 (Best Buy, March 2026). See [DDR5 Pricing Crisis](#ddr5-pricing-crisis--march-2026).

##### Full Cluster Parts List (F1 — Ryzen 9 9900X)

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Silverstone RM23-502 (full ATX 2U chassis) | 3 | $176 | $528 |
| ASUS Prime X670E-PRO WiFi or similar AM5 ATX board | 3 | $270 | $810 |
| Ryzen 9 9900X | 3 | $374 | $1,122 |
| 128GB DDR5-5600 (2× 64GB UDIMM) | 3 | $1,243 | $3,729 |
| Noctua NH-L9a-AM5 (37mm cooler, fits 2U with margin) | 3 | $45 | $135 |
| Samsung 990 Pro 2TB NVMe (boot + VM storage) | 3 | $230 | $690 |
| Corsair RM850x ATX PSU (IEC C14 native) | 3 | $136 | $408 |
| Mellanox ConnectX-3 dual 10GbE SFP+ (used, eBay) | 3 | $22 | $66 |
| Generic 2U sliding rack rails | 3 | $40 | $120 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total (Ryzen 9 9900X variant)** | | | **~$7,815** |

> Reusing the WD SN750 SE 1TB NVMe drives from the current servers saves ~$480 (3× NVMe line item).

---

#### F2: ASRock Rack Barebone (2U1G-B650)

The ASRock Rack 2U1G-B650 is a purpose-built 2U server barebone with AM5 socket, full IPMI/BMC out-of-band management, redundant 1200W PSU, and a PCIe 5.0 x16 slot verified for full-height GPU use (RTX A6000, etc.). This bridges the gap between DIY and enterprise: server-grade management features with a desktop-class CPU platform.

##### Retailer Price Reference (Option F2 Key Components)

| Component | Amazon | eBay (new) | Newegg | ASRock Direct | Best Price |
|-----------|--------|-----------|--------|---------------|-----------|
| ASRock Rack 2U1G-B650 barebone | ~$1,348 | ~$1,250–1,348 | ~$1,389 | asrockrack.com ~$1,348 | **$1,348** |
| AMD Ryzen 9 9900X | ~$374 | ~$340–370 | ~$379 | Micro Center ~$349 | **$349** |
| 128GB DDR5-5600 ECC UDIMM (2×64GB) | ~$1,243 | ~$1,150–1,243 | ~$1,289 | Best Buy ~$1,243 | **$1,243** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |

##### Full Cluster Parts List (F2)

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| ASRock Rack 2U1G-B650 barebone (chassis + board + redundant PSU + IPMI) | 3 | $1,348 | $4,044 |
| Ryzen 9 9900X | 3 | $374 | $1,122 |
| 128GB DDR5-5600 ECC (2× 64GB UDIMM) | 3 | $1,243 | $3,729 |
| Samsung 990 Pro 2TB NVMe | 3 | $230 | $690 |
| Mellanox ConnectX-3 dual 10GbE SFP+ (onboard is 1GbE only) | 3 | $22 | $66 |
| **Total** | | | **~$9,651** |

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

> **Price note**: The ASRock Rack 2U1G-B650 was previously listed at $1,825 in this analysis. Current unit price (March 2026) is ~$1,348. However, the 128GB DDR5-5600 ECC UDIMM RAM is now ~$1,243/kit (up from ~$295), making the overall cluster total **~$9,651** — significantly higher than the original estimate despite the unit price drop.

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

### Option G — Minisforum MS-A2 Cluster (Zen 5 Workstation)

**Configuration**: 3-node cluster of Minisforum MS-A2 mini PCs — the spiritual successor to the MS-01 with a full AMD Zen 5 upgrade (Ryzen 9 9955HX), a physically PCIe 4.0 x16 slot (electrically x8), and native dual 10GbE SFP+.

The MS-A2 is ServeTheHome's recommended "nearly perfect homelab system" as of early 2026. It fixes the MS-01's two biggest weaknesses — outdated 13th gen Intel CPU and limited PCIe bandwidth — while keeping the same dual 10GbE SFP+ form factor.

#### Hardware Specs

| Attribute | Value |
|-----------|-------|
| CPU | AMD Ryzen 9 9955HX (16C/32T, up to 5.4GHz, Zen 5) |
| RAM | 2× DDR5 SODIMM slots, up to **96GB DDR5** |
| Storage | 2× M.2 NVMe slots (PCIe 4.0) |
| GPU slot | **PCIe 4.0 x16 physical / x8 electrical** — single-slot low-profile GPU |
| Network | **2× 10GbE SFP+** + 1× 2.5GbE RJ45 |
| PSU | External DC brick (120W) |
| Size | ~209mm × 195mm × 43mm (same footprint as MS-01) |
| Barebone price | ~$799 (price drop from launch $839) |

> **vs MS-01 (Option C)**: MS-A2 has 16C Zen 5 vs 14C 13th gen Intel, same dual 10GbE, same form factor. PCIe slot is x8 electrical vs x4 on MS-01 — better GPU bandwidth. The MS-A2 is the clear upgrade pick if buying new in 2026.

#### Retailer Price Reference (Option G Key Components)

| Component | Amazon | eBay (new) | Newegg | Minisforum Direct | Best Price |
|-----------|--------|-----------|--------|-------------------|-----------|
| Minisforum MS-A2 barebone (Ryzen 9 9955HX) | ~$799 | ~$770–799 | ~$819 | minisforum.com ~$799 | **$799** |
| Crucial 64GB DDR5-5600 SODIMM (2×32GB) | ~$630 | ~$580–620 | ~$649 | crucial.com ~$630 | **$630** |
| Samsung 990 Pro 2TB NVMe | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | ~$230 | ~$200–220 | ~$230 | mikrotik.com ~$230 | **$230** |
| JetKVM | jetkvm.com $69 | N/A | N/A | jetkvm.com $69 | **$69** |

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-A2 barebone (Ryzen 9 9955HX) | 3 | $799 | $2,397 |
| Crucial 64GB DDR5-5600 SODIMM kit (2×32GB) | 3 | $630 | $1,890 |
| Samsung 990 Pro 2TB NVMe (VM storage, 2nd M.2) | 3 | $230 | $690 |
| 8-port 10GbE switch (MikroTik CRS309-1G-8S+IN) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$5,454** |

> Optional RAM upgrade to 96GB: 2×48GB kit (~$630/kit at current pricing) → ~$1,890 for cluster (same as the 64GB kits!). RAM upgrade economics are severely impacted by the DDR5 shortage.

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | AMD Ryzen 9 9955HX (16C/32T, 5.4GHz, Zen 5) |
| Total cores | 48 cores / 96 threads |
| RAM per node | 64GB DDR5 (upgradeable to 96GB with 2×48GB kit) |
| Total RAM | 192GB (288GB max) |
| Storage per node | 1× included M.2 slot + 1× 2TB add-on |
| Network | 2× 10GbE SFP+ + 2.5GbE per node |
| PCIe slot | PCIe 4.0 x16 physical / x8 electrical (single-slot LP GPU) |
| Idle power per node | ~30–35W |
| Total idle power | ~90–105W |
| Noise | <30 dB |
| Form factor | Mini PC (~209mm × 195mm × 43mm) |
| Rack format | racknex UM-MIN-201 or STRONG CLUB 2U mount (same as MS-01) |
| Power cabling | External DC brick → NEMA 5-15 PDU strip |

**Annual electricity**: 97W × 8,760h × $0.13 = ~$110/year
**Savings vs current**: ~$950/year

**Advantages**:
- Zen 5 16-core CPU — most capable mini PC node for compute-heavy workloads
- Dual 10GbE SFP+ — enables Ceph and fast live migration (same as MS-01)
- PCIe x8 electrical — better GPU bandwidth than MS-01 (x4 electrical)
- Same racknex/mount ecosystem as MS-01 (drop-in replacement)
- 96GB max RAM per node (vs 64GB for Beelink options)

**Limitations**:
- PCIe slot is still single-slot low-profile only (vs MS-02 Ultra's full dual-slot)
- External DC brick (not IEC C14 native)
- Barebone only — must source RAM and NVMe separately

---

### Option H — GEEKOM GT15 Max Cluster (Intel AI Mini PC)

**Configuration**: 3-node cluster of GEEKOM GT15 Max mini PCs — a premium Intel Core Ultra 9 mini PC aimed at AI workloads. Strong CPU performance, but the weakest networking and no PCIe slot of any option in this analysis.

#### Hardware Specs

| Attribute | Value |
|-----------|-------|
| CPU | Intel Core Ultra 9 285H (16C/22T, up to 5.4GHz, Lunar Lake) |
| RAM | 2× DDR5 SODIMM slots, up to **64GB DDR5** |
| Storage | 2× M.2 NVMe slots |
| GPU slot | **None** |
| Network | **2× 2.5GbE RJ45** only — no 10GbE option |
| PSU | External DC brick |
| Unit price (configured, 32GB/1TB) | ~$1,234 |

> **Verdict**: The GT15 Max is a strong single-node workstation but a poor cluster node. No 10GbE means no Ceph distributed storage, slow live VM migration, and the $1,234/node cost is significantly higher than MS-A2 ($839) for a worse cluster feature set.

#### Retailer Price Reference (Option H Key Components)

| Component | Amazon | eBay (new) | Newegg | GEEKOM Direct | Best Price |
|-----------|--------|-----------|--------|---------------|-----------|
| GEEKOM GT15 Max (Core Ultra 9 285H, 32GB/1TB) | ~$1,234 | ~$1,100–1,200 | ~$1,249 | geekom.com ~$1,234 | **$1,200** (eBay) |
| Samsung 990 Pro 2TB NVMe (2nd M.2) | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| 8-port 2.5GbE switch (TP-Link TL-SG108-M2) | ~$80 | ~$70–78 | ~$82 | — | **$80** |
| JetKVM | jetkvm.com $69 | N/A | N/A | jetkvm.com $69 | **$69** |

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| GEEKOM GT15 Max (Core Ultra 9 285H, 32GB DDR5, 1TB NVMe) | 3 | $1,234 | $3,702 |
| Samsung 990 Pro 2TB NVMe (2nd M.2, VM storage) | 3 | $230 | $690 |
| 8-port 2.5GbE switch (TP-Link TL-SG108-M2) | 1 | $80 | $80 |
| CAT6 patch cables | 1 | $15 | $15 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$4,694** |

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Intel Core Ultra 9 285H (16C/22T, 5.4GHz, Lunar Lake) |
| Total cores | 48 cores / 66 threads |
| RAM per node | 32GB DDR5 (upgradeable to 64GB, 2-SODIMM) |
| Total RAM | 96GB (192GB with upgrade) |
| Storage per node | 2× M.2 NVMe |
| Network | **2× 2.5GbE only** — no 10GbE |
| PCIe slot | **None** |
| Idle power per node | ~35–45W |
| Total idle power | ~105–135W |
| Noise | <30 dB |
| Form factor | Mini PC |
| Rack format | Generic 1U shelf or NUC-style rack tray |
| Power cabling | External DC brick → NEMA 5-15 PDU strip |

**Annual electricity**: 120W × 8,760h × $0.13 = ~$136/year
**Savings vs current**: ~$924/year

**Why Option H is not recommended as a cluster**:
- 2.5GbE is identical to budget Option A (SER8) for networking — no Ceph
- $4,403 total is more expensive than Option G (MS-A2, $3,783) which has 10GbE, PCIe, and more cores
- No GPU path whatsoever
- RAM maxes at 64GB — same as cheaper Beelink options

**When GT15 Max makes sense**:
- Single-node AI workstation (not cluster use)
- Intel NPU is relevant for your workload (Lunar Lake has strong NPU for edge AI inference)
- You specifically need Intel platform compatibility

---

### Option I — Minisforum MS-S1 Max Cluster (AI Workstation)

**Configuration**: 3-node cluster of Minisforum MS-S1 Max — a high-end AI workstation with AMD Ryzen AI Max+ 395 (Strix Halo), 128GB LPDDR5x unified memory, and an iGPU with 40 CUs (equivalent to a discrete mid-range GPU). This is an extreme option at ~$9,800 for 3 nodes.

#### Hardware Specs

| Attribute | Value |
|-----------|-------|
| CPU | AMD Ryzen AI Max+ 395 (16C/32T, up to 5.1GHz, Zen 5) |
| RAM | **128GB LPDDR5x-8533 — soldered, not upgradeable** |
| iGPU | Radeon 8060S — 40 CUs, 128GB unified memory pool |
| Storage | 2× M.2 NVMe slots (PCIe 5.0 + PCIe 4.0) |
| GPU slot | PCIe 4.0 x16 physical / **x4 electrical** |
| Network | **2× 10GbE SFP+** + 1× 2.5GbE RJ45 |
| PSU | External DC brick |
| Unit price | ~$2,959 |

> **Critical caveat**: RAM is soldered LPDDR5x — you cannot add or replace it. The 128GB is a ceiling. The iGPU (Radeon 8060S with 40 CUs and full 128GB pool access) is the main differentiator for local LLM inference — it can run 70B parameter models in FP8 without a discrete GPU. However, at $2,959/node × 3 = $8,877 for just the hardware, this is a $9,800+ cluster. Better evaluated as a single-node AI workstation in a hybrid configuration.

#### Retailer Price Reference (Option I Key Components)

| Component | Amazon | eBay (new) | Newegg | Minisforum Direct | Best Price |
|-----------|--------|-----------|--------|-------------------|-----------|
| Minisforum MS-S1 Max (Ryzen AI Max+ 395, 128GB) | ~$2,959 | ~$2,800–2,959 | ~$2,999 | minisforum.com ~$2,959 | **$2,959** |
| Samsung 990 Pro 2TB NVMe (PCIe 5.0 slot) | ~$230 | ~$210–230 | ~$239 | samsung.com ~$245 | **$230** |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | ~$230 | ~$200–220 | ~$230 | mikrotik.com ~$230 | **$230** |

> **Note**: MS-S1 Max RAM is soldered LPDDR5x — not affected by the DDR5 SODIMM shortage. The 128GB is baked into the $2,959 unit price.

#### Full Cluster Parts List

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-S1 Max (Ryzen AI Max+ 395, 128GB LPDDR5x) | 3 | $2,959 | $8,877 |
| Samsung 990 Pro 2TB NVMe (VM storage) | 3 | $230 | $690 |
| 8-port 10GbE switch (MikroTik CRS309-1G-8S+IN) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$10,044** |

#### Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | Ryzen AI Max+ 395 (16C/32T, Zen 5, Strix Halo) |
| Total cores | 48 cores / 96 threads |
| RAM per node | **128GB LPDDR5x-8533 (soldered — fixed, not upgradeable)** |
| Total RAM | 384GB |
| iGPU per node | Radeon 8060S — 40 CUs, full 128GB memory pool access |
| Storage per node | 2× M.2 NVMe (PCIe 5.0 + PCIe 4.0) |
| Network | 2× 10GbE SFP+ + 2.5GbE per node |
| PCIe slot | PCIe 4.0 x16 physical / x4 electrical (single-slot only) |
| Idle power per node | ~45–55W |
| Total idle power | ~135–165W |
| Noise | <30 dB |
| Form factor | Mini PC |
| Rack format | Generic 1U shelf (same footprint as MS-A2 approximately) |
| Power cabling | External DC brick → NEMA 5-15 PDU strip |

**Annual electricity**: 150W × 8,760h × $0.13 = ~$170/year
**Savings vs current**: ~$890/year

**Advantages**:
- Radeon 8060S iGPU can run 70B LLM models in FP8 without any discrete GPU
- 128GB unified memory pool — iGPU and CPU share all 128GB; no VRAM limit
- Zen 5 16-core CPU with highest single-thread performance in this comparison
- 10GbE SFP+ for Ceph — full cluster storage capabilities

**Why a 3-node MS-S1 Max cluster is not recommended**:
- $10,044 total is 1.8× the cost of Option G (MS-A2) for equivalent cluster networking
- Soldered RAM cannot be upgraded or replaced if degraded
- PCIe slot is only x4 electrical — worse than MS-A2 (x8) for any PCIe add-on
- AI inference advantage is only meaningful on 1 node; the other 2 are wasted premium
- See Hybrid Option 2 for the recommended way to use the MS-S1 Max

---

### Option J — Refurbished 14th/15th Gen Dell Servers (Crisis-Era Value)

**Configuration**: 3-node cluster of refurbished Dell PowerEdge 14th gen servers — the **crisis-era best value** option. With DDR5 at $630+ per kit, refurbished servers with DDR4 ECC already installed become cost-competitive with new mini PC clusters.

`★ Insight ─────────────────────────────────────`
This option only makes economic sense **because** of the DDR5 crisis. In a normal DDR5 pricing environment (~$130/kit), the power and noise trade-offs would not be worth it. This is a bridge strategy: buy cheap capable hardware now, resell when DDR5 normalizes and mini PC clusters return to their "normal" economics.
`─────────────────────────────────────────────────`

#### 14th Gen Models (2017–2020)

| Model | Form | Sockets | Max RAM | PCIe Slots | Est. Refurb Price (128GB config) | Best Use |
|-------|------|---------|---------|-----------|----------------------------------|----------|
| R440 | 1U | 2 | 1TB | 2× LP | ~$589–800 | Entry 1U; limited PCIe |
| R540 | 2U | 2 | 1TB | 4× (2FH+2LP) | ~$600–900 | Budget 2U; 12× 3.5" storage bays |
| **R640** | **1U** | **2** | **3TB** | **3× LP** | **~$879–1,200** | **Best value 1U — 2× Gold 5218, 128GB DDR4, 8× 2.5" SFF** |
| R740 | 2U | 2 | 3TB | 8× (4FH+4LP) | ~$900–2,000 | GPU path — 4× FH PCIe 3.0 |
| R740xd | 2U | 2 | 3TB | 8× (4FH+4LP) | ~$713–1,500 | Storage beast — 12× LFF + 4× SFF bays |
| R840 | 2U | 4 | 6TB | 6× (4FH+2HH) | ~$2,000–5,000 | 4-socket density; expensive |
| R940 | 3U | 4 | 6TB | 8× | ~$2,000–4,000 | 4-socket; 80C/160T possible |

#### 15th Gen Models (2021–2023)

| Model | Form | Sockets | DDR Gen | Est. Refurb Price | Notes |
|-------|------|---------|---------|-------------------|-------|
| R450 | 1U | 2 | DDR4 | ~$2,900 | Entry 1U Ice Lake |
| R650 | 1U | 2 | DDR4 | ~$4,300 | Performance 1U |
| R650xs | 1U | 2 | DDR4 | ~$3,500–4,000 | Cost-optimized R650 |
| R750 | 2U | 2 | DDR4 | ~$4,300 | Full GPU; 2U |
| R750xs | 2U | 2 | DDR4 | ~$4,900 | Cost-optimized R750 |
| R860 | 2U | 4 | **DDR5** | ~$8,000+ | 4-socket Sapphire Rapids; **DDR5 still crisis pricing** |

> **15th gen is 3–5× the price of 14th gen refurbs.** Unless you need Ice Lake/SPR per-core perf, 14th gen is the value play for a bridge strategy.

#### Recommended Config: R640 Cluster (Best Value)

**Verified eBay listing (March 2026)**: 2× Gold 5218 (32C/64T), 128GB DDR4, H730P RAID, iDRAC9 Enterprise, dual 750W PSU — **$879/unit** free shipping.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Dell R640 refurb (2× Gold 5218, 128GB DDR4 ECC, 8× 2.5" SFF) | 3 | $879 | $2,637 |
| MikroTik CRS309-1G-8S+IN (10GbE via 10GbE NDC) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| **Total** | | | **~$2,907** |

> No JetKVM needed — iDRAC9 Enterprise provides full remote KVM, virtual media, and power control.

#### R640 Cluster Specs

| Metric | Value |
|--------|-------|
| Nodes | 3 |
| CPU per node | 2× Intel Xeon Gold 5218 (2× 16C/32T = 32C/64T, 2.3GHz base / 3.9GHz boost, Cascade Lake) |
| Total cores | 96 cores / 192 threads |
| RAM per node | 128GB DDR4-2933 ECC (included in purchase) |
| Total RAM | 384GB DDR4 ECC |
| Storage | 8× 2.5" SFF hot-swap bays per node (drives not included) |
| Network | 10GbE NDC (onboard Intel X710) + 1GbE management |
| PCIe | 3× LP PCIe 3.0 slots |
| PSU | Dual 750W Platinum hot-swap redundant |
| Remote management | **iDRAC9 Enterprise** — full remote KVM, virtual media, power API |
| Idle power per node | ~150W |
| Total idle power | ~450W |
| Noise | **40–55 dB** — enterprise fans |
| Form factor | 1U rack, 26" depth |
| Rack format | Standard 19" rails (included) |
| Power cabling | IEC C14 → rack PDU C13 (native) |

**Annual electricity**: 450W × 8,760h × $0.13 = ~$512/year
**Savings vs current**: ~$548/year

#### R740 Alternative (GPU Path)

The R740 (2U) has 4× full-height PCIe 3.0 slots vs R640's 3× LP only. For GPU passthrough, the R740 is the right 14th gen choice. Refurb R740 with 2× Gold 6132, 128GB DDR4 is ~$900–1,200 on eBay.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Dell R740 refurb (2× Gold 6132, 128GB DDR4 ECC) | 3 | $1,050 | $3,150 |
| MikroTik CRS309-1G-8S+IN | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| **Total** | | | **~$3,420** |

#### Why Option J Is the Crisis-Era Value Play

- **$2,907 cluster** — cheaper than every mini PC option at 64GB except none; beats Option A ($3,701), Option B ($3,559), and all hybrids at 64GB
- **128GB/node included** in purchase — no $630/kit DDR5 purchase required
- **iDRAC9 Enterprise** — saves $207 on JetKVM and provides IPMI power control
- **10GbE NDC onboard** — Ceph-ready out of the box; no switch upgrade needed
- **2× per-core perf vs current fleet** — Gold 5218 vs Sandy Bridge E5; still a meaningful upgrade

#### Why Option J Is Not the Long-Term Answer

- **Noise**: 40–55 dB — same enterprise fan problem as current servers; not tolerable in a living space
- **Power**: ~150W/node idle → ~$512/year electricity (vs ~$85 for Option B)
- **DDR4**: 2666–2933 MT/s bandwidth (2–3× slower than DDR5-5600)
- **PCIe 3.0**: Limits GPU and NVMe performance ceiling
- **End of life**: No CPU upgrade path; next hardware refresh means full replacement

**Recommended use**: Bridge strategy — buy R640 cluster now ($2,907) to replace noisy 2009–2012 servers, save $548/year on electricity, then resell when DDR5 normalizes (late 2027) and transition to Option B or G mini PC cluster.

---

## Hybrid Cluster Configurations

Not every node in a Proxmox cluster needs to be identical. Mixed configurations let you assign roles — one node handles GPU/AI inference while others provide compute and Ceph storage — reducing cost versus buying 3 premium nodes.

> **Proxmox compatibility note**: All nodes in a cluster must reach the same corosync/management subnet. Mixing 10GbE and 2.5GbE nodes is possible — use 10GbE for Ceph replication between 10GbE nodes and 2.5GbE for VM traffic on the budget nodes. The only hard requirement is that Ceph OSDs are on nodes that can reach each other at ≥10GbE.

---

### Hybrid 1 — GPU Node + Compute Nodes (MS-A2 + 2× SER9 Max)

**Concept**: One MS-A2 serves as the AI/GPU node (PCIe x8 slot for GPU passthrough + Ollama). Two SER9 Max nodes handle VM compute. All three share 10GbE for Ceph.

> **Crisis-era note**: SER9 Max compute nodes use the 64GB/1TB pre-configured SKU at $779 — buying factory 64GB is significantly cheaper than 32GB unit + $630 SODIMM upgrade.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-A2 barebone (GPU/AI node) | 1 | $799 | $799 |
| Crucial 64GB DDR5 SODIMM (MS-A2) | 1 | $630 | $630 |
| Samsung 990 Pro 2TB NVMe (MS-A2 VM storage) | 1 | $230 | $230 |
| Beelink SER9 Max **64GB/1TB configured** (compute nodes) | 2 | $779 | $1,558 |
| Samsung 990 Pro 2TB NVMe (SER9 Max ×2, 2nd M.2) | 2 | $230 | $460 |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$4,154** |

**Cluster summary**: 3 nodes, ~40 cores/80 threads, 192GB RAM, 10GbE Ceph, 1× PCIe x8 GPU node
**Annual electricity**: ~85W × 8,760h × $0.13 = ~$97/year

**Best for**: Adding GPU inference to an otherwise SER9 Max cluster without paying for 3× MS-A2. The AI node runs Ollama; all 8 agent VMs call its endpoint over the 10GbE fabric.

---

### Hybrid 2 — AI Workstation + Cluster (1× MS-S1 Max + 2× MS-A2)

**Concept**: One MS-S1 Max provides the massive iGPU + 128GB unified memory for LLM inference. Two MS-A2 nodes provide Zen 5 compute and form the Ceph quorum.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-S1 Max (AI inference node) | 1 | $2,959 | $2,959 |
| Samsung 990 Pro 2TB NVMe (MS-S1 VM storage) | 1 | $230 | $230 |
| Minisforum MS-A2 barebone (compute nodes) | 2 | $799 | $1,598 |
| Crucial 64GB DDR5 SODIMM (MS-A2 ×2) | 2 | $630 | $1,260 |
| Samsung 990 Pro 2TB NVMe (MS-A2 ×2) | 2 | $230 | $460 |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$6,984** |

**Cluster summary**: 3 nodes, ~48 cores/96 threads, 256GB RAM (128 soldered + 128 SODIMM), 10GbE Ceph, Radeon 8060S iGPU
**Annual electricity**: ~120W × 8,760h × $0.13 = ~$136/year

**Best for**: The highest LLM inference capability in a mini PC cluster. The MS-S1 Max's 128GB unified memory pool lets it run 70B models without discrete GPU hardware. The two MS-A2 nodes handle all agent VMs and Ceph storage.

---

### Hybrid 3 — Budget + Expansion (1× MS-01 + 2× SER8)

**Concept**: One MS-01 as the capable node (10GbE, PCIe slot), two SER8 as cheap compute. The SER8 nodes only have 2.5GbE so Ceph is limited to the MS-01 — use local-lvm storage per node or run PBS on the MS-01.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| Minisforum MS-01 barebone (i9-13900H) | 1 | $539 | $539 |
| Crucial 64GB DDR5 SODIMM (MS-01) | 1 | $630 | $630 |
| Samsung 990 Pro 2TB NVMe (MS-01, 2× slots) | 2 | $230 | $460 |
| Beelink SER8 (compute nodes) | 2 | $479 | $958 |
| Crucial 64GB DDR5 SODIMM (SER8 ×2) | 2 | $630 | $1,260 |
| 8-port 2.5GbE switch (TRENDnet TEG-S380) | 1 | $122 | $122 |
| CAT6 patch cables | 1 | $15 | $15 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$4,191** |

**Cluster summary**: 3 nodes, ~30 cores/52 threads, 192GB RAM, 2.5GbE (no Ceph), 1× PCIe 4.0 x4 on MS-01 node
**Annual electricity**: ~60W × 8,760h × $0.13 = ~$68/year

**Best for**: Lowest-cost path to a functional cluster with a GPU upgrade path. The MS-01 node holds a single-slot LP GPU for Ollama. SER8 nodes run the agent VMs. No Ceph — local-lvm storage per node, Proxmox Backup Server on MS-01.

---

### Hybrid 4 — Rack-Native Mixed (1× MS-02 Ultra + 2× MS-A2)

**Concept**: One MS-02 Ultra as the premium GPU/AI node (PCIe 5.0 x16, IEC C14 native, 256GB ECC RAM). Two MS-A2 nodes provide Zen 5 compute and 10GbE Ceph. All three share the 10GbE fabric.

| Item | Qty | Unit Price | Total |
|------|-----|-----------|-------|
| MS-02 Ultra barebone (Core Ultra 9 285HX) | 1 | $1,199 | $1,199 |
| 128GB DDR5 ECC SODIMM (MS-02) | 1 | $1,300 | $1,300 |
| Samsung 990 Pro 2TB NVMe (MS-02) | 1 | $230 | $230 |
| Minisforum MS-A2 barebone (Ryzen 9 9955HX, ×2) | 2 | $799 | $1,598 |
| Crucial 64GB DDR5 SODIMM (MS-A2 ×2) | 2 | $630 | $1,260 |
| Samsung 990 Pro 2TB NVMe (MS-A2 ×2) | 2 | $230 | $460 |
| MikroTik CRS309-1G-8S+IN (8-port 10GbE) | 1 | $230 | $230 |
| SFP+ DAC cables (3-pack) | 1 | $40 | $40 |
| JetKVM (remote KVM access) | 3 | $69 | $207 |
| **Total** | | | **~$6,524** |

**Cluster summary**: 3 nodes, ~56 cores, 256GB RAM (128GB ECC + 2×64GB), 10GbE Ceph, PCIe 5.0 x16 on MS-02 node
**Annual electricity**: ~115W × 8,760h × $0.13 = ~$131/year

**Best for**: A balanced premium cluster where the MS-02 Ultra anchors the rack (IEC C14, full dual-slot GPU) and the MS-A2 nodes provide high-core-count Zen 5 compute. Power cabling is mixed — MS-02 goes direct to C13 PDU, MS-A2 nodes need NEMA brick adapters.

---

## Buy Now vs Wait Analysis

Current electricity cost: ~$1,060/year. DDR5 prices are projected to normalize by late 2027. Should you buy now at crisis prices, or wait for DDR5 to return to normal (~$150–200 for 64GB SODIMM)?

### The Math

**Electricity cost of waiting 18 months** (to ~Q3 2027):
```
$1,060/year × 1.5 years = $1,590
```

**Potential DDR5 savings if you wait** (normalized pricing per cluster):
| Option | Current RAM Cost | Normalized RAM (~2027) | Savings |
|--------|-----------------|------------------------|---------|
| 64GB SODIMM cluster (3 kits) | 3 × $630 = $1,890 | 3 × $175 = $525 | **~$1,365** |
| 128GB UDIMM cluster (3 kits) | 3 × $1,243 = $3,729 | 3 × $350 = $1,050 | **~$2,679** |
| 128GB ECC SODIMM cluster (3 kits) | 3 × $1,300 = $3,900 | 3 × $450 = $1,350 | **~$2,550** |

### By Option

| Option | Buy Now Total | Electricity Cost of Waiting | RAM Savings from Waiting | Net Cost of Waiting |
|--------|--------------|---------------------------|--------------------------|----------------------|
| A (3× SER8, 64GB SODIMM) | $3,701 | +$1,590 | -$1,365 | **+$225 more expensive to wait** |
| B (3× SER9 Max, 64GB configured) | $3,559 | +$1,590 | -$0 (factory RAM) | **+$1,590 more expensive to wait** |
| G (3× MS-A2, 64GB SODIMM) | $5,454 | +$1,590 | -$1,365 | **+$225 more expensive to wait** |
| D (3× MS-02 Ultra, 128GB ECC SODIMM) | $9,034 | +$1,590 | -$2,550 | **-$960 cheaper to wait** |
| F1 (3× DIY 2U, 128GB UDIMM) | $7,815 | +$1,590 | -$2,679 | **-$1,089 cheaper to wait** |
| F2 (3× ASRock Rack, 128GB ECC UDIMM) | $9,651 | +$1,590 | -$2,679 | **-$1,089 cheaper to wait** |
| J (3× R640 refurb) | $2,907 | +$1,590 | -$0 (DDR4 included) | **+$1,590 more expensive to wait** |

### Verdict

**Buy now** (electricity cost of waiting > RAM savings):
- Option A, B, G, all Hybrids — the $1,590 electricity cost of running old servers exceeds the RAM savings you'd realize in 18 months
- Option J — buying a bridge refurb cluster now saves electricity immediately; RAM is not a variable
- Option E (R360), H (GT15 Max), I (MS-S1 Max) — RAM is in unit price; waiting only costs electricity

**Waiting is economically rational for**:
- Options D, F1, F2 — these require 128GB kits where the DDR5 premium is $2,550–2,679, exceeding the 18-month electricity cost by $1,000+

**Hybrid strategy** (recommended):
1. **Buy R640 refurb cluster now** ($2,907) — replace noisy 2009-era servers, save electricity, maintain full functionality
2. **Wait 18–24 months** for DDR5 to normalize
3. **Sell R640 cluster** (~$1,500–2,000 on eBay in 2027–2028) and **buy Option G or B mini PC cluster** at normalized DDR5 prices (~$3,000–3,500)

Net cost of hybrid strategy: ~$1,000–1,500 after resale, vs spending $5,000–9,000 today on a mini PC cluster with crisis-priced RAM.

---

## Additional Mini PCs Evaluated

These candidates were researched but don't warrant full standalone option write-ups. They represent either redundant options to existing ones, older silicon, or configurations with limiting weaknesses.

| Model | CPU | Max RAM | 2nd NVMe | Networking | Est. Price | Verdict |
|-------|-----|---------|----------|-----------|-----------|---------|
| GMKtec NucBox K8 Plus | Ryzen 7 8845HS (8C, Zen 4) | 96GB DDR5 | Yes | 2× 2.5GbE | $425–660 | Good budget option; no 10GbE limits cluster use. Cheaper than SER8 with more RAM capacity. |
| Minisforum UM890 Pro | Ryzen 9 8945HS (8C, Zen 4) | 96GB DDR5 | Yes (OCuLink) | 2× 2.5GbE | $479–650 | OCuLink eGPU port is interesting for GPU passthrough, but no 10GbE disqualifies it for Ceph. |
| ASUS NUC 14 Pro+ | Core Ultra 9 185H (6P+8E, 14C) | 64GB DDR5 | Yes | 2× 2.5GbE | $700–1,000 | Premium ASUS build quality; Intel vPro AMT management. But no 10GbE and lower max RAM than MS-A2. |
| GEEKOM A8 | Ryzen 9 8945HS (8C, Zen 4) | 64GB DDR5 | Yes | 2× 2.5GbE | $500–650 | Similar to UM890 Pro; good daily driver but not suited for cluster networking. |
| HP Elite Mini 800 G9 | i9-12900T (16C, 12th gen) | 64GB DDR5 | Yes | 1× 1GbE | $300–515 (refurb) | Lowest cost path to 16-core node. 1GbE only and Intel 12th gen make this a budget curiosity, not a cluster choice. |
| Lenovo ThinkCentre M75q Gen 5 | Ryzen PRO 7 8700GE (8C, Zen 4) | 64GB DDR5 | Yes | 1× 1GbE | $400–700 | Enterprise manageability (vPro-equivalent), good build quality. 1GbE eliminates it as a cluster node. |

### Key Findings from Additional Research

**Common pattern**: Most mini PCs in the $400–700 range max out at dual 2.5GbE networking. This is fine for a budget cluster where Ceph is not required (Options A/Hybrid 3 territory), but it means live VM migration is slow and no distributed storage.

**The 10GbE divide**: Only the Beelink SER9 Max, Minisforum MS-01/MS-A2, MS-S1 Max, and MS-02 Ultra have native 10GbE in this price range. All other mini PCs require an external PCIe 10GbE adapter — which requires a PCIe slot (which most of them don't have).

**GMKtec K8 Plus as budget alternative to SER8**: At ~$425 configured, the K8 Plus undercuts the SER8 ($449) with higher max RAM (96GB vs 64GB). If you need the RAM headroom and can live with 2.5GbE, it's worth considering over the SER8 for Option A.

---

## Comparison Tables

### Full Option Comparison

| | **Option A** | **Option B** | **Option C** | **Option D** | **Option E** | **Option F** | **Option G** | **Option H** | **Option I** | **Option J** |
|---|---|---|---|---|---|---|---|---|---|---|
| **Hardware** | Beelink SER8 | Beelink SER9 Max | Minisforum MS-01 | Minisforum MS-02 Ultra | Dell R360 | DIY 2U (RM23-502) | Minisforum MS-A2 | GEEKOM GT15 Max | Minisforum MS-S1 Max | Dell R640 (refurb) |
| **CPU per node** | Ryzen 7 8745HS (8C, Zen 4) | Ryzen 7 H255 (8C, Zen 5) | i9-13900H (14C, 13th gen) | Core Ultra 9 285HX (24C, Arrow Lake) | Xeon E-2474G (8C) | Ryzen 9 9900X (12C, Zen 5) | **Ryzen 9 9955HX (16C, Zen 5)** | Core Ultra 9 285H (16C, Lunar Lake) | Ryzen AI Max+ 395 (16C, Zen 5) | 2× Gold 5218 (32C, Cascade Lake) |
| **Total cores** | 24C / 48T | 24C / 48T | 42C / 60T | 72C / 72T | 24C / 48T | 36C / 72T | **48C / 96T** | 48C / 66T | 48C / 96T | **96C / 192T** |
| **Max RAM / node** | 64GB DDR5 | 64GB DDR5 | 96GB DDR5 | **256GB ECC DDR5** | 128GB DDR5 | 128GB DDR5 UDIMM | 96GB DDR5 | 64GB DDR5 | **128GB LPDDR5x (soldered)** | **3TB DDR4 ECC** |
| **RAM in cluster (parts list)** | 192GB | 192GB | 192GB | 384GB | 192GB | 384GB | 192GB | 96GB | 384GB | **384GB (included)** |
| **PCIe slot** | None | None | PCIe 4.0 x4 (LP) | **PCIe 5.0 x16** (dual-slot) | PCIe 4.0 x8 | 4–7 LP + riser | PCIe 4.0 x16 / **x8 elec.** (LP) | **None** | PCIe 4.0 x16 / x4 elec. (LP) | 3× LP PCIe 3.0 |
| **GPU capable?** | No | No | Single-slot LP | Yes (RTX 4060 Ti LP) | Single-width (A2) | LP; full-height via riser | Single-slot LP (better than MS-01) | **No** | Single-slot LP only | LP only (PCIe 3.0) |
| **iGPU for LLM?** | No | No | No | No | No | No | No | Partial (Arc Xe) | **Yes — Radeon 8060S 40CU, 128GB pool** | No |
| **Network** | 2.5GbE | 10GbE | 2× 10GbE SFP+ | 2× 25GbE SFP28 + 10GbE | 2× 10GbE | 10GbE PCIe NIC | **2× 10GbE SFP+** | **2× 2.5GbE only** | 2× 10GbE SFP+ | **10GbE NDC onboard** |
| **Ceph capable?** | No | Yes | Yes | Yes | Yes | Yes | Yes | **No** | Yes | Yes |
| **PSU / power in** | DC brick | DC brick | DC brick | **Internal 350W, IEC C14** | Hot-swap, IEC C14 | **ATX, IEC C14** | DC brick | DC brick | DC brick | **Dual hot-swap, IEC C14** |
| **Noise** | <30 dB | <30 dB | <30 dB | ≤36 dB | **40–55 dB** | ~25–35 dB | <30 dB | <30 dB | <30 dB | **40–55 dB** |
| **Idle power (cluster)** | ~45W | ~75W | ~90W | ~110W | ~210W | ~120W | ~97W | ~120W | ~150W | **~450W** |
| **Rack format** | 1U shelf | 1U shelf | racknex 1.33U–2U | racknex 2.33U | Standard 1U | 2U rails × 3 = 6U | racknex (same as MS-01) | 1U shelf | 1U shelf | **Standard 1U rails** |
| **iDRAC/IPMI** | No (JetKVM) | No (JetKVM) | No (JetKVM) | No (JetKVM) | Yes (built-in) | No (JetKVM / F2 has IPMI) | No (JetKVM) | No (JetKVM) | No (JetKVM) | **Yes — iDRAC9 Enterprise** |
| **Total cost** | ~$3,701 | ~$3,559 | ~$6,154 | ~$9,034 (no GPU) | ~$6,330 | ~$7,815 (F1) / ~$9,651 (F2) | ~$5,454 | ~$4,694 | ~$10,044 | **~$2,907** |

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
| **Option G (3× MS-A2)** | 48C / 96T | 192–288GB | **~5.5×** | Gen4 |
| **Option H (3× GT15 Max)** | 48C / 66T | 96–192GB | **~5×** | Gen4 |
| **Option I (3× MS-S1 Max)** | 48C / 96T | 384GB (soldered) | **~5.5×** | Gen5/4 |
| **Hybrid 1 (MS-A2 + 2× SER9 Max)** | 40C / 80T | 192GB | **~5×** | Gen4 |
| **Hybrid 2 (MS-S1 Max + 2× MS-A2)** | 48C / 96T | 256GB | **~5.5×** | Gen5/4 |
| **Hybrid 4 (MS-02 Ultra + 2× MS-A2)** | 56C / 88T | 256GB | **~5.5×** | Gen5/4 |

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
| **Option G (3× MS-A2)** | ~97W | ~$110 | <30 dB | ~4U (racknex) |
| **Option H (3× GT15 Max)** | ~120W | ~$136 | <30 dB | ~1U shelf |
| **Option I (3× MS-S1 Max)** | ~150W | ~$170 | <30 dB | ~2U shelf |
| **Option J (3× R640 refurb)** | ~450W | ~$512 | 40–55 dB | 3U (1U each) |
| **Hybrid 1 (MS-A2 + 2× SER9 Max)** | ~85W | ~$97 | <30 dB | ~1–2U |
| **Hybrid 2 (MS-S1 Max + 2× MS-A2)** | ~120W | ~$136 | <30 dB | ~2U |
| **Hybrid 3 (MS-01 + 2× SER8)** | ~60W | ~$68 | <30 dB | ~2U |
| **Hybrid 4 (MS-02 Ultra + 2× MS-A2)** | ~115W | ~$131 | <30–36 dB | ~4U mixed |

### Cost Comparison (net of resale)

> **Note**: All prices reflect March 2026 DDR5 crisis pricing. See [DDR5 Pricing Crisis](#ddr5-pricing-crisis--march-2026) and [Buy Now vs Wait Analysis](#buy-now-vs-wait-analysis) for context.

| Setup | Hardware Cost | Est. Resale | Net Cost | Annual Power Savings |
|-------|--------------|-------------|----------|----------------------|
| **Option J (R640 refurb)** | ~$2,907 | $1,500–$3,700 | **-$793 to +$1,407** | ~$548/yr |
| **Option A (SER8 64GB)** | ~$3,701 | $1,500–$3,700 | **+$1 to +$2,201** | ~$1,009/yr |
| **Option B (SER9 Max 64GB configured)** | ~$3,559 | $1,500–$3,700 | **-$141 to +$2,059** | ~$975/yr |
| **Option C (MS-01 64GB)** | ~$6,154 | $1,500–$3,700 | **$2,454–$4,654** | ~$958/yr |
| **Option D (MS-02 Ultra 128GB ECC)** | ~$9,034 | $1,500–$3,700 | **$5,334–$7,534** | ~$935/yr |
| **Option E (R360)** | ~$6,330 | $1,500–$3,700 | **$2,630–$4,830** | ~$821/yr |
| **Option F1 (DIY 2U 128GB)** | ~$7,815 | $1,500–$3,700 | **$4,115–$6,315** | ~$924/yr |
| **Option F2 (ASRock Rack 128GB ECC)** | ~$9,651 | $1,500–$3,700 | **$5,951–$8,151** | ~$924/yr |
| **Option G (MS-A2 64GB)** | ~$5,454 | $1,500–$3,700 | **$1,754–$3,954** | ~$950/yr |
| **Option H (GT15 Max)** | ~$4,694 | $1,500–$3,700 | **$994–$3,194** | ~$924/yr |
| **Option I (MS-S1 Max 128GB soldered)** | ~$10,044 | $1,500–$3,700 | **$6,344–$8,544** | ~$890/yr |
| **Hybrid 1 (MS-A2 + 2× SER9 Max 64GB)** | ~$4,154 | $1,500–$3,700 | **$454–$2,654** | ~$963/yr |
| **Hybrid 2 (MS-S1 Max + 2× MS-A2)** | ~$6,984 | $1,500–$3,700 | **$3,284–$5,484** | ~$924/yr |
| **Hybrid 3 (MS-01 + 2× SER8 64GB)** | ~$4,191 | $1,500–$3,700 | **$491–$2,691** | ~$992/yr |
| **Hybrid 4 (MS-02 Ultra + 2× MS-A2 64GB)** | ~$6,524 | $1,500–$3,700 | **$2,824–$5,024** | ~$929/yr |

> At crisis DDR5 pricing, **Option J (R640 refurb, $2,907)** and **Option B (SER9 Max 64GB configured, $3,559)** are the two cheapest paths. Option J is the cheapest absolute buy — but it retains the noise and power trade-offs of enterprise servers. Option B is the cheapest quiet mini PC cluster with 10GbE Ceph. Option G (MS-A2) at $5,454 is the most capable 10GbE cluster with PCIe GPU path.

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

> All prices reflect March 2026 DDR5 crisis pricing. See [Buy Now vs Wait Analysis](#buy-now-vs-wait-analysis) before deciding.

| Priority | Best Choice | Why |
|----------|-------------|-----|
| **Lowest absolute cost (crisis pricing)** | **Option J (R640 refurb)** | $2,907 — DDR4 ECC included, iDRAC9 built-in. Bridge strategy: replace now, resell in 2027 |
| **Lowest cost quiet mini PC cluster** | **Option B (SER9 Max 64GB configured)** | $3,559 — 64GB/1TB factory SKU avoids $630 SODIMM purchase; 10GbE Ceph |
| **Lowest power / quietest** | Option A (SER8) | ~45W idle, near-silent; but $3,701 due to crisis DDR5 |
| **Best balance of cost + networking** | **Option B (SER9 Max)** | 10GbE Ceph, Zen 5, $3,559 — now cheaper than Option A at 64GB |
| **Best new cluster node (2026 recommendation, budget unlimited)** | **Option G (MS-A2)** | Zen 5 16C, dual 10GbE SFP+, PCIe x8 GPU slot, ServeTheHome's top pick — $5,454 |
| **Best bridge strategy** | **Option J → Option B/G** | Buy R640 now ($2,907), wait for DDR5 normalization, resell and upgrade in 2027–2028 |
| **GPU inference (single-slot, budget)** | Option C (MS-01) or **Option G (MS-A2)** | MS-A2 has x8 electrical vs MS-01's x4; better GPU bandwidth same form factor |
| **GPU inference (full dual-slot GPU)** | Option D (MS-02 Ultra) | PCIe 5.0 x16 supports RTX 4060 Ti LP or better; 256GB ECC RAM — but $9,034 at crisis prices |
| **LLM on iGPU (no discrete GPU needed)** | **Hybrid 2 (MS-S1 Max + 2× MS-A2)** | Radeon 8060S with 128GB unified pool runs 70B models; $6,984 is the right way to use MS-S1 Max |
| **Rack-native power cabling (no bricks)** | Option D (MS-02 Ultra) | Only mini PC with internal IEC C14 PSU |
| **iDRAC/IPMI + hot-swap PSU** | Option J (R640 refurb) or Option E (R360) | iDRAC9 Enterprise built-in; J is far cheaper ($2,907 vs $6,330) |
| **Maximum RAM capacity** | Option D (MS-02 Ultra) | 256GB ECC DDR5 per node (768GB cluster) — but $9,034 total at crisis pricing |
| **Maximum flexibility / repairability** | Option F1 (DIY 2U) | Standard desktop parts, AM5 socket, any component individually replaceable |
| **IPMI + GPU + desktop CPU (server-grade)** | Option F2 (ASRock Rack) | IPMI/BMC + PCIe 5.0 x16 + AM5 Zen 5; but $9,651 at crisis DDR5 pricing |
| **Lowest cost cluster with GPU path** | **Hybrid 1 (MS-A2 + 2× SER9 Max)** | $4,154 — MS-A2 holds GPU, SER9 Max nodes have 10GbE Ceph; better networking than Hybrid 3 |

### Key Trade-offs at a Glance

**Option J vs A/B/G**: The R640 refurb at $2,907 is cheaper than any mini PC option at 64GB. But it runs at ~450W (vs ~45–97W for mini PCs) and produces 40–55 dB noise. This is a bridge strategy — not a permanent home for quiet home lab hardware.

**Option A vs B (at crisis prices)**: Option B (SER9 Max 64GB configured) at $3,559 is now *cheaper* than Option A (SER8 + 64GB SODIMM upgrade) at $3,701. The 10GbE networking is now essentially free compared to the alternative. Always choose B over A.

**Option B vs G**: Option G (MS-A2) at $5,454 costs ~$1,900 more than Option B for a 3-node cluster. You get: 16C vs 8C, PCIe x8 GPU slot, 96GB max RAM. If GPU inference is on your roadmap at all, the extra cost is worth it. If you only need 8 VMs with no GPU plans, Option B is the better buy.

**Option B vs C**: At crisis prices, MS-01 (Option C) is $6,154 vs SER9 Max (Option B) at $3,559. That's $2,595 more for a PCIe x4 slot and faster Intel CPU. The economics favor Option B over C unless you're committed to GPU inference.

**Option C vs D**: At crisis prices, MS-02 Ultra (Option D) is $9,034 vs MS-01 (Option C) at $6,154. The $2,880 premium buys PCIe 5.0 x16 (vs x4), 256GB ECC RAM, 25GbE, and no external power brick. Only justified if full dual-slot GPU passthrough is a hard requirement.

**Option D vs E**: Server-class hardware (R360, $6,330) is cheaper than MS-02 Ultra ($9,034) at crisis DDR5 prices. However, R360 is louder, uses 2× more power, and has inferior per-core performance. For a home lab, R360 is not recommended over R640 refurb (Option J) or any mini PC option.

**Option D vs F1**: At crisis prices, MS-02 Ultra ($9,034) and DIY F1 ($7,815) are close. F1 wins on cost ($1,200 savings), PCIe flexibility (multiple slots), and AM5 upgrade path. MS-02 Ultra wins on 256GB ECC RAM and 25GbE networking. F1 is the better value at crisis pricing.

**Option E vs F2**: The Dell R360 at ~$6,330 gives you Xeon E-2474G (8C) + iDRAC9 + hot-swap PSU. The ASRock Rack F2 at ~$9,651 gives you Ryzen 9 9900X (12C) + IPMI/BMC + PCIe 5.0 x16. At crisis prices, both are expensive. Neither is recommended over Option J (R640 refurb) for a bridge strategy.

### Key Trade-offs: New Options

**Option G (MS-A2) vs Option C (MS-01)**: The MS-A2 is now $799 (dropped from $839 at launch) vs MS-01 at $539. At crisis DDR5 prices where RAM dominates the cost, the $260/node barebone premium for MS-A2 is easier to justify — you get Zen 5 16C vs 13th gen Intel 14C, PCIe x8 vs x4. Use MS-01 only if you find it heavily discounted.

**Option G (MS-A2) vs Option B (SER9 Max)**: At crisis prices, Option G is $5,454 vs Option B at $3,559 — a $1,895 gap. In normal pricing, this gap was ~$400. The DDR5 premium makes Option B relatively more attractive than before. Choose G only if GPU inference is a definite plan.

**Option H (GT15 Max) vs Option G (MS-A2)**: At crisis prices, H is $4,694 vs G at $5,454 — H is now cheaper. But GT15 Max still has no 10GbE and no PCIe. Option B (SER9 Max, $3,559) still beats H on both cost and networking. There is no scenario where GT15 Max is the right cluster choice.

**Option I (MS-S1 Max) as a cluster**: Three MS-S1 Max units at $10,044 is extremely expensive. The iGPU LLM advantage only helps on 1 node; the other 2 are wasteful. Buy 1× MS-S1 Max as the AI node and pair it with 2× MS-A2 for compute (Hybrid 2, $6,984).

**Option J (R640 refurb) as a bridge**: At $2,907 with 96C/192T and 384GB DDR4 ECC, Option J is the cheapest functional cluster. It is not quiet (~50 dB) and not power efficient (~$512/year). Ideal as a 12–18 month bridge strategy while waiting for DDR5 prices to normalize.

### Action Items

1. **Confirm r820 RAM** — SSH in and verify the 384GB measurement: `free -h`. If confirmed, list on eBay immediately at $1,200–1,500 with RAM. This server funds most of the upgrade regardless of which path you choose.

2. **Decide: buy now or wait for DDR5 normalization** — See [Buy Now vs Wait Analysis](#buy-now-vs-wait-analysis):
   - **Buy now** if noise and electricity costs are the priority: Options B, J
   - **Wait** if you want 128GB per node and can tolerate current servers another 18 months: Options D, F1, F2
   - **Hybrid bridge strategy**: Buy Option J (R640 refurb, $2,907) now, wait for DDR5, then upgrade

3. **Decide on GPU / LLM path** — If local Ollama is a goal:
   - 70B model support → Hybrid 2 (MS-S1 Max + 2× MS-A2, $6,984)
   - Smaller models (7B–13B) → Option G (MS-A2, $5,454) with RTX 3050 LP added later
   - No GPU needed → Option B (SER9 Max 64GB configured, $3,559)

4. **Crisis-era default recommendation**: **Option B (SER9 Max 64GB/1TB configured cluster)** at **~$3,559**. The 64GB factory SKU at $779/unit avoids the $630 SODIMM purchase. 10GbE Ceph, Zen 5 8-core, near-silent. Best combination of cost and capability at March 2026 pricing.

5. **If noise is not a constraint**: **Option J (R640 refurb cluster)** at **~$2,907** is the absolute cheapest path. 96C/192T, 384GB DDR4 ECC, iDRAC9 built-in, Ceph-ready. Treat as a bridge until DDR5 normalizes.

6. **Decide on rack vs shelf** — Options B/G/J all have clean rack solutions (1U shelf for B, racknex for G, standard rails for J). Options A/H need brick adapters.

7. **Order hardware** — R640 refurb units: search eBay for "Dell R640 2× Gold 5218 128GB". Mini PC units: Amazon Prime 2–5 days; MS-A2 from Minisforum direct 1–2 weeks.

8. **Keep the NVMe drives** — Pull all 5 WD SN750 1TB drives before selling servers. They fit directly in mini PC M.2 slots and are worth ~$350 total. (Not needed for Option J — R640 uses SAS bays.)

---

*Analysis based on SSH inspection (Feb 28, 2026), repository review, and multi-source market pricing as of March 2026. Prices sourced from Amazon, eBay, Newegg, Best Buy, B&H, Micro Center, Walmart, and manufacturer direct. DDR5 pricing reflects the 2024–2026 global memory shortage; all DDR5 prices verified March 2026 against Amazon, Best Buy, and Micro Center. Refurbished server prices verified against active eBay listings. All prices vary; verify before purchasing.*
