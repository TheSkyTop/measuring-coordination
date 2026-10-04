#!/usr/bin/env python3
"""
fetch_openelectricity.py — pull a FULL YEAR (or any range) of NEM dispatch data
from the OpenElectricity API and write one CSV per region in the same format the
web export uses, so the coordination pipeline (run_openelectricity.py) reads it directly.

WHY THIS EXISTS: the OpenElectricity website only exports 30-min data for <=7 days.
The API has no such cap (it just chunks by its range limits), so this is the way to
get a whole year. The free Community plan covers the last 2 years (includes 2025).

------------------------------------------------------------------------------
ONE-TIME SETUP
  1. Get a free API key:  https://platform.openelectricity.org.au   (sign up -> API key)
  2. Install the client:  pip install openelectricity pandas
  3. Set your key (pick one):
        macOS/Linux:  export OPENELECTRICITY_API_KEY="oe_xxx..."
        Windows CMD:  set OPENELECTRICITY_API_KEY=oe_xxx...
        or just paste it into API_KEY below.

RUN
  python fetch_openelectricity.py --region SA1 --start 2025-01-01 --end 2026-01-01 \
         --interval hour --out "../Submission3/Source_Data"

  --interval hour  -> 24 points/day, 12 requests/year  (recommended; robust, fast)
  --interval 5m    -> finest detail, ~46 requests/year (slower; best resolution)
  --region all     -> every NEM region (SA1 VIC1 NSW1 QLD1 TAS1)

Then tell Claude the file is in Submission3/Source_Data and it runs the measurement.
------------------------------------------------------------------------------
"""
import os, sys, argparse, csv
from datetime import datetime, timedelta
from collections import defaultdict

API_KEY = "oe_8gFMruLFKEX57bGQxByzTw"  # optional: paste your key here instead of using the env var

# OpenElectricity fueltech id  ->  web-export column name (what the pipeline reads)
FT = {
    'coal_black':'Coal (Black) -  MW','coal_brown':'Coal (Brown) -  MW',
    'gas_ccgt':'Gas (CCGT) -  MW','gas_ocgt':'Gas (OCGT) -  MW','gas_steam':'Gas (Steam) -  MW',
    'gas_recip':'Gas (Reciprocating) -  MW','gas_wcmg':'Gas (Reciprocating) -  MW',
    'distillate':'Distillate -  MW','bioenergy_biomass':'Bioenergy -  MW','bioenergy_biogas':'Bioenergy -  MW',
    'hydro':'Hydro -  MW','wind':'Wind -  MW',
    'solar_utility':'Solar (Utility) -  MW','solar_rooftop':'Solar (Rooftop) -  MW',
    'battery_charging':'Battery (Charging) -  MW','battery_discharging':'Battery (Discharging) -  MW',
    'pumps':'Battery (Charging) -  MW',
}
REGIONS = ['SA1','VIC1','NSW1','QLD1','TAS1']
LIMIT_DAYS = {'5m':7,'hour':31,'day':360}   # API max range per request
IV = {'5m':'5m','hour':'1h','day':'1d'}     # our flag -> API interval code

def chunks(start, end, max_days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=max_days), end)
        yield cur, nxt
        cur = nxt

def region_of(name):
    for r in REGIONS:
        if r in str(name): return r
    return None

def fueltech_of(name):
    for ft in FT:
        if ft in str(name).lower(): return ft
    return None

def add(store, region, ts, col, val):
    if val is None: return
    store[region].setdefault(ts, {})[col] = store[region].setdefault(ts, {}).get(col, 0.0) + float(val)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--region', default='SA1')
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--interval', default='hour', choices=['5m','hour','day'])
    ap.add_argument('--out', default='.')
    a = ap.parse_args()

    if API_KEY: os.environ['OPENELECTRICITY_API_KEY'] = API_KEY
    if not os.environ.get('OPENELECTRICITY_API_KEY'):
        sys.exit("ERROR: set OPENELECTRICITY_API_KEY (env var) or paste it into API_KEY at the top.")

    from openelectricity import OEClient
    from openelectricity.types import DataMetric, MarketMetric

    start = datetime.fromisoformat(a.start); end = datetime.fromisoformat(a.end)
    regions = REGIONS if a.region.lower()=='all' else [a.region.upper()]
    store = {r: {} for r in regions}            # region -> ts -> {col: val}
    maxd = LIMIT_DAYS[a.interval]; iv = IV[a.interval]

    market_metrics = [MarketMetric.PRICE, MarketMetric.DEMAND,
                      MarketMetric.CURTAILMENT_WIND, MarketMetric.CURTAILMENT_SOLAR_UTILITY,
                      MarketMetric.FLOW_IMPORTS, MarketMetric.FLOW_EXPORTS]
    MKT = {'price':'Price - AUD/MWh','demand':'demand',
           'curtailment_wind':'Wind (Curtailment) -  MW',
           'curtailment_solar_utility':'Solar (Utility) (Curtailment) -  MW',
           'imports':'Imports -  MW','exports':'Exports -  MW'}

    with OEClient() as client:
        for ci,(cs,ce) in enumerate(chunks(start,end,maxd),1):
            print(f"[{ci}] {cs.date()} -> {ce.date()}  generation...", flush=True)
            gen = client.get_network_data(network_code="NEM", metrics=[DataMetric.POWER],
                  interval=iv, date_start=cs, date_end=ce,
                  primary_grouping="network_region", secondary_grouping="fueltech")
            for ts_ in gen.data:
                for res in ts_.results:
                    reg = region_of(res.name); ft = fueltech_of(res.name)
                    if reg not in store or ft is None or ft not in FT: continue
                    for dp in res.data:
                        v = dp.value
                        if ft=='battery_charging' and v is not None and v>0: v=-v  # ensure load negative
                        add(store, reg, dp.timestamp, FT[ft], v)
            print(f"     market (price/demand/curtailment/flows)...", flush=True)
            mkt = client.get_market(network_code="NEM", metrics=market_metrics,
                  interval=iv, date_start=cs, date_end=ce, primary_grouping="network_region")
            for ts_ in mkt.data:
                m = str(ts_.metric).lower()
                col = MKT.get(m)
                if col is None: continue
                for res in ts_.results:
                    reg = region_of(res.name)
                    if reg not in store: continue
                    for dp in res.data:
                        v = dp.value
                        if m=='exports' and v is not None: v=-abs(v)   # exports negative
                        if m=='imports' and v is not None: v=abs(v)
                        add(store, reg, dp.timestamp, col, v)

    os.makedirs(a.out, exist_ok=True)
    cols_order = ['Imports -  MW','Exports -  MW','Battery (Charging) -  MW','Battery (Discharging) -  MW',
                  'Coal (Black) -  MW','Coal (Brown) -  MW','Distillate -  MW','Gas (Steam) -  MW',
                  'Gas (CCGT) -  MW','Gas (OCGT) -  MW','Gas (Reciprocating) -  MW','Bioenergy -  MW',
                  'Hydro -  MW','Wind -  MW','Solar (Utility) -  MW','Solar (Rooftop) -  MW',
                  'Wind (Curtailment) -  MW','Solar (Utility) (Curtailment) -  MW',
                  'demand','Price - AUD/MWh']
    for reg, rows in store.items():
        if not rows: print(f"WARNING: no data for {reg}"); continue
        ts_sorted = sorted(rows)
        present = [c for c in cols_order if any(c in rows[t] for t in ts_sorted)]
        path = os.path.join(a.out, f"{reg}_{start.year}_api.csv")
        with open(path,'w',newline='') as f:
            w = csv.writer(f); w.writerow(['date']+present)
            for t in ts_sorted:
                w.writerow([t]+[rows[t].get(c,0.0) for c in present])
        print(f"WROTE {path}  ({len(ts_sorted)} intervals, {len(present)} columns)")

if __name__ == '__main__':
    main()
