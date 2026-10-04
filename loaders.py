"""AEMO MMSDM loaders -> pipeline structures. v1 expects CSVs with these columns:
 DUDETAILSUMMARY.csv : DUID, REGIONID, DISPATCHTYPE, TECH, MAXCAPACITY, STORAGE_MWH, EFF
 DISPATCHLOAD.csv    : SETTLEMENTDATE, DUID, DISPATCHMW          (signed for storage: +discharge,-charge)
 DISPATCHREGIONSUM.csv: SETTLEMENTDATE, REGIONID, TOTALDEMAND, NETINTERCHANGE   (+ = import into region)
 DISPATCHPRICE.csv   : SETTLEMENTDATE, REGIONID, RRP
 (optional) BIDS.csv : SETTLEMENTDATE, DUID, BIDPRICE
Real MMSDM tables map onto these with light renaming; battery gen/load DUIDs are merged to a signed net.
"""
import pandas as pd, numpy as np
from coordlib import srmc, VRE_TECHS, STOR_TECHS

def load(datadir, region):
    reg=pd.read_csv(f"{datadir}/DUDETAILSUMMARY.csv")
    reg=reg[reg.REGIONID==region].copy()
    ld=pd.read_csv(f"{datadir}/DISPATCHLOAD.csv", parse_dates=['SETTLEMENTDATE'])
    rs=pd.read_csv(f"{datadir}/DISPATCHREGIONSUM.csv", parse_dates=['SETTLEMENTDATE'])
    rs=rs[rs.REGIONID==region].sort_values('SETTLEMENTDATE')
    try:
        bids=pd.read_csv(f"{datadir}/BIDS.csv", parse_dates=['SETTLEMENTDATE'])
    except FileNotFoundError:
        bids=None
    times=rs.SETTLEMENTDATE.to_numpy()
    ld=ld[ld.DUID.isin(reg.DUID)]
    piv=ld.pivot_table(index='SETTLEMENTDATE',columns='DUID',values='DISPATCHMW',aggfunc='sum').reindex(times).fillna(0.0)
    units={}
    for _,r in reg.iterrows():
        tech=str(r.TECH).lower()
        units[r.DUID]=dict(tech=tech, cap=float(r.MAXCAPACITY), E=float(r.get('STORAGE_MWH',0) or 0),
                           eff=float(r.get('EFF',0.9) or 0.9),
                           kind=('storage' if tech in STOR_TECHS else 'vre' if tech in VRE_TECHS else 'disp'))
    pr=pd.read_csv(f"{datadir}/DISPATCHPRICE.csv", parse_dates=['SETTLEMENTDATE'])
    pr=pr[pr.REGIONID==region].set_index('SETTLEMENTDATE').reindex(times)
    return dict(times=times, demand=rs.TOTALDEMAND.to_numpy(float), imports=rs.NETINTERCHANGE.to_numpy(float),
                rrp=pr.RRP.to_numpy(float), gen=piv, units=units, bids=bids, region=region)
