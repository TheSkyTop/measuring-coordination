import sys, json, numpy as np, pandas as pd
from coordlib import day_metrics, srmc
from loaders import load

def run(datadir, region, out_prefix):
    D=load(datadir, region); times=pd.to_datetime(D['times'])
    day=pd.Series(times).dt.floor('D').to_numpy()
    rows=[]; gap_all=np.full(len(times),np.nan); copt_all=np.full(len(times),np.nan)
    for d in pd.unique(day):
        idx=np.where(day==d)[0]
        if len(idx)<6: continue
        dem=D['demand'][idx]; imp=D['imports'][idx]
        disp={};vre={};stor={}
        for duid,u in D['units'].items():
            g=D['gen'][duid].to_numpy()[idx] if duid in D['gen'] else np.zeros(len(idx))
            if u['kind']=='disp': disp[duid]=dict(mc=srmc(u['tech']),cap=u['cap'],gen=np.clip(g,0,None))
            elif u['kind']=='vre': vre[duid]=dict(avail=np.clip(g,0,None),gen=np.clip(g,0,None))
            else: stor[duid]=dict(P=u['cap'],E=u['E'] if u['E']>0 else u['cap']*2,eff=u['eff'],
                                  soe0=(u['E'] if u['E']>0 else u['cap']*2)/2,net=g)
        if not disp or not stor: continue
        ren=sum(np.asarray(v['gen']).sum() for v in vre.values()); rs_share=100*ren/max(dem.sum(),1e-6)
        rrp=D['rrp'][idx]; negf=100*np.mean(rrp<0)
        m=day_metrics(dem,imp,disp,vre,stor)
        if m is None: continue
        rows.append(dict(date=pd.Timestamp(d).date().isoformat(),
                         CC=round(m['CC'],3),eta=round(m['eta'],4),rho=round(m['rho'],3),
                         Cdec=round(m['Cdec'],1),Copt=round(m['Copt'],1),ren_share=round(rs_share,1),neg_freq=round(negf,1)))
        gap_all[idx]=m['gap_t']; copt_all[idx]=m['Copt_t']
    res=pd.DataFrame(rows); res.to_csv(f"{out_prefix}_daily.csv",index=False)
    # hourly CC (8760): aggregate per-interval gap and opt cost to the hour
    ts=pd.DataFrame({'t':times,'gap':gap_all,'copt':copt_all}).dropna()
    ts['hour']=ts.t.dt.floor('h')
    hr=ts.groupby('hour').agg(gap=('gap','sum'),copt=('copt','sum')).reset_index()
    hr['CC']=100*hr.gap/hr.copt.replace(0,np.nan)
    hr.to_csv(f"{out_prefix}_hourly.csv",index=False)
    # hour-of-day x month heatmap of mean CC
    hr['hod']=hr.hour.dt.hour; hr['mon']=hr.hour.dt.month
    hm=hr.pivot_table(index='mon',columns='hod',values='CC',aggfunc='mean')
    hm.to_csv(f"{out_prefix}_heatmap.csv")
    summ=dict(region=region,days=int(len(res)),hours=int(len(hr)),
              CC_mean=float(res.CC.mean()),CC_median=float(res.CC.median()),CC_p90=float(res.CC.quantile(.9)),
              eta_mean=float(res.eta.mean()),rho_mean=float(res.rho.mean()))
    json.dump(summ,open(f"{out_prefix}_summary.json","w"),indent=1)
    print(f"[{region}] days={summ['days']} hours={summ['hours']}  CC_mean={summ['CC_mean']:.1f}%  CC_p90={summ['CC_p90']:.1f}%  eta={summ['eta_mean']:.3f}  rho={summ['rho_mean']:.2f}")
    return res,hr,hm,summ

if __name__=="__main__":
    a=sys.argv; run(a[1] if len(a)>1 else "data_synth", a[2] if len(a)>2 else "SA1", a[3] if len(a)>3 else "outputs_metrics/SA1")
