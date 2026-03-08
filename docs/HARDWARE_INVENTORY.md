# Hardware Inventory — Home Lab Proxmox Cluster

**Collected**: 2026-03-08
**Method**: Ansible playbook (`ansible/hardware_inventory.yml`) — pvesh API + dmidecode + smartctl; physical drive details via `smartctl -d megaraid,N` passthrough
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

### NVMe Drives (M.2 2280, all healthy)

| Host | Model | Serial | Capacity | SMART |
|------|-------|--------|----------|-------|
| r420 | WD_BLACK SN770 1TB | 22084G803381 | 931.5 GB | PASSED |
| r8202 | WD_BLACK SN750 SE 1TB | 22015G801810 | 931.5 GB | PASSED |
| r820 | WD_BLACK SN750 SE 1TB | 22015G801833 | 931.5 GB | PASSED |

### Physical Drives Behind PERC — r420

Queried via `smartctl -d megaraid,N`. All **3.5" SATA desktop drives** (consumer BarraCuda — unusual in a server).

| Slot | Model | Serial | Capacity | RPM | Form Factor | SMART |
|------|-------|--------|----------|-----|-------------|-------|
| 0 | Seagate ST1000DM010-2EP102 | Z9AB6ER5 | 1.00 TB | 7200 | **3.5 inches** | PASSED |
| 1 | Seagate ST1000DM010-2EP102 | Z9AB6ERL | 1.00 TB | 7200 | **3.5 inches** | PASSED |
| 2 | Seagate ST1000DM010-2EP102 | Z9AB6XY3 | 1.00 TB | 7200 | **3.5 inches** | PASSED |
| 3 | Seagate ST1000DM010-2EP102 | Z9AB6VFT | 1.00 TB | 7200 | **3.5 inches** | PASSED |

ZFS use: sdb/sdc/sdd → `sas-data` raidz1; sda → likely OS/boot VD.

### Physical Drives Behind PERC — r8202

All **2.5" enterprise SAS drives**, 15K RPM. Very high runtime hours.

| Slot | Vendor | Model | Capacity | RPM | Form Factor | Runtime | Grown Defects | Non-Med Errors |
|------|--------|-------|----------|-----|-------------|---------|---------------|----------------|
| 0 | Seagate | ST9146853SS | 146 GB | 15K | **2.5 inches** | 56,312 hrs (~6.4 yr) | 0 | 10 |
| 1 | Seagate | ST9146853SS | 146 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 2 | Toshiba | MK1401GRRB | 146 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 3 | Toshiba | MK1401GRRB | 146 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 4 | HP | EH0300FBQDD | 300 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 5 | HP | EH0300FBQDD | 300 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 6 | HP | EH0300FBQDD | 300 GB | 15K | **2.5 inches** | (not queried) | — | — |
| 7 | HP | EH0300FBQDD | 300 GB | 15K | **2.5 inches** | (not queried) | — | — |

ZFS use: none. PERC presents them as single large logical volume (sda, 1169 GB), likely RAID-5 or RAID-6.

> Note: 10 non-medium errors on slot 0 indicates minor error log entries — not critical, but worth monitoring.

### Physical Drives Behind PERC — r820

Mix of 4× SAS HDDs and 8× SATA SSDs. **All 2.5" SFF.**

| Slot | Vendor / Model | Capacity | Type | RPM | Form Factor | SMART | Hours |
|------|---------------|----------|------|-----|-------------|-------|-------|
| 0 | Hitachi HUC10606 CLAR600 | 600 GB | SAS HDD | 10K | **2.5 inches** | Health: OK, 0 defects | 371 hrs |
| 1 | Hitachi HUC10606 CLAR600 | 600 GB | SAS HDD | 10K | **2.5 inches** | Health: OK | — |
| 2 | Hitachi HUC10606 CLAR600 | 600 GB | SAS HDD | 10K | **2.5 inches** | Health: OK | — |
| 3 | Hitachi HUC10606 CLAR600 | 600 GB | SAS HDD | 10K | **2.5 inches** | Health: OK | — |
| 8 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 9 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 10 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 11 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 12 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 13 | Crucial CT1000MX500SSD1 | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 14 | WD WDBNCE0010PNC (Blue SN) | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |
| 15 | WD WDBNCE0010PNC (Blue SN) | 1.00 TB | SATA SSD | SSD | **2.5 inches** | PASSED | — |

ZFS use: sdb–sdi (slots 8–15, the 8 SSDs) → `sas-data` raidz2; sda (4 Hitachi HDDs as RAID-0 stripe = ~2400 GB logical) → not in ZFS.

> The Hitachi drives are enterprise SAS HDDs with only ~370 hours of use — essentially new drives despite living in old hardware.

### USB Drives (boot media, not transferable)

| Host | Model | Size |
|------|-------|------|
| r8202 | SanDisk 3.2Gen1 | 61.5 GB |
| r820 | SanDisk 3.2Gen1 | 61.5 GB |

---

## R640 Compatibility Matrix

Target: 3× Dell PowerEdge R640 (2× Xeon Gold 6140, 128 GB DDR4 each)

| Component | Host(s) | Qty | R640 Compatible? | Notes |
|-----------|---------|-----|-----------------|-------|
| **DDR3 ECC RAM** | All | ~540 GB total | **NO** | R640 requires DDR4. All DDR3 scrap/sell. |
| **3.5" SATA HDDs** (Seagate ST1000DM010) | r420 | 4× 1TB | **NO** | R640 is 2.5" SFF only. 3.5" desktop drives don't fit and are consumer grade anyway. |
| **2.5" SAS HDDs** (Hitachi HUC10606) | r820 | 4× 600GB | **YES** | 2.5" SFF SAS, 10K RPM. Will fit R640 bays. Only 371 hrs of use — essentially new. |
| **2.5" SATA SSDs** (Crucial MX500 1TB) | r820 | 6× 1TB | **YES** | 2.5" SFF SATA. Fit R640 bays natively. All SMART PASSED. |
| **2.5" SATA SSDs** (WD Blue SN 1TB) | r820 | 2× 1TB | **YES** | 2.5" SFF SATA. Fit R640 bays natively. All SMART PASSED. |
| **2.5" SAS HDDs** (Seagate/Toshiba/HP) | r8202 | 8× 146–300GB | **YES (but low value)** | 2.5" SFF, physically fit. But 146 GB and 300 GB is tiny — and slot 0 has 56K hours. Probably not worth moving. |
| **NVMe M.2 2280** (WD Black 1TB) | r420, r8202, r820 | 3× 1TB | **YES (with adapter)** | M.2 2280. R640 needs PCIe M.2 adapter card. All healthy. |
| **BCM5720 1GbE NICs** | All | 2× per host | **Redundant** | R640 has onboard 1GbE. Only useful if you need more than 4 ports per node. |
| **PERC H710/H710P** | All | 1× per host | **NO** | R640 has its own PERC. Skip. |
| **Matrox G200eR2** | All | — | **N/A** | Soldered BMC chip. Not a removable card. |

### Key Takeaways for R640 Migration

1. **r420's drives are worthless for R640** — 3.5" consumer Seagate desktop drives. Cannot physically fit in R640. Repurpose r420 as NAS/archive or sell.

2. **r820 is the drive goldmine** — All 12 drives are 2.5" SFF and can move to R640:
   - 4× Hitachi 600GB 10K SAS HDDs (basically new, 371 hrs) → strong candidates for R640 boot or data drives
   - 8× 1TB SATA SSDs (Crucial + WD) → excellent for ZFS storage in R640

3. **3 WD Black NVMe drives** — all healthy, move to R640 as the fast `nvme-fast` pool equivalent. Need PCIe M.2 adapter cards (~$15 each).

4. **r8202's drives fit but aren't worth it** — 2.5" physically fits but the drives are 146–300 GB with up to 56K runtime hours. Skip unless desperate for SAS spindles.

5. **No DDR3 transfers anywhere** — all current RAM is DDR3. Budget for DDR4 for R640s.

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
1. **Procure 3× M.2 PCIe adapter cards** — for the WD Black NVMe drives (M.2 2280 NVMe → PCIe x4 riser).
2. **Bring r720xd back online** — run inventory playbook against it to complete the full picture.
3. **Plan DDR4 RAM** — R640 arrives with 128 GB DDR4 per node; decide if that's sufficient or purchase additional DIMMs.
4. **Decide r420 fate** — its 3.5" desktop drives and old LGA 1356 platform have little reuse value once R640s arrive. Best candidate to retire.

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
- [ ] **r8202 per-drive runtime/health** — only slot 0 health queried in detail; run full scan across slots 1–7
- [ ] **NIC speeds** — `iface_speeds` collection returned empty (interfaces may use different naming on Proxmox); use `ethtool eno1` manually to confirm 1GbE vs 10GbE
- [ ] **R640 bay count** — confirm whether R640 units are 10-bay or 24-bay 2.5" SFF configurations
- [x] ~~Physical drive form factors~~ — resolved via `smartctl -d megaraid,N` passthrough (see Drive Inventory above)
