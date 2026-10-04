"""
loaders_aggregate — REAL-DATA path from a SINGLE regional generation-by-fuel CSV.

Lowers the data barrier: instead of the full unit-level MMSDM set, the pipeline
runs from one regional CSV per region (e.g. an OpenElectricity region export, or a
NEMOSIS region roll-up) with columns:

  time, demand, price(optional), and one column per fuel/technology
  (e.g. black_coal, brown_coal, gas, ccgt, ocgt, hydro, wind, solar, battery, imports)

Fuels are classified into dispatchable / variable-renewable / storage / imports.
Output structures feed coordlib.day_metrics unchanged, so the counterfactual and the
metrics (CC, eta) are exactly those validated in the unit-level path.
"""
import numpy as np, pandas as pd
from coordlib import srmc

ALIAS={'coal':'black_coal','black coal':'black_coal','brown coal':'brown_coal',
       'gas_ccgt':'ccgt','gas_ocgt':'ocgt','gas_recip':'ocgt','gas_steam':'gas_steam',
       'distillate':'diesel','bioenergy':'biomass','biomass':'biomass','hydro':'hydro',
       'pumps':'battery','battery':'battery','bess':'battery',
       'wind':'wind','solar':'solar','solar_utility':'solar','solar_rooftop':'solar',
       'rooftop_solar':'solar','pv':'solar'}
VRE={'wind','solar'}; STOR={'battery'}
DEMAND_COLS=['demand','total_demand','operational_demand','load']
IMPORT_COLS=['imports','net_import','net_imports','interconnector','netinterchange']
TIME_COLS=['time','settlementdate','timestamp','date','interval']
PRICE_COLS=['price','rrp','spot_price']

def _norm(c): return str(c).strip().lower().replace(' ','_')

def load_region(csvpath, storage_hours=2.0, eff=0.9):
    df=pd.read_csv(csvpath)
    cols={_norm(c):c for c in df.columns}
    tcol=next((cols[c] for c in TIME_COLS if c in cols),None)
    if tcol is None: raise ValueError("no time column found")
    df['_t']=pd.to_datetime(df[tcol]); df=df.sort_values('_t').reset_index(drop=True)
    dcol=next((cols[c] for c in DEMAND_COLS if c in cols),None)
    if dcol is None: raise ValueError("no demand column found")
    icol=next((cols[c] for c in IMPORT_COLS if c in cols),None)
    pcol=next((cols[c] for c in PRICE_COLS if c in cols),None)
    used={tcol,dcol}|({icol} if icol else set())|({pcol} if pcol else set())
    fuel={}
    for c in df.columns:
        if c in used or c=='_t': continue
        key=_norm(c); tech=ALIAS.get(key,key)
        if pd.api.types.is_numeric_dtype(df[c]): fuel[c]=tech
    df['_date']=df['_t'].dt.date
    days=[]
    for d,g in df.groupby('_date'):
        T=len(g)
        demand=g[dcol].to_numpy(float)
        imports=g[icol].to_numpy(float) if icol else np.zeros(T)
        disp={}; vre_sum=np.zeros(T); stor_net=np.zeros(T); stor_pow=0.0
        for c,tech in fuel.items():
            s=np.nan_to_num(g[c].to_numpy(float))
            if tech in VRE: vre_sum+=np.clip(s,0,None)
            elif tech in STOR: stor_net+=s; stor_pow=max(stor_pow,np.abs(s).max())
            else:
                cap=max(np.nanmax(s)*1.15,1.0)
                if tech not in disp: disp[tech]={'mc':srmc(tech),'cap':cap,'gen':s.copy()}
                else:
                    disp[tech]['gen']=disp[tech]['gen']+s; disp[tech]['cap']+=cap
        vre={'vre':{'avail':vre_sum,'gen':vre_sum}}
        stor={}
        if stor_pow>0:
            P=stor_pow*1.1; E=P*storage_hours
            stor={'battery':{'P':P,'E':E,'eff':eff,'soe0':E*0.5,'net':stor_net}}
        days.append((str(d),demand,imports,disp,vre,stor,(g[pcol].to_numpy(float) if pcol else None)))
    return days
