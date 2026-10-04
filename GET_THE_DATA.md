# GET THE DATA — one regional file unlocks the real measurement

The pipeline needs **one generation-by-fuel CSV per region** (5-min or 30-min). Pick any source below; all give the columns the pipeline reads. Start with **South Australia, 2025**.

---

## Option A — OpenElectricity (easiest, 2 minutes, no code)
1. Go to **https://explore.openelectricity.org.au/**
2. Choose region: **South Australia** (top selector).
3. Set the date range — e.g. **1 Jan 2025 → 31 Dec 2025** — and the finest interval offered.
4. Click **Download / Export → CSV** (generation by technology, demand, price).
5. Save it as `SA1_2025.csv` and drop it into **Paper 3's data folder**:
   `Submission3/Source_Data/`

That's it — tell me it's there and I run the measurement.

---

## Option B — AEMO NEM data dashboard
**https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/data-dashboard-nem**
Export regional generation-by-fuel + demand + price for the period, save per region.

## Option C — NEMOSIS (most faithful to AEMO source; needs Python + internet)
```bash
pip install nemosis pandas
```
```python
from nemosis import dynamic_data_compiler
s,e = "2025/01/01 00:00:00","2026/01/01 00:00:00"
price  = dynamic_data_compiler(s,e,"DISPATCHPRICE","./cache")        # RRP
region = dynamic_data_compiler(s,e,"DISPATCHREGIONSUM","./cache")    # demand, interchange
unit   = dynamic_data_compiler(s,e,"DISPATCHLOAD","./cache")         # unit dispatch
# roll units up to fuel totals per interval (join DUDETAILSUMMARY for fuel type),
# then save one CSV per region with the columns below.
```

---

## Required columns (case-insensitive; extras ignored)
| column | meaning |
|---|---|
| `time` | interval timestamp |
| `demand` | regional operational demand (MW) |
| `price` | RRP ($/MWh) — optional but enables negative-price frequency |
| fuel columns | `black_coal, brown_coal, gas, ccgt, ocgt, hydro, wind, solar, battery` (MW; battery **signed**: + discharge, − charge) |
| `imports` | net interconnector import (MW, + into region) — optional |

See `coordination_pipeline/data_real/EXAMPLE_region_format.csv` for the exact shape.

## What happens once the file is in `Submission3/Source_Data/`
I run (outputs land beside it, in Paper 3):
```bash
python coordination_pipeline/run_real.py Submission3/Source_Data/SA1_2025.csv SA1 Submission3/Source_Data/SA1_measured
```
→ real **CC, η, ρ**, the **8760 heatmap**, a **QA report** (`_qa.json`), and a **storage-duration sensitivity** bracket. I then write the measured South Australian 2025 numbers and the 8760 heatmap into Paper 3 §8, and the line "we do not claim to have measured…" becomes "we measure."

> Note: I cannot download this file from inside this session (AEMO serves it as a binary download my tools can't parse, and the live APIs time out). The two-minute manual export is the reliable path — then everything else is automated.
