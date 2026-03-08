# Hardware Inventory — Home Lab Proxmox Cluster

**Collected**: 2026-03-08
**Method**: Ansible playbook (`ansible/hardware_inventory.yml`) — pvesh API + dmidecode + smartctl
**Hosts surveyed**: r420, r8202, r820 (r720xd **offline/unreachable** at time of collection)

---

## Summary Comparison Table

| | **r420** | **r8202** | **r820** | **r720xd** |
|---|---|---|---|---|
| Model | PowerEdge R420 | PowerEdge R820 | PowerEdge R820 | PowerEdge R720xd |
| Service Tag | F8QXX12 | 5DZXBW1 | G1J77Y1 | (not collected) |
| BIOS | 2.9.0 (2020-01-09) | 2.7.0 (2020-01-07) | 2.7.0 (2020-01-07) | — |
| CPU | 2× Xeon E5-2420 v2 | 2× Xeon E5-4650 | 4× Xeon E5-4650 | — |
| Cores / Threads | 12c / 24t | 16c / 32t | 32c / 64t | — |
| RAM | 70.7 GB DDR3 ECC | 51.0 GB DDR3 ECC | 377.8 GB DDR3 ECC | — |
| DIMM slots (used/total) | 12/12 | 13/24 | 48/48 | — |
| NVMe | WD Black SN770 1TB | WD Black SN750 SE 1TB | WD Black SN750 SE 1TB | — |
| SAS pool | raidz1 × 3× ~931G = 2.72 TB | None | raidz2 × 8× ~931G = 7.27 TB | — |
| RAID controller | PERC H710P | PERC H710 | PERC H710P | — |
| NICs | 2× BCM5720 (4× 1GbE) | 2× BCM5720 (4× 1GbE) | 2× BCM5720 (4× 1GbE) | — |
| GPU | Matrox G200eR2 (BMC only) | Matrox G200eR2 (BMC only) | Matrox G200eR2 (BMC only) | — |
| Cluster IP | 10.220.1.7 | 10.220.1.8 | 10.220.1.11 | 10.220.1.10 |

> **Note**: r8202 is the Ansible hostname alias for a Dell PowerEdge R820 (service tag 5DZXBW1), not an "R8202" model.

---

## Per-Server Detail

### r420.infiquetra.com — Dell PowerEdge R420

**Identity**
- Model: Dell PowerEdge R420 (2U, 2-socket)
- Service Tag: `F8QXX12`
- BIOS: 2.9.0 released 2020-01-09

**CPU**
- 2× Intel Xeon E5-2420 v2 @ 2.20 GHz
- 6 cores per socket → **12 cores / 24 threads total**
- Microarchitecture: Ivy Bridge-EP (LGA 1356)

**Memory**
- Total: **70.7 GB DDR3 ECC Registered**
- 12 DIMM slots — all 12 populated (no expansion headroom)
- Mix of 8 GB @ 1333 MT/s and 4 GB @ 1066 MT/s modules
- Manufacturers: Samsung, Micron, Kingston

**Storage**

| Device | Model | Size | Type | Notes |
|--------|-------|------|------|-------|
| /dev/nvme0n1 | WD_BLACK SN770 1TB | 1000 GB | NVMe M.2 | SMART: PASSED |
| /dev/sda | (PERC H710P virtual disk) | 999.7 GB | SAS logical | Cannot query — behind MegaRAID |
| /dev/sdb | (PERC H710P virtual disk) | 999.7 GB | SAS logical | In `sas-data` raidz1 |
| /dev/sdc | (PERC H710P virtual disk) | 999.7 GB | SAS logical | In `sas-data` raidz1 |
| /dev/sdd | (PERC H710P virtual disk) | 999.7 GB | SAS logical | In `sas-data` raidz1 |

**ZFS Pools**

| Pool | Config | Raw | Usable | Used | Health |
|------|--------|-----|--------|------|--------|
| nvme-fast | Single NVMe | 932 GB | 928 GB | 3% | ONLINE |
| sas-data | raidz1 (3 drives) | 3× 931 GB | 2.72 TB | 0% | ONLINE |

**Network**
- 2× Broadcom NetXtreme BCM5720 (dual-port each → 4× 1GbE ports)
- vmbr0 bridged to nic0 @ 10.220.1.7/24

**PCIe Notable Devices**
- `0000:01:00.0` — Broadcom/LSI MegaRAID SAS 2208 [Thunderbolt] (PERC H710P)
- `0000:02:00.0/1` — BCM5720 Gigabit Ethernet PCIe (2× ports)
- `0000:06:00.0` — Matrox G200eR2 (iDRAC BMC graphics, not usable for VMs)
- `0000:08:00.0` — WD Black SN770 NVMe SSD

---

### r8202.infiquetra.com — Dell PowerEdge R820 (alias)

**Identity**
- Model: Dell PowerEdge R820 (2U, 2-socket)
- Service Tag: `5DZXBW1`
- BIOS: 2.7.0 released 2020-01-07

**CPU**
- 2× Intel Xeon E5-4650 @ 2.70 GHz
- 8 cores per socket → **16 cores / 32 threads total**
- Microarchitecture: Sandy Bridge-EP (LGA 2011)

**Memory**
- Total: **51.0 GB DDR3 ECC Registered**
- 24 DIMM slots — **13 populated, 11 empty** (significant expansion headroom)
- 4 GB modules @ 1066/1333 MT/s
- Manufacturers: Micron, Kingston

**Storage**

| Device | Model | Size | Type | Notes |
|--------|-------|------|------|-------|
| /dev/nvme0n1 | WD_BLACK SN750 SE 1TB | 1000 GB | NVMe M.2 | SMART: PASSED |
| /dev/sda | (PERC H710 virtual disk) | 1169.3 GB | SAS logical | Possibly RAID-1 pair |
| /dev/sdb | SanDisk 3.2Gen1 | 61.5 GB | USB | Boot/diagnostics USB |

**ZFS Pools**

| Pool | Config | Raw | Usable | Used | Health |
|------|--------|-----|--------|------|--------|
| nvme-fast | Single NVMe | 932 GB | 928 GB | 1.5% | ONLINE |

> No SAS data pool on this host — the SAS disks may be in a hardware RAID-1 used only for OS/boot.

**Network**
- 2× Broadcom NetXtreme BCM5720 (dual-port each → 4× 1GbE ports)
- vmbr0 bridged to nic0 @ 10.220.1.8/24

**PCIe Notable Devices**
- `0000:03:00.0` — Broadcom/LSI MegaRAID SAS 2208 [Thunderbolt] (PERC H710)
- `0000:01:00.0/1`, `0000:02:00.0/1` — BCM5720 Gigabit Ethernet PCIe (4× ports)
- `0000:0b:00.0` — Matrox G200eR2 (iDRAC BMC graphics)
- `0000:05:00.0` — WD Black SN750 SE NVMe SSD

---

### r820.infiquetra.com — Dell PowerEdge R820

**Identity**
- Model: Dell PowerEdge R820 (2U, 4-socket)
- Service Tag: `G1J77Y1`
- BIOS: 2.7.0 released 2020-01-07

**CPU**
- 4× Intel Xeon E5-4650 @ 2.70 GHz
- 8 cores per socket → **32 cores / 64 threads total**
- Microarchitecture: Sandy Bridge-EP (LGA 2011)

**Memory**
- Total: **377.8 GB DDR3 ECC Registered**
- 48 DIMM slots — **all 48 populated** (no expansion headroom)
- 8 GB modules @ 1333 MT/s
- Manufacturers: Micron, Hynix, Kingston, Nanya

**Storage**

| Device | Model | Size | Type | Notes |
|--------|-------|------|------|-------|
| /dev/nvme0n1 | WD_BLACK SN750 SE 1TB | 1000 GB | NVMe M.2 | SMART: PASSED |
| /dev/sda | (PERC H710P virtual disk) | 2397.7 GB | SAS logical | Likely RAID-1 mirror of 2× large HDDs |
| /dev/sdb–sdi | (PERC H710P virtual disk) | 999.7 GB each | SAS logical | 8 drives in sas-data raidz2 |
| /dev/sdj | SanDisk 3.2Gen1 | 61.5 GB | USB | Boot/diagnostics USB |

**ZFS Pools**

| Pool | Config | Raw | Usable | Used | Health |
|------|--------|-----|--------|------|--------|
| nvme-fast | Single NVMe | 932 GB | 928 GB | 5% | ONLINE |
| sas-data | raidz2 (8 drives) | 8× 931 GB | 7.27 TB | 0% | ONLINE |

**Network**
- 2× Broadcom NetXtreme BCM5720 (dual-port each → 4× 1GbE ports)
- vmbr0 bridged to nic0 @ 10.220.1.11/24

**PCIe Notable Devices**
- `0000:03:00.0` — Broadcom/LSI MegaRAID SAS 2208 [Thunderbolt] (PERC H710P)
- `0000:01:00.0/1`, `0000:02:00.0/1` — BCM5720 Gigabit Ethernet PCIe (4× ports)
- `0000:0b:00.0` — Matrox G200eR2 (iDRAC BMC graphics)
- `0000:44:00.0` — WD Black SN750 SE NVMe SSD

---

### r720xd.infiquetra.com — Dell PowerEdge R720xd

**Status**: UNREACHABLE at time of inventory (SSH timeout to 10.220.1.10)

Per CLAUDE.md architecture table (populated manually):
- **RAM**: 94 GB
- **vCPU**: 24
- **NVMe pool**: nvme-fast
- **SAS pool**: sas-data (raidz2 × 2, 11 drives)
- **IP**: 10.220.1.10

> Run inventory again once host is reachable to fill in full specs.

---

## Drive Inventory

### NVMe Drives (all healthy, all transferable to R640)

| Host | Device | Model | Serial | Capacity | SMART |
|------|--------|-------|--------|----------|-------|
| r420 | /dev/nvme0n1 | WD_BLACK SN770 1TB | 22084G803381 | 931.5 GB | PASSED |
| r8202 | /dev/nvme0n1 | WD_BLACK SN750 SE 1TB | 22015G801810 | 931.5 GB | PASSED |
| r820 | /dev/nvme0n1 | WD_BLACK SN750 SE 1TB | 22015G801833 | 931.5 GB | PASSED |

### SAS/SATA Drives — Behind PERC Controllers

> **Limitation**: All SAS drives are presented via Dell PERC H710/H710P controllers. Smartctl cannot query them directly without MegaRAID CLI (`perccli` or `megacli`). The sizes below are logical volume sizes exposed to the OS, not individual physical drive capacities.

| Host | Logical Device | Exposed Size | Actual use | Notes |
|------|---------------|-------------|------------|-------|
| r420 | /dev/sda | 999.7 GB | ZFS sas-data spare/boot? | Via PERC H710P |
| r420 | /dev/sdb–sdd | 999.7 GB each | sas-data raidz1 (3 drives) | 3× 1TB SAS HDDs (actual model unknown) |
| r8202 | /dev/sda | 1169.3 GB | Likely OS RAID-1 | Via PERC H710 |
| r820 | /dev/sda | 2397.7 GB | Likely OS RAID-1 (2× large HDD) | Via PERC H710P |
| r820 | /dev/sdb–sdi | 999.7 GB each | sas-data raidz2 (8 drives) | 8× ~1TB SAS HDDs (actual model unknown) |

### USB Drives

| Host | Device | Model | Size | Purpose |
|------|--------|-------|------|---------|
| r8202 | /dev/sdb | SanDisk 3.2Gen1 | 61.5 GB | Boot/diagnostics |
| r820 | /dev/sdj | SanDisk 3.2Gen1 | 61.5 GB | Boot/diagnostics |

---

## R640 Compatibility Matrix

Target: 3× Dell PowerEdge R640 (2× Xeon Gold 6140, 128 GB DDR4 each)

| Component | Current Servers | R640 Compatible? | Notes |
|-----------|----------------|-----------------|-------|
| **DDR3 RAM** | All current servers | **NO** | R640 requires DDR4. All current DDR3 is scrap/sell. |
| **3.5" SAS HDDs** | r420, r820, r720xd (likely 3.5") | **NO** | R640 is 2.5" SFF only (10 or 24 bay depending on config). 3.5" LFF drives do not fit. |
| **2.5" SAS HDDs** | Unknown (behind PERC, can't confirm form factor) | **MAYBE** | If any drives are 2.5" SAS, they can move to R640. Needs physical verification or perccli to confirm. |
| **NVMe M.2 (WD Black)** | 3× WD Black 1TB NVMe (r420, r8202, r820) | **YES (with adapter)** | R640 supports M.2 via BOSS card or PCIe adapter. All 3 drives are healthy. |
| **BCM5720 1GbE NICs** | All servers (2× per host = 4× ports) | **YES** | Standard PCIe Gen3. However R640 likely already has 4× 1GbE onboard — these are redundant unless you need 10GbE. |
| **PERC H710/H710P** | All servers | **NO / DON'T** | R640 has its own PERC controller. These are redundant and won't be needed. |
| **Matrox G200eR2** | All servers (iDRAC GPU) | **N/A** | Soldered to motherboard, not a discrete card. iDRAC is separate on R640. |
| **Intel SATA AHCI** | All servers (on-board) | **N/A** | On-board chipset controller, not transferable. |
| **WD Black SN770/SN750 SE NVMe** | 3 drives | **YES (M.2 2280)** | M.2 2280 form factor, PCIe Gen3/Gen4. Will need M.2 to U.2 carrier or PCIe adapter card for R640. |

### Key Takeaways for R640 Migration

1. **RAM stays behind** — DDR3 is incompatible with R640's DDR4 slots. Plan to populate R640 with its own DDR4.

2. **NVMe drives are the most transferable asset** — 3× WD Black 1TB drives are healthy and can be repurposed in R640s as fast storage (nvme-fast pool equivalent). You'll need M.2 adapters since R640 doesn't have native M.2 slots.

3. **SAS HDD form factor is the critical unknown** — The PERC controller hides whether drives are 2.5" or 3.5". Run `perccli /c0 /eall /sall show` on each host to get physical drive info. If they're 3.5" LFF, they cannot go into R640. If 2.5" SFF, they can.

4. **NICs are low-value transfers** — BCM5720 is 1GbE only. R640 likely has onboard 1GbE. If you want 10GbE for the R640 cluster, plan to buy dedicated 10GbE NICs (e.g., Intel X710 or Mellanox ConnectX-3/4) rather than reusing these.

5. **PERC controllers are not worth transferring** — R640 will have its own PERC. Skip these.

---

## Server Recommendations

### Keep Running
| Server | Reason |
|--------|--------|
| **r820** | Highest value: 64 threads, 377 GB RAM, 7.27 TB raidz2 pool. Best candidate to remain as a bulk storage/compute node alongside R640s. |
| **r820 (r8202 alias)** | 32 threads, 51 GB RAM (11 empty DIMMs — can be expanded with cheap DDR3). No SAS pool currently. Decent secondary node. |

### Retire / Repurpose
| Server | Reason |
|--------|--------|
| **r420** | Lowest compute (12 cores), oldest platform (LGA 1356, E5-2420 v2). DDR3 slots fully packed. Least useful once R640s arrive. Good candidate to retire, sell for parts, or repurpose as a dedicated storage node. |
| **r720xd** | Unknown status (offline). Needs investigation. If healthy, assess similarly to r420/r8202 based on actual specs. |

### Priority Actions Before R640 Arrival
1. **Identify SAS drive form factor** — run `perccli` on r420 and r820 to determine if drives are 2.5" (movable) or 3.5" (cannot be used in R640).
2. **Procure M.2 adapters** — 3× PCIe adapters (M.2 NVMe to PCIe x4) for the WD Black drives.
3. **Bring r720xd back online** — run inventory playbook against it to complete the full picture.
4. **Plan DDR4 RAM** — R640 arrives with 128 GB DDR4 per node; decide if that's sufficient or purchase additional DIMMs.

---

## How to Re-Run Inventory

```bash
cd ansible
uv run ansible-playbook -i inventory/hosts.yml hardware_inventory.yml \
  --vault-password-file ~/.vault_pass.txt
```

Output files: `docs/inventory/<hostname>.json`

To inventory only specific hosts:
```bash
uv run ansible-playbook -i inventory/hosts.yml hardware_inventory.yml \
  --vault-password-file ~/.vault_pass.txt \
  --limit r720xd.infiquetra.com
```

---

## Gaps and Follow-ups

- [ ] **r720xd** — offline, needs re-run once host is reachable
- [ ] **Physical SAS drive models** — need `perccli /c0 /eall /sall show all` on r420, r8202, r820
- [ ] **NIC speeds** — `iface_speeds` collection returned empty (interfaces may use different naming on Proxmox); use `ethtool eno1` manually to confirm 1GbE vs 10GbE
- [ ] **R640 bay count** — confirm whether R640 units are 10-bay or 24-bay 2.5" SFF configurations
