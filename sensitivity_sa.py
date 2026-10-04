import numpy as np, pandas as pd
from coordlib import day_metrics, srmc
DISP={'Distillate':'diesel','Gas (Steam)':'gas_steam','Gas (CCGT)':'ccgt','Gas (OCGT)':'ocgt','Gas (Reciprocating)':'ocgt'}
def col(df,k):
    for c in df.columns:
        if c.strip().lower().startswith(k.lower()): return c
def g(df,k):
    c=col(df,k); return (pd.to_numeric(df[c],errors='coerce').fillna(0).to_numpy() if c else np.zeros(len(df)))
df=pd.read_csv("SA1_2025_api.csv"); df.columns=[c.strip() for c in df.columns]
df['_t']=pd.to_datetime(df[col(df,'date')],utc=True); df=df.sort_values('_t').reset_index(drop=True)
demand=g(df,'demand'); batt=g(df,'Battery (Discharging)')+g(df,'Battery (Charging)')
disp_cols={k:g(df,k) for k in DISP if col(df,k) is not None}
wind=g(df,'Wind -'); su=g(df,'Solar (Utility) -'); sr=g(df,'Solar (Rooftop)'); vre_gen=wind+su+sr
curt=g(df,'Wind (Curtailment)')+g(df,'Solar (Utility) (Curtailment)')
local=sum(disp_cols.values())+vre_gen+batt; imports=demand-local
df['_d']=df['_t'].dt.date; groups=df.groupby('_d').groups
def cc_annual(storage_hours=2.0, eff=0.9, use_curt=True, peaker_mult=1.0):
    P=max(np.abs(batt).max()*1.1,1.0); E=P*storage_hours
    sd=sc=0.0
    srmc_over={'ocgt':srmc('ocgt')*peaker_mult}
    for d,idx in groups.items():
        sl=np.array(idx); T=len(sl)
        if T<20: continue
        disp={k:{'mc':srmc_over.get(DISP[k],srmc(DISP[k])),'cap':max(v[sl].max()*1.3,1.0),'gen':v[sl]} for k,v in disp_cols.items()}
        avail=(vre_gen+curt) if use_curt else vre_gen
        vre={'vre':{'avail':avail[sl],'gen':vre_gen[sl]}}
        stor={'battery':{'P':P,'E':E,'eff':eff,'soe0':E*0.5,'net':batt[sl]}}
        m=day_metrics(demand[sl],imports[sl],disp,vre,stor)
        if m and m['Copt']>0: sd+=m['Cdec']; sc+=m['Copt']
    return 100*(sd-sc)/sc
print("BASE (2h,0.90,curt):           %.1f" % cc_annual())
print("storage 1h / 2h / 4h:          %.1f / %.1f / %.1f"%(cc_annual(storage_hours=1),cc_annual(storage_hours=2),cc_annual(storage_hours=4)))
print("battery eff 0.85 / 0.90 / 0.95:%.1f / %.1f / %.1f"%(cc_annual(eff=0.85),cc_annual(eff=0.90),cc_annual(eff=0.95)))
print("curtailment headroom on / off: %.1f / %.1f"%(cc_annual(use_curt=True),cc_annual(use_curt=False)))
print("peaker SRMC x0.8 / x1.0 / x1.2:%.1f / %.1f / %.1f"%(cc_annual(peaker_mult=0.8),cc_annual(peaker_mult=1.0),cc_annual(peaker_mult=1.2)))
