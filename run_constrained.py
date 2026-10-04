"""Security-constrained counterfactual: min-generation (must-run) floors + ramp limits.
Reports CC as a function of must-run stringency, and a fuel-group response correlation."""
import sys, json, numpy as np, pandas as pd
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from coordlib import srmc
DISP={'Distillate':'diesel','Gas (Steam)':'gas_steam','Gas (CCGT)':'ccgt','Gas (OCGT)':'ocgt','Gas (Reciprocating)':'ocgt','Hydro':'hydro'}
def col(df,k):
    for c in df.columns:
        if c.strip().lower().startswith(k.lower()): return c
def g(df,k):
    c=col(df,k); return (pd.to_numeric(df[c],errors='coerce').fillna(0).to_numpy() if c else np.zeros(len(df)))

def load(csv):
    df=pd.read_csv(csv); df.columns=[c.strip() for c in df.columns]
    df['_t']=pd.to_datetime(df[col(df,'date')],utc=True); df=df.sort_values('_t').reset_index(drop=True)
    demand=g(df,'demand'); batt=g(df,'Battery (Discharging)')+g(df,'Battery (Charging)')
    disp={k:g(df,k) for k in DISP if col(df,k) is not None and g(df,k).max()>0}
    wind=g(df,'Wind -'); su=g(df,'Solar (Utility) -'); sr=g(df,'Solar (Rooftop)'); vre=wind+su+sr
    avail=vre+g(df,'Wind (Curtailment)')+g(df,'Solar (Utility) (Curtailment)')
    local=sum(disp.values())+vre+batt; imports=demand-local
    df['_d']=df['_t'].dt.date
    return df,demand,imports,disp,vre,avail,batt

def cc_constrained(csv, mustrun=0.0, ramp_frac=0.5, storage_hours=2.0, eff=0.9, want_rho=False):
    df,demand,imports,disp,vre,avail,batt=load(csv)
    U=list(disp); caps={u:max(disp[u].max()*1.3,1.0) for u in U}
    P=max(np.abs(batt).max()*1.1,1.0); E=P*storage_hours
    sumC=sumO=0.0; devs={u:[] for u in U}; devs['battery']=[]
    for d,idx in df.groupby('_d').groups.items():
        sl=np.array(idx); T=len(sl)
        if T<20: continue
        nU=len(U); oG=0; oVU=nU*T; oCH=oVU+T; oDIS=oCH+T; oSOE=oDIS+T; oUNS=oSOE+T; nv=oUNS+T
        c=np.zeros(nv); bnd=[(0,None)]*nv
        for i,u in enumerate(U):
            mc=srmc(DISP[u]); real=disp[u][sl]
            for t in range(T):
                c[oG+i*T+t]=mc; bnd[oG+i*T+t]=(mustrun*real[t], caps[u])   # must-run floor
        for t in range(T): bnd[oVU+t]=(0,max(avail[sl][t],0))
        eps=0.5
        for t in range(T): c[oCH+t]=eps;c[oDIS+t]=eps;bnd[oCH+t]=(0,P);bnd[oDIS+t]=(0,P);bnd[oSOE+t]=(0,E)
        for t in range(T): c[oUNS+t]=400.0
        A=[];b=[]
        for t in range(T):
            row=np.zeros(nv)
            for i in range(nU): row[oG+i*T+t]=1
            row[oVU+t]=1; row[oDIS+t]=1; row[oCH+t]=-1; row[oUNS+t]=1
            A.append(row); b.append(demand[sl][t]-imports[sl][t])
        soe0=E*0.5
        for t in range(T):
            row=np.zeros(nv); row[oSOE+t]=1
            if t>0: row[oSOE+t-1]=-1
            row[oCH+t]=-eff; row[oDIS+t]=1/eff
            A.append(row); b.append(soe0 if t==0 else 0.0)
        Aub=[];bub=[]
        R={u:ramp_frac*caps[u] for u in U}
        for i,u in enumerate(U):
            for t in range(1,T):
                r1=np.zeros(nv); r1[oG+i*T+t]=1; r1[oG+i*T+t-1]=-1; Aub.append(r1); bub.append(R[u])
                r2=np.zeros(nv); r2[oG+i*T+t]=-1; r2[oG+i*T+t-1]=1; Aub.append(r2); bub.append(R[u])
        res=linprog(c,A_ub=csr_matrix(np.array(Aub)),b_ub=np.array(bub),
                    A_eq=csr_matrix(np.array(A)),b_eq=np.array(b),bounds=bnd,method='highs')
        if not res.success: continue
        x=res.x
        Copt=sum(srmc(DISP[u])*x[oG+i*T:oG+i*T+T].sum() for i,u in enumerate(U))
        Cdec=sum(srmc(DISP[u])*disp[u][sl].sum() for u in U)
        if Copt<=0: continue
        sumC+=Cdec; sumO+=Copt
        if want_rho:
            for i,u in enumerate(U): devs[u].append(disp[u][sl]-x[oG+i*T:oG+i*T+T])
            devs['battery'].append(batt[sl]-(x[oDIS:oDIS+T]-x[oCH:oCH+T]))
    cc=100*(sumC-sumO)/sumO
    rho=np.nan
    if want_rho:
        series={k:np.concatenate(v) for k,v in devs.items() if v}
        keys=[k for k in series if np.std(series[k])>1e-6]
        if len(keys)>1:
            M=np.vstack([series[k] for k in keys]); R=np.corrcoef(M)
            rho=(np.nansum(R)-np.trace(R))/(len(keys)*(len(keys)-1))
    return cc,rho

if __name__=="__main__":
    SD="/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/Submission3/Source_Data/"
    reg=sys.argv[1] if len(sys.argv)>1 else "SA1"
    csv=SD+f"{reg}_2025_api.csv"
    print(f"[{reg}] must-run sweep (ramp {0.5}cap/h):")
    for mr in [0.0,0.25,0.5,0.75]:
        cc,rho=cc_constrained(csv,mustrun=mr,want_rho=(mr==0.0))
        print(f"  must-run={mr:.2f}  CC={cc:5.1f}%"+(f"  fuel-group rho={rho:+.2f}" if mr==0.0 else ""))
