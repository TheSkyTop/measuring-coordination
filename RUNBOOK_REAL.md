# Run-book — REAL coordination measurement from one regional CSV

The pipeline can compute **real** coordination cost (CC), efficiency (η) and the
hourly/8760 series from a **single generation-by-fuel CSV per region** — no unit-level
MMSDM download required. This is the credible-first ("v1, technology-aggregate") real
measurement; the unit-level path (`run.py`) refines it later.

## 1. Get the data (one file per region)
Either source works — both give the required columns:

**A. OpenElectricity (easiest, no code)**
1. Open https://explore.openelectricity.org.au/ → choose a region (e.g. South Australia).
2. Set the date range (e.g. 1 Jan 2025 – 31 Dec 2025) and the finest interval available.
3. Download the CSV (generation by fuel technology + demand + price).

**B. NEMOSIS (if you prefer AEMO source data)**
```python
from nemosis import dynamic_data_compiler
# DISPATCHREGIONSUM (demand, price) + DISPATCHLOAD rolled up by fuel via DUDETAILSUMMARY
```
Roll units up to fuel totals per interval and save one CSV per region.

## 2. Required columns (case-insensitive; extra columns are ignored)
| column | meaning |
|---|---|
| `time` | interval timestamp (5-min or 30-min) |
| `demand` | regional operational/total demand (MW) |
| `price` | regional RRP ($/MWh) — optional, enables negative-price frequency |
| fuel columns | one per technology: `black_coal, brown_coal, gas, ccgt, ocgt, hydro, wind, solar, battery` (MW; battery signed: + discharge, − charge) |
| `imports` | net interconnector import (MW, + into region) — optional |

See `data_real/EXAMPLE_region_format.csv` for the exact shape.

## 3. Drop it in and run
Place the file in `data_real/`, then:
```bash
cd coordination_pipeline
python run_real.py data_real/SA1_2025.csv SA1 outputs_real/SA1
```
Outputs in `outputs_real/`: `SA1_daily.csv`, `SA1_hourly.csv`, `SA1_summary.json`
(CC mean/median/p90, η, ρ, renewable share, negative-price frequency).

## 4. Working with Claude
If you drop the CSV(s) into this project folder, I will run the pipeline and write the
**real** CC/η/ρ and the 8760 heatmap straight into Paper 3 — replacing the
AEMO-schema validation figures with measured values for the 2025 NEM.

## Method note
For each day the counterfactual co-optimises the realised dispatchable fleet + storage
against realised demand, net imports and realised variable-renewable availability,
minimising reconstructed SRMC; CC = 100·(C_realised − C_optimal)/C_optimal, η = C_opt/C_dec.
The physical system is identical in both, so the gap is coordination, not capacity.
Storage energy is assumed 2 h unless a duration column is supplied (a documented sensitivity).
