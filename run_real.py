"""
run_real.py — produce REAL coordination metrics from a single regional CSV.

Usage:
    python run_real.py data_real/SA1_2025.csv SA1 outputs_real/SA1

Outputs (same schema as the unit-level path):
    {out}_daily.csv    date, CC, eta, rho, Cdec, Copt, ren_share, neg_freq
    {out}_hourly.csv   hour-resolution CC (the 8760 series when a full year is supplied)
    {out}_summary.json CC mean/median/p90, eta, rho, coverage
"""
import sys, json, numpy as np, pandas as pd
from loaders_aggregate import load_region
from coordlib import day_metrics
from qa import check_input, check_metrics, storage_sensitivity

def main(csv, region, out):
    inq=check_input(csv)
    print('input QA:', 'OK' if inq['ok'] else 'FAILED', '|', '; '.join(inq['issues']))
    if not inq['ok']:
        print('refusing to measure on invalid input'); return
    days=load_region(csv)
    rows=[]; hourly=[]; viol=[]
    for date,demand,imports,disp,vre,stor,price in days:
        m=day_metrics(demand,imports,disp,vre,stor)
        if m is None: continue
        mv=check_metrics(m)
        if mv!=['ok']: viol.append({'date':date,'flags':mv})
        T=len(demand)
        vre_tot=float(vre['vre']['gen'].sum()); ren_share=100*vre_tot/max(demand.sum(),1e-9)
        neg=100*np.mean(price<0) if price is not None else np.nan
        rows.append(dict(date=date,CC=m['CC'],eta=m['eta'],rho=m['rho'],
                         Cdec=m['Cdec'],Copt=m['Copt'],ren_share=ren_share,neg_freq=neg))
        # hourly CC from interval gap
        gap=m['gap_t']; copt=np.maximum(m['Copt_t'],1e-9)
        per=max(1,T//24)
        for h in range(24):
            sl=slice(h*per,(h+1)*per)
            cc_h=100*gap[sl].sum()/max(copt[sl].sum(),1e-9)
            hourly.append(dict(date=date,hour=h,CC=cc_h))
    d=pd.DataFrame(rows)
    if d.empty: print("no solvable days — check CSV columns"); return
    d.to_csv(f"{out}_daily.csv",index=False)
    pd.DataFrame(hourly).to_csv(f"{out}_hourly.csv",index=False)
    summ=dict(region=region,days=int(len(d)),
              CC_mean=float(d.CC.mean()),CC_median=float(d.CC.median()),CC_p90=float(d.CC.quantile(.9)),
              eta_mean=float(d.eta.mean()),rho_mean=float(np.nanmean(d.rho)),
              ren_share_mean=float(d.ren_share.mean()),neg_freq_mean=float(np.nanmean(d.neg_freq)))
    summ['property_violations']=len(viol)
    sens=storage_sensitivity(csv,region)
    summ['storage_duration_sensitivity_CCmean']=sens
    json.dump(summ,open(f"{out}_summary.json","w"),indent=2)
    json.dump({'input_qa':inq,'property_violations':viol,'storage_sensitivity':sens},
              open(f"{out}_qa.json","w"),indent=2,default=str)
    print(f"REAL measurement [{region}]  days={summ['days']}  "
          f"CC_mean={summ['CC_mean']:.2f}%  eta={summ['eta_mean']:.3f}  "
          f"CC_p90={summ['CC_p90']:.2f}%  ren_share={summ['ren_share_mean']:.1f}%")
    print(f"  property checks: {len(viol)} violations | storage-duration CC range: {sens}")

if __name__=="__main__":
    csv,region,out=sys.argv[1],sys.argv[2],sys.argv[3]
    import os; os.makedirs(os.path.dirname(out) or '.',exist_ok=True)
    main(csv,region,out)
