"""
coordlib — a pipeline to MEASURE coordination cost in the NEM from dispatch data.

Coordination cost   CC  = 100 * (C_dec - C_opt) / C_opt
Decision corr.      rho = mean off-diagonal corr of storage/flex deviations (realised - co-opt)
Coordination eff.   eta = C_opt / C_dec  in (0,1]

C_dec : operating cost of the REALISED dispatch (independent decisions), reconstructed from
        unit dispatch x reconstructed marginal cost.
C_opt : operating cost of the COUNTERFACTUAL co-optimised dispatch of the SAME fleet, the
        same realised availabilities, demand and net interconnector flow, solved as one LP.
Same physical system in both -> the gap is coordination, not capacity.

Inputs are AEMO MMSDM tables (see loaders); v1 is energy-only, per-region, solved day-by-day.
FCAS co-optimisation, network constraints and inter-day storage carry-over are documented
extensions (see README).
"""
import numpy as np, pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

# ---- technology default short-run marginal costs ($/MWh) used when bids are absent ----
TECH_SRMC = {'black_coal':42,'brown_coal':30,'ccgt':70,'ocgt':120,'gas':95,'gas_steam':85,
             'hydro':15,'biomass':50,'liquid':300,'diesel':320,'wind':0,'solar':0,'vre':0,
             'battery':0,'load':0,'other':80}
VRE_TECHS={'wind','solar','vre'}; STOR_TECHS={'battery'}
BACKSTOP=400.0  # $/MWh for any unserved energy in the counterfactual

def srmc(tech, bid=None):
    if bid is not None and np.isfinite(bid): return float(bid)
    return float(TECH_SRMC.get(str(tech).lower(), TECH_SRMC['other']))

# ---------------- co-optimisation of one day (T intervals) ----------------
def cooptimise_day(demand, imports, disp, vre, stor, mustrun=0.0):
    """demand[T], imports[T] (net import MW, +into region); disp/vre/stor are dicts:
       disp[u]={'mc':, 'cap':, 'gen':T}  vre[v]={'avail':T,'gen':T}
       stor[s]={'P':,'E':,'eff':,'soe0':,'net':T(realised dis-ch)}  -> returns C_opt, schedules"""
    T=len(demand); U=list(disp); V=list(vre); S=list(stor)
    nU,nV,nS=len(U),len(V),len(S)
    oG=0; oVU=nU*T; oCH=oVU+nV*T; oDIS=oCH+nS*T; oSOE=oDIS+nS*T; oUNS=oSOE+nS*T; nvar=oUNS+T
    c=np.zeros(nvar); bnd=[(0,None)]*nvar
    for i,u in enumerate(U):
        mc=disp[u]['mc']
        gen_u=np.asarray(disp[u]['gen'])
        for t in range(T): c[oG+i*T+t]=mc; bnd[oG+i*T+t]=(mustrun*max(gen_u[t],0),disp[u]['cap'])
    for j,v in enumerate(vre):
        for t in range(T): c[oVU+j*T+t]=0.0; bnd[oVU+j*T+t]=(0,max(vre[v]['avail'][t],0))
    eps=0.5
    for k,s in enumerate(S):
        P=stor[s]['P']; E=stor[s]['E']
        for t in range(T):
            c[oCH+k*T+t]=eps; c[oDIS+k*T+t]=eps
            bnd[oCH+k*T+t]=(0,P); bnd[oDIS+k*T+t]=(0,P); bnd[oSOE+k*T+t]=(0,E)
    for t in range(T): c[oUNS+t]=BACKSTOP
    A=[]; b=[]
    # balance (equality): gen + vre_used + (dis-ch) + imports + unserved = demand
    for t in range(T):
        row=np.zeros(nvar)
        for i in range(nU): row[oG+i*T+t]=1
        for j in range(nV): row[oVU+j*T+t]=1
        for k in range(nS): row[oDIS+k*T+t]=1; row[oCH+k*T+t]=-1
        row[oUNS+t]=1
        A.append(row); b.append(demand[t]-imports[t])
    # soe dynamics (equality)
    for k,s in enumerate(S):
        eff=stor[s]['eff']; soe0=stor[s]['soe0']
        for t in range(T):
            row=np.zeros(nvar); row[oSOE+k*T+t]=1
            if t>0: row[oSOE+k*T+t-1]=-1
            row[oCH+k*T+t]=-eff; row[oDIS+k*T+t]=1/eff
            A.append(row); b.append(soe0 if t==0 else 0.0)
    Aub=[]; bub=[]
    for i,u in enumerate(U):
        bud=disp[u].get('budget',None)
        if bud is not None:
            row=np.zeros(nvar); 
            for t in range(T): row[oG+i*T+t]=1
            Aub.append(row); bub.append(float(bud))
    kw=dict(A_eq=csr_matrix(np.array(A)),b_eq=np.array(b),bounds=bnd,method='highs')
    if Aub: kw['A_ub']=csr_matrix(np.array(Aub)); kw['b_ub']=np.array(bub)
    res=linprog(c,**kw)
    if not res.success: return None
    x=res.x
    # C_opt = fuel cost of dispatchable gen (exclude eps regulariser & backstop in the comparable cost)
    Copt=sum(disp[u]['mc']*x[oG+i*T:oG+i*T+T].sum() for i,u in enumerate(U))
    stor_opt={s:(x[oDIS+k*T:oDIS+k*T+T]-x[oCH+k*T:oCH+k*T+T]) for k,s in enumerate(S)}
    Copt_t=np.zeros(T)
    for i,u in enumerate(U): Copt_t+=disp[u]['mc']*x[oG+i*T:oG+i*T+T]
    return dict(Copt=Copt, stor_opt=stor_opt, Copt_t=Copt_t)

def realised_cost(disp):
    """C_dec = reconstructed cost of the realised dispatchable generation."""
    return sum(d['mc']*np.asarray(d['gen']).sum() for d in disp.values())

def day_metrics(demand, imports, disp, vre, stor, mustrun=0.0):
    co=cooptimise_day(demand,imports,disp,vre,stor,mustrun=mustrun)
    if co is None: return None
    Cdec=realised_cost(disp); Copt=co['Copt']
    if Copt<=0: return None
    CC=100*(Cdec-Copt)/Copt; eta=Copt/Cdec if Cdec>0 else 1.0
    T=len(demand); Cdec_t=np.zeros(T)
    for u in disp: Cdec_t+=disp[u]['mc']*np.asarray(disp[u]['gen'])
    gap_t=Cdec_t-co['Copt_t']
    # decision correlation among storage units: realised net vs co-opt net deviation
    S=list(stor); dev=[]
    for s in S:
        d=np.asarray(stor[s]['net'])-co['stor_opt'][s]; dev.append(d)
    rho=np.nan
    if len(dev)>1:
        R=np.corrcoef(np.array(dev)); rho=(np.nansum(R)-np.trace(R))/(len(S)*(len(S)-1))
    return dict(CC=CC, eta=eta, rho=float(rho), Cdec=Cdec, Copt=Copt, gap_t=gap_t, Copt_t=co['Copt_t'])
