# coordination_pipeline — measuring coordination cost in the NEM

The world's-first measurement pipeline for **coordination cost** in an electricity market. Given real dispatch data it reconstructs the realised dispatch, builds the **counterfactual co-optimised dispatch of the same fleet, network and weather**, and reports three metrics:

- **Coordination cost** `CC = 100·(C_dec − C_opt)/C_opt` — economic efficiency loss
- **Coordination efficiency** `η = C_opt/C_dec ∈ (0,1]` — operator dashboard metric (1 = perfectly coordinated)
- **Decision correlation** `ρ` — mean off-diagonal correlation of resource deviations (realised − co-optimised)

Holding the physical system fixed isolates **coordination** from **capacity**.

> **Status.** The pipeline is complete and validated end-to-end on AEMO-schema **synthetic** data (see `data_processed/SA_demo`, `outputs_metrics/`, `figures/`). It is ready to run on **real** CY2025 data the moment the NEMOSIS ingest is run (network required). All `outputs_metrics/` and `figures/` currently shipped are from the synthetic fixture and are labelled as such.

## Minimum viable version (do this first)
**SA region · CY2025 · utility batteries + wind/solar + demand · 5-min → hourly.** Get `real dispatch → counterfactual dispatch → coordination metrics` working for one region; then add VIC; then the full NEM. Do **not** attempt full NEMDE replication first — the goal is *credible, transparent, reproducible*.

## Pipeline layout
```
coordination_pipeline/
├── scripts_ingest/
│   ├── ingest_nemosis.py     # REAL data: pull AEMO MMS tables via NEMOSIS -> processed CSVs
│   └── make_synthetic.py     # synthetic AEMO-schema fixture (validation / offline dev)
├── loaders.py                # data layer: read processed CSVs -> pipeline structures
├── coordlib.py               # model_counterfactual: co-optimisation LP + metrics (CC, η, ρ)
├── run.py                    # orchestrator: region -> daily/hourly metrics + heatmap
├── figures_pipeline.py       # the three key figures
├── data_processed/           # cleaned CSVs the pipeline reads (SA_demo = synthetic example)
├── outputs_metrics/          # CC/η/ρ: *_daily.csv, *_hourly.csv (8760), *_heatmap.csv, *_summary.json
└── figures/                  # fig_heatmap_SA, fig_regional, fig_drivers
```

## Required AEMO data (real run)
| Module | AEMO MMS table | Pipeline file |
|---|---|---|
| Unit dispatch (5-min) | `DISPATCHLOAD` (TOTALCLEARED / SCADA) | `DISPATCHLOAD.csv` |
| Price (5-min) | `DISPATCHPRICE` (RRP) | `DISPATCHPRICE.csv` |
| Demand + interchange | `DISPATCHREGIONSUM` (TOTALDEMAND, NETINTERCHANGE) | `DISPATCHREGIONSUM.csv` |
| Unit registration | `DUDETAILSUMMARY` / Generators & Scheduled Loads | `DUDETAILSUMMARY.csv` |
| Bids (optional, cost) | `BIDDAYOFFER` / `BIDPEROFFER` | `BIDS.csv` |
| Constraints (phase 2) | `GENCONDATA` / invoked constraints | — |
| Interconnectors (phase 2) | `DISPATCHINTERCONNECTORRES` | — |
| FCAS (phase 2) | `DISPATCHLOAD` FCAS + FCAS prices | — |

## Tech stack
Python · pandas · **DuckDB** (recommended for the large 5-min tables) · **NEMOSIS** (UNSW CEEM — pulls AEMO MMS/NEMWeb data) · scipy.optimize (LP; swappable for `linopy`/`pyomo`) · matplotlib.

## Run it
**Real data (SA, one month first):**
```bash
pip install nemosis duckdb pandas scipy matplotlib
cd scripts_ingest
python ingest_nemosis.py --start "2025/01/01 00:00:00" --end "2025/02/01 00:00:00" \
       --region SA1 --cache ../data_raw --out ../data_processed
cd ..
python run.py data_processed SA1 outputs_metrics/SA1
python figures_pipeline.py
```
**Synthetic (offline validation, no network):**
```bash
cd scripts_ingest && python make_synthetic.py && cd ..
python run.py scripts_ingest/data_synth SA1 outputs_metrics/SA1
```

## Outputs
- `outputs_metrics/{REGION}_hourly.csv` — hourly CC (the 8760 series)
- `outputs_metrics/{REGION}_daily.csv` — daily CC, η, ρ, renewable share, negative-price frequency
- `outputs_metrics/{REGION}_heatmap.csv` — hour-of-day × month CC
- `outputs_metrics/{REGION}_summary.json` — CC mean/median/p90, η, ρ
- `figures/` — (1) 8760 heatmap, (2) regional comparison, (3) drivers (CC vs ρ + variance explained)

## Method (v1, energy-only)
For each day the counterfactual LP co-optimises dispatchable generation, curtailable VRE (capped at realised availability) and storage (state-of-energy dynamics, power/energy limits) to meet realised demand net of realised interconnector flow, minimising reconstructed fuel cost. `C_dec` is the reconstructed cost of the realised dispatch on the same assets; `CC`, `η`, `ρ` follow. Marginal costs come from bids where available, else technology SRMC defaults (`coordlib.TECH_SRMC`).

**Identification assumptions** (each a sensitivity): same fleet/network/weather/demand in both; counterfactual feasible against realised constraints; faithful cost reconstruction; non-coordination causes (binding transmission, local constraints, market rules) attributed by re-solving with/without each. Phase 2 adds network constraints, interconnector optimisation, FCAS co-optimisation and inter-day storage carry-over.

## Roadmap
1. SA CY2025 — ingest, reconstruct `D_real`, plot real battery charging / negative prices / renewable share.
2. Build the simplified counterfactual; output first **real** CC, η, ρ and the 8760 heatmap.
3. Extend to VIC, then the full NEM (SA/VIC/NSW/QLD/TAS).
4. Add constraints, interconnectors, FCAS; harden cost reconstruction from bids.

The first real result to aim for is a single citable sentence, e.g. *"Coordination cost accounted for X% of operating cost in the 2025 South Australian market,"* or *"decision correlation, not renewable penetration, explains most coordination inefficiency."*
