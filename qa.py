"""
qa.py — data-integrity and property checks for the coordination pipeline.

Two jobs:
  (1) validate the INPUT regional dispatch data before measurement, and
  (2) enforce, at run time, the metric PROPERTIES proved in the Supplementary Information
      (non-negativity, boundedness), so any violation flags a data/reconstruction fault
      rather than passing silently.

A measurement is only trustworthy if its inputs are clean and its outputs obey the
theorems. Every real run writes a QA report alongside the metrics.
"""
import numpy as np, pandas as pd
from loaders_aggregate import (load_region, DEMAND_COLS, IMPORT_COLS, TIME_COLS,
                               PRICE_COLS, ALIAS, VRE, STOR, _norm)

BAL_TOL=0.05   # interval energy-balance tolerance (fraction of demand)

def check_input(csvpath):
    """Structural + physical integrity of the raw regional CSV."""
    issues=[]; df=pd.read_csv(csvpath); cols={_norm(c):c for c in df.columns}
    tcol=next((cols[c] for c in TIME_COLS if c in cols),None)
    dcol=next((cols[c] for c in DEMAND_COLS if c in cols),None)
    if tcol is None: issues.append("FAIL no time column")
    if dcol is None: issues.append("FAIL no demand column")
    if issues: return dict(ok=False,issues=issues)
    t=pd.to_datetime(df[tcol]); 
    if t.is_monotonic_increasing is False: issues.append("WARN timestamps not sorted")
    if t.duplicated().any(): issues.append(f"WARN {int(t.duplicated().sum())} duplicate timestamps")
    dt=t.diff().dropna().dt.total_seconds()
    if dt.nunique()>1: issues.append(f"WARN irregular intervals ({sorted(set(dt))[:3]}s)")
    d=pd.to_numeric(df[dcol],errors='coerce')
    if d.isna().any(): issues.append(f"FAIL {int(d.isna().sum())} missing demand values")
    if (d<=0).any(): issues.append(f"WARN {int((d<=0).sum())} non-positive demand intervals")
    # energy balance: sum(generation)+imports ~ demand
    icol=next((cols[c] for c in IMPORT_COLS if c in cols),None)
    fuelcols=[cols[c] for c in cols if c not in {_norm(tcol),_norm(dcol)} and c not in PRICE_COLS
              and (icol is None or c!=_norm(icol)) and pd.api.types.is_numeric_dtype(df[cols[c]])]
    gen=df[fuelcols].apply(pd.to_numeric,errors='coerce').clip(lower=None).sum(axis=1)
    imp=pd.to_numeric(df[icol],errors='coerce').fillna(0) if icol else 0
    resid=(gen+imp-d)/d.replace(0,np.nan)
    bad=int((resid.abs()>BAL_TOL).sum())
    if bad>0: issues.append(f"WARN {bad}/{len(df)} intervals exceed {int(BAL_TOL*100)}% energy-balance tolerance (median resid {resid.median():+.1%})")
    if abs(np.nanmedian(resid))>0.25: issues.append(f"FAIL gross energy-balance failure (median resid {np.nanmedian(resid):+.1%}) — data not a coherent regional dispatch")
    ok=not any(i.startswith("FAIL") for i in issues)
    return dict(ok=ok,n_intervals=int(len(df)),fuel_columns=fuelcols,
                balance_median=float(np.nanmedian(resid)),issues=issues or ["clean"])

def check_metrics(m):
    """Enforce the SI properties on a day's metrics (Theorems S2.1, S2.2)."""
    v=[]
    if m is None: return ["FAIL infeasible counterfactual"]
    if m['CC']< -1e-6: v.append(f"FAIL CC<0 ({m['CC']:.3f}) — violates Thm S2.1 (reconstruction fault)")
    if not (0<m['eta']<=1+1e-9): v.append(f"FAIL eta∉(0,1] ({m['eta']:.3f})")
    if m['rho']==m['rho'] and not (-1-1e-6<=m['rho']<=1+1e-6): v.append(f"FAIL rho∉[-1,1] ({m['rho']:.3f})")
    return v or ["ok"]

def storage_sensitivity(csvpath, region, hours=(1.0,2.0,4.0)):
    """Bracket CC under the storage-duration assumption (a documented sensitivity)."""
    from coordlib import day_metrics
    out={}
    for h in hours:
        days=load_region(csvpath,storage_hours=h); ccs=[]
        for _,dem,imp,disp,vre,stor,_ in days:
            m=day_metrics(dem,imp,disp,vre,stor)
            if m: ccs.append(m['CC'])
        out[f"{h}h"]=float(np.mean(ccs)) if ccs else None
    return out
