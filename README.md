# Measuring Coordination — code and data

Code and processed data for: Y. Xie and Z. Chen, "Measuring Coordination: A Scientific Framework for Making Coordination Observable in Electricity Markets" (submitted to IEEE Transactions on Smart Grid, 2026).

All results in the paper are produced from **real** hourly dispatch data for the five regions of the Australian National Electricity Market (NEM), calendar year 2025, as shipped in `Source_Data/`.

## Layout
- `run_year.py` — full-year measurement: daily counterfactual LP (energy-only, or must-run-constrained via `mustrun=φ`), cost-weighted annual CC, η, daily and hour×month outputs.
- `coordlib.py` — counterfactual co-optimisation (dispatchable merit order, storage, curtailable VRE) and metric definitions; technology SRMC defaults.
- `run_constrained.py`, `sensitivity_sa.py` — must-run (φ) and parameter sensitivities reported in the Supplementary Material (S8, S9).
- `qa.py` — input integrity checks and run-time checks of the metric properties (CC ≥ 0, η ∈ (0,1]).
- `fetch_openelectricity.py`, `loaders_aggregate.py`, `run_openelectricity.py` — ingest of hourly regional generation-by-fuel, demand, price and curtailment from Open Electricity.
- `Source_Data/` — inputs (`<REGION>_2025_api.csv`) and outputs used in the paper: `*_measured_daily.csv`, `*_measured_heatmap.csv`, `*_measured_summary.json` (energy-only), `*_constrained_summary.json` (φ = 0.5), `regional_final.json`.
- `figure_code/` — scripts producing the paper's figures.
- `RUNBOOK_REAL.md`, `GET_THE_DATA.md` — reproduction steps.

## Reproduce one region
```
pip install pandas numpy scipy matplotlib
# inputs are shipped in Source_Data/; to re-download see GET_THE_DATA.md
python run_year.py Source_Data/SA1_2025_api.csv Source_Data/SA1_2025_measured SA1 0.0   # energy-only
python run_year.py Source_Data/SA1_2025_api.csv Source_Data/SA1_2025_constrained SA1 0.5  # must-run φ=0.5
```
Days on which the LP is infeasible against the realised record, or on which least-cost cost is zero, are skipped and reported in the summary `full_days`.

## Licence
Code: MIT. Processed data are derived from Open Electricity (CC BY-NC 4.0) and are for non-commercial research use.
