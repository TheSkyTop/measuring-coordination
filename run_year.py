"""Full-year coordination measurement. Full dispatchable fleet (coal+gas+hydro+distillate+bio);
rooftop excluded (operational demand is net of it); hydro under a daily energy budget; net
interconnector from the balance. Cost-weighted annual CC. Optional must-run."""
import sys, json, numpy as np, pandas as pd
from coordlib import day_metrics, srmc
DISP={'Distillate':'diesel','Gas (Steam)':'gas_steam','Gas (CCGT)':'ccgt','Gas (OCGT)':'ocgt',
      'Gas (Reciprocating)':'ocgt','Coal (Black)':'black_coal','Coal (Brown)':'brown_coal',
      'Hydro':'hydro','Bioenergy':'biomass'}
def col(df,k):
    for c in df.columns:
        if c.strip().lower().startswith(k.lower()): return c
    return None
def g(df,k):
    c=col(df,k); return (pd.to_numeric(df[c],errors='coerce').fillna(0).to_numpy() if c else np.zeros(len(df)))
def main(csv, out, region="NEM", mustrun=0.0, storage_hours=2.0, eff=0.9):
    df=pd.read_csv(csv); df.columns=[c.strip() for c in df.columns]
    t=pd.to_datetime(df[col(df,'date')],utc=True); df=df.assign(_t=t).sort_values('_t').reset_index(drop=True)
    demand=g(df,'demand')
    batt=g(df,'Battery (Discharging)')+g(df,'Battery (Charging)')
    disp_cols={k:g(df,k) for k in DISP if col(df,k) is not None and g(df,k).max()>1}
    wind=g(df,'Wind -'); su=g(df,'Solar (Utility) -')
    vre_gen=wind+su
    vre_avail=vre_gen+g(df,'Wind (Curtailment)')+g(df,'Solar (Utility) (Curtailment)')
    local=sum(disp_cols.values())+vre_gen+batt
    imports=demand-local
    price=g(df,'Price'); df['_d']=pd.to_datetime(df['_t']).dt.date
    P=max(np.abs(batt).max()*1.1,1.0); E=P*storage_hours
    rows=[]; hourly=[]; sumCdec=sumCopt=0.0
    for d,idx in df.groupby('_d').groups.items():
        sl=np.array(idx); T=len(sl)
        if T<20: continue
        disp={}
        for k,v in disp_cols.items():
            e={'mc':srmc(DISP[k]),'cap':max(v[sl].max()*1.3,1.0),'gen':v[sl]}
            if DISP[k]=='hydro': e['budget']=v[sl].sum()
            disp[k]=e
        vre={'vre':{'avail':vre_avail[sl],'gen':vre_gen[sl]}}
        stor={'battery':{'P':P,'E':E,'eff':eff,'soe0':E*0.5,'net':batt[sl]}}
        m=day_metrics(demand[sl],imports[sl],disp,vre,stor,mustrun=mustrun)
        if m is None or m['Copt']<=0: continue
        sumCdec+=m['Cdec']; sumCopt+=m['Copt']
        ren=100*vre_gen[sl].sum()/max((vre_gen[sl].sum()+sum(v[sl].sum() for v in disp_cols.values())+np.maximum(imports[sl],0).sum()),1e-9)
        rows.append(dict(date=str(d),CC=m['CC'],eta=m['eta'],Cdec=m['Cdec'],Copt=m['Copt'],ren_share=ren,neg_freq=100*np.mean(price[sl]<0),curtail_mwh=(vre_avail[sl]-vre_gen[sl]).sum()))
        gap=m['gap_t']; copt=m['Copt_t']; per=max(1,T//24); mon=pd.to_datetime(str(d)).month
        for h in range(24):
            a,b=h*per,(h+1)*per
            hourly.append(dict(month=mon,hour=h,gap=gap[a:b].sum(),copt=copt[a:b].sum()))
    R=pd.DataFrame(rows); H=pd.DataFrame(hourly)
    R.to_csv(f"{out}_daily.csv",index=False)
    Hg=H.groupby(['month','hour']).agg(gap=('gap','sum'),copt=('copt','sum')).reset_index()
    Hg['CC']=100*Hg['gap']/Hg['copt'].clip(lower=1e-9)
    Hg.pivot(index='month',columns='hour',values='CC').to_csv(f"{out}_heatmap.csv")
    cc=100*(sumCdec-sumCopt)/sumCopt
    summ={"region":region,"mustrun":mustrun,"full_days":int(len(R)),
          "CC_annual_costweighted":round(cc,2),"eta_annual":round(sumCopt/sumCdec,4),
          "CC_daily_median":round(float(R.CC.median()),2),
          "neg_freq_annual":round(float(R.neg_freq.mean()),2),"ren_share_annual":round(float(R.ren_share.mean()),2),
          "total_curtailment_GWh":round(float(R.curtail_mwh.sum())/1000,1),
          "corr_CC_renshare":round(float(np.corrcoef(R.CC.clip(upper=R.CC.quantile(.95)),R.ren_share)[0,1]),3),
          "corr_CC_negprice":round(float(np.corrcoef(R.CC.clip(upper=R.CC.quantile(.95)),R.neg_freq)[0,1]),3)}
    json.dump(summ,open(f"{out}_summary.json","w"),indent=2); print(json.dumps(summ))
if __name__=="__main__":
    reg=sys.argv[3] if len(sys.argv)>3 else "NEM"
    mr=float(sys.argv[4]) if len(sys.argv)>4 else 0.0
    main(sys.argv[1], sys.argv[2], region=reg, mustrun=mr)
