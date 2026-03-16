# UPS Power Analysis & Purchase Recommendations

**Date**: 2026-03-16
**Cluster**: olympus (6-node Proxmox)

---

## Measured Power Consumption

Data pulled from Prometheus via IPMI exporter DCMI power readings on 2026-03-16.

| Host | Model | Current (W) | 7-Day Avg (W) | 7-Day Peak (W) |
|------|-------|-------------|----------------|-----------------|
| r420 (10.220.1.7) | PowerEdge R420 | 126 | 126 | 140 |
| r640-1 (10.220.1.8) | PowerEdge R640 | 120 | 124 | 168 |
| r640-2 (10.220.1.9) | PowerEdge R640 | 120 | 122 | 192 |
| r640-3 (10.220.1.12) | PowerEdge R640 | 144 | 146 | 168 |
| r720xd (10.220.1.10) | PowerEdge R720xd | 182 | 182 | 196 |
| r820 (10.220.1.11) | PowerEdge R820 | 266 | 267 | 294 |
| **Total** | | **958W** | **967W** | **1,158W** |

### Key Observations

- **Steady-state draw is ~960W** — remarkably stable (averages match current readings almost exactly)
- **Peak draw is ~1,160W** — only ~20% above idle; these servers run Ceph + light VMs, not heavy compute
- **R820 is the power hog** — 28% of total draw from one server (4-socket, 377GB RAM)
- **R640s are efficient** — 120-144W each despite 128GB RAM and NVMe/SSD arrays

### Electrical Context

- **~960W steady = ~8.0A on a 120V/15A circuit** (53% utilization — within the 80% continuous load rule of 12A)
- **~1,160W peak = ~9.7A** — still fine on a single 15A circuit
- A **20A circuit** is ideal if rewiring during re-rack (gives 2,400W continuous headroom)

---

## UPS Sizing Requirements

| Parameter | Value |
|-----------|-------|
| Steady-state load | ~960W |
| Peak load | ~1,160W |
| Target runtime (ride-out short outage) | 10-15 minutes |
| Target runtime (graceful shutdown) | 5 minutes minimum |
| Form factor | Rack-mountable, 2U preferred |
| Voltage | 120V (US) |
| Output waveform | **Pure sine wave required** — Dell PowerEdge servers use Active PFC PSUs which can malfunction on simulated/stepped sine wave |

### Sizing Math

- At 0.9 power factor: 960W ÷ 0.9 = 1,067 VA minimum (but 100% load = terrible runtime)
- **Rule of thumb**: size to 30-50% load for good runtime and battery longevity
- 960W ÷ 0.5 = 1,920 VA minimum → round up to **2,200-3,000 VA**
- **3,000 VA is the sweet spot**: ~32% load at steady state, ~39% at peak

---

## Recommendations

### Option A — Best Bang for Buck: Refurb APC SMT3000RM2U

| Item | Est. Price | Runtime at 960W |
|------|------------|-----------------|
| APC SMT3000RM2U (refurb, new batteries) | $500–700 | **16–18 min** |
| USB cable | $5–10 | |
| **Total** | **~$510–710** | |

Sources: eBay, ExcessUPS, Amazon Renewed. The SMT3000RM2U is the same unit as the newer SMT3000RM2UC minus SmartConnect cloud — irrelevant since NUT is used for monitoring. Replacement batteries (RBC43 compatible) run ~$100–150.

### Option B — Best New Value: CyberPower PR3000LCDRTXL2U

| Item | Est. Price | Runtime at 960W |
|------|------------|-----------------|
| CyberPower PR3000LCDRTXL2U | $1,000–1,100 | **9–10 min** |
| USB cable | $5–10 | |
| **Total** | **~$1,010–1,110** | |

Unity power factor (3000W from 3000VA). Supports external battery packs for extended runtime.

### Option B+ — CyberPower + Extended Battery

| Item | Est. Price | Runtime at 960W |
|------|------------|-----------------|
| CyberPower PR3000LCDRTXL2U | $1,000–1,100 | |
| BP48V75ART2U external battery pack | $450–550 | |
| **Total** | **~$1,460–1,660** | **~25–30 min** |

### Option C — Industry Standard: APC SMT3000RM2UC (new)

| Item | Est. Price | Runtime at 960W |
|------|------------|-----------------|
| APC SMT3000RM2UC | $1,400–1,600 | **16–18 min** |
| USB cable | $5–10 | |
| **Total** | **~$1,410–1,610** | |

### Option D — Enterprise: Eaton 5PX G2 3000 (built-in network card)

| Item | Est. Price | Runtime at 960W |
|------|------------|-----------------|
| Eaton 5PX G2 3000 (w/ network card) | $1,800–2,200 | **10–12 min** |
| EBM extended battery module | $600–800 | |
| **Total w/ EBM** | **~$2,410–3,010** | **~25–35 min** |

---

## Runtime Comparison

| UPS | At 960W (steady) | At 1,160W (peak) | With External Battery |
|-----|-----------------|-----------------|----------------------|
| APC SMT3000RM2U (refurb) | ~16–18 min | ~12–14 min | N/A |
| APC SMT3000RM2UC (new) | ~16–18 min | ~12–14 min | N/A |
| CyberPower PR3000LCDRTXL2U | ~9–10 min | ~7–8 min | ~25–30 min |
| Eaton 5PX G2 3000 | ~10–12 min | ~7–9 min | ~25–35 min |

**APC's 16-18 minutes at 960W** is the clear winner for runtime without external batteries — enough time to get the generator out and plugged in. CyberPower or Eaton with an EBM are the path to 25+ minutes.

---

## Wiring

All recommended units use an **L5-30P input plug** — plugs directly into an L5-30R receptacle on a 30A/120V circuit with no adapters. On the existing dedicated 30A circuit:

- 3,600W continuous capacity at 80% rule = 2,880W
- 960W servers + 300W UPS charging = 1,260W → **35% circuit utilization** — plenty of headroom

---

## Annual Operating Cost

| Item | Cost |
|------|------|
| Electricity (960W × 8,760h × $0.13/kWh) | ~$1,093/year |
| UPS efficiency loss (~5%) | ~$55/year |
| Battery replacement (every 3–5 years, amortized) | ~$30–50/year |
| **Total** | **~$1,178/year** |

---

## Current State (as of 2026-03-16)

A **Tripp Lite SMART1500LCD** (1500VA / 900W) is already in the rack powering the networking equipment (UniFi UDM, 48-port switch, fibre aggregation switch). It is **not** powering any servers — its 900W capacity is insufficient for the 960W cluster load.

NUT is configured to monitor the Tripp Lite via USB to r640-1. See `ansible/ups.yml` and `ansible/roles/ups_nut/`.

The server UPS purchase decision is still open. **Recommended path: Refurb APC SMT3000RM2U (~$600).**
