"""Adapt an OpenElectricity region CSV (MW, sub-hourly) -> real coordination measurement."""
import sys, json, numpy as np, pandas as pd
from coordlib import day_metrics, srmc
from qa import check_metrics

def col(df, key):
    for c in df.columns:
        if c.strip().lower().startswith(key.lower()): return c
    return None

DISP={'Distillate':'diesel','Gas (Steam)':'gas_steam','Gas (CCGT)':'ccgt',
      'Gas (OCGT)':'ocgt','Gas (Reciprocating)':'ocgt','Coal (Brown)':'brown_coal','Coal (Black)':'black_coal','Hydro':'hydro','Bioenergy':'biomass'}
VREC={'Wind':'Wind (Curtailment)','Solar (Utility)':'Solar (Utility) (Curtailment)','Solar (Rooftop)':None}

def _read_many(path):
    import glob, os
    if os.path.isdir(path):
        files=sorted(glob.glob(os.path.join(path,'*.csv')))
    elif any(ch in path for ch in '*?['):
        files=sorted(glob.glob(path))
    else:
        files=[path]
    files=[f for f in files if 'measured' not in os.path.basename(f).lower()]
    if not files: raise FileNotFoundError(path)
    parts=[]
    for f in files:
        d=pd.read_csv(f); d.columns=[c.strip() for c in d.columns]; parts.append(d)
    df=pd.concat(parts, ignore_index=True)
    tcol=[c for c in df.columns if c.lower().startswith('date')][0]
    df=df.drop_duplicates(subset=[tcol]).reset_index(drop=True)
    print(f"stitched {len(files)} file(s) -> {len(df)} intervals")
    return df

def run(csv, region, out, storage_hours=2.0, eff=0.9):
    df=_read_many(csv); df.columns=[c.strip() for c in df.columns]
    tcol=col(df,'date'); df['_t']=pd.to_datetime(df[tcol]); df=df.sort_values('_t').reset_index(drop=True)
    g=lambda k:(pd.to_numeric(df[col(df,k)],errors='coerce').fillna(0).to_numpy() if col(df,k) is not None else np.zeros(len(df)))
    imports=g('Imports')+g('Exports')                       # net (exports stored negative)
    batt=g('Battery (Discharging)')+g('Battery (Charging)') # signed net (+dis, -charge)
    disp_cols={k:g(k) for k in DISP if col(df,k) is not None}
    wind=g('Wind'); su=g('Solar (Utility)'); sr=g('Solar (Rooftop)')
    vre_gen=wind+su+sr
    vre_avail=vre_gen+g('Wind (Curtailment)')+g('Solar (Utility) (Curtailment)')
    supply=sum(disp_cols.values())+vre_gen+np.maximum(batt,0)
    dcol=col(df,'demand')
    if dcol is not None:
        demand=pd.to_numeric(df[dcol],errors='coerce').fillna(0).to_numpy()
    else:
        demand=supply+imports-np.maximum(-batt,0)          # derive from balance when absent
    price=g('Price'); df['_date']=df['_t'].dt.date
    P=max(np.abs(batt).max()*1.1,1.0); E=P*storage_hours
    rows=[]; hourly=[]; viol=[]
    for d,idx in df.groupby('_date').groups.items():
        sl=np.array(idx); T=len(sl)
        disp={k:{'mc':srmc(DISP[k]),'cap':max(v[sl].max()*1.2,1.0),'gen':v[sl]} for k,v in disp_cols.items()}
        vre={'vre':{'avail':vre_avail[sl],'gen':vre_gen[sl]}}
        stor={'battery':{'P':P,'E':E,'eff':eff,'soe0':E*0.5,'net':batt[sl]}}
        m=day_metrics(demand[sl],imports[sl],disp,vre,stor)
        if m is None: continue
        mv=check_metrics(m); 
        if mv!=['ok']: viol.append({'date':str(d),'flags':mv})
        ren=100*vre_gen[sl].sum()/max(demand[sl].sum(),1e-9); neg=100*np.mean(price[sl]<0)
        rows.append(dict(date=str(d),CC=m['CC'],eta=m['eta'],rho=m['rho'],Cdec=m['Cdec'],Copt=m['Copt'],
                         ren_share=ren,neg_freq=neg,curtail_mwh=(vre_avail[sl]-vre_gen[sl]).sum()*0.5))
        gap=m['gap_t']; copt=np.maximum(m['Copt_t'],1e-9); per=max(1,T//24)
        for h in range(24):
            s2=sl[h*per:(h+1)*per]
            if len(s2): hourly.append(dict(date=str(d),hour=h,CC=100*(gap[h*per:(h+1)*per]).sum()/max(copt[h*per:(h+1)*per].sum(),1e-9)))
    R=pd.DataFrame(rows); R.to_csv(f"{out}_daily.csv",index=False); pd.DataFrame(hourly).to_csv(f"{out}_hourly.csv",index=False)
    summ=dict(region=region,source=csv.split('/')[-1],interval_min=int((df['_t'].iloc[1]-df['_t'].iloc[0]).total_seconds()/60),
              days=int(len(R)),period=f"{df['_t'].min()} to {df['_t'].max()}",
              CC_mean=float(R.CC.mean()),CC_median=float(R.CC.median()),CC_p90=float(R.CC.quantile(.9)),
              eta_mean=float(R.eta.mean()),rho_mean=float(np.nanmean(R.rho)),
              ren_share_mean=float(R.ren_share.mean()),neg_freq_mean=float(R.neg_freq.mean()),
              property_violations=len(viol))
    json.dump(summ,open(f"{out}_summary.json","w"),indent=2)
    json.dump({'summary':summ,'violations':viol},open(f"{out}_qa.json","w"),indent=2,default=str)
    print(json.dumps(summ,indent=2))
    return summ

if __name__=="__main__":
    run(sys.argv[1],sys.argv[2],sys.argv[3])
