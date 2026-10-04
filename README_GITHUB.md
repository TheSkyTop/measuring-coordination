# Measuring Coordination — code and data

Code and processed data for: Y. Xie and Z. Chen, "Measuring Coordination: A Scientific Framework for Making Coordination Observable in Electricity Markets" (submitted to IEEE Transactions on Smart Grid, 2026).

- `run_year.py`, `coordlib.py`, `run_constrained.py`, `qa.py` — counterfactual co-optimisation pipeline (daily LP, energy-only and must-run-constrained), metric computation and integrity checks.
- `fetch_openelectricity.py`, `loaders_aggregate.py` — ingest of hourly regional dispatch (Open Electricity, CC BY-NC 4.0).
- `Source_Data/` — input CSVs (five NEM regions, 2025), measured daily/hourly/heatmap outputs and summary JSONs used in the paper.
- `figure_code/` — scripts producing the paper's figures.
- `RUNBOOK_REAL.md`, `GET_THE_DATA.md` — how to reproduce.

Licence: code MIT; processed data derived from Open Electricity under CC BY-NC 4.0 (non-commercial).
