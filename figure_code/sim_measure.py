"""Paper 3 — coordination MEASUREMENT demonstration.
Counterfactual identification on the companion co-optimisation model:
  Coordination Cost  CC   = 100*(C_dec - C_opt)/C_opt        (economic efficiency loss)
  Decision corr.     rho  = mean off-diagonal corr of agent deviations
  Coordination eff.  eta  = C_opt/C_dec = 1/(1+CC/100)  in (0,1]  (operator metric)
C_opt is the counterfactual co-optimised dispatch of the SAME fleet/network/weather;
C_dec is the realised decentralised outcome. Physical system identical -> isolates
coordination from capacity. Region points are CALIBRATED to the real NEM ordering
(SA>VIC>NSW>QLD>TAS) in renewable share and battery fleet; magnitudes are modelled.
"""
import sys, json, numpy as np
sys.path.append("/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/Submission/Code")
import sim

def metrics(pen, N, cfrac, cmag=0.30, seeds=20):
    scfi, rho, negfrac = sim.run_point(pen, N=N, cfrac=cfrac, cmag=cmag, seeds=seeds)
    eta = 100.0/(100.0+scfi)          # coordination efficiency in (0,1]
    return dict(CC=scfi, rho=rho, eta=eta, neg=negfrac)

out={}

# ---- five NEM regions, calibrated to the real ordering (VRE share, battery N, common-share) ----
regions = {
 "South Australia": dict(pen=0.78, N=10, cfrac=0.85),
 "Victoria":        dict(pen=0.66, N=9,  cfrac=0.80),
 "New South Wales": dict(pen=0.48, N=7,  cfrac=0.70),
 "Queensland":      dict(pen=0.42, N=6,  cfrac=0.65),
 "Tasmania":        dict(pen=0.30, N=3,  cfrac=0.25),   # hydro-dominated control
}
reg={}
for r,kw in regions.items():
    reg[r]=metrics(**kw)
out['regions']=reg

# ---- CC vs renewable penetration (fixed N) ----
pens=[0.30,0.40,0.50,0.60,0.70,0.80,0.90,0.97]
out['pen_sweep']=[dict(pen=p, **metrics(p, N=8, cfrac=0.75)) for p in pens]

# ---- CC vs battery penetration N (fixed high pen) ----
Ns=[2,4,6,8,10,12,16]
out['batt_sweep']=[dict(N=n, **metrics(0.80, N=n, cfrac=0.80)) for n in Ns]

# ---- driver dataset: vary pen, N, cfrac -> regress CC ----
rows=[]
rng=np.random.default_rng(3)
for pen in [0.4,0.55,0.7,0.85,0.95]:
    for N in [4,8,12]:
        for cfrac in [0.3,0.6,0.85]:
            m=metrics(pen,N,cfrac,seeds=12)
            rows.append([pen,N,cfrac,m['neg']/100,m['rho'],m['CC']])
rows=np.array(rows)
# UNIVARIATE variance explained by each driver (clean, collinearity-free) + slope sign
X=rows[:,:5]; y=rows[:,5]
names=['renewable penetration','battery count N','common-signal share','negative-price freq','decision correlation ρ']
def uni(col):
    x=X[:,col]; A=np.c_[np.ones(len(x)),x]; b,_,_,_=np.linalg.lstsq(A,y,rcond=None)
    r2=float(1-np.sum((y-A@b)**2)/np.sum((y-y.mean())**2)); return float(b[1]), r2
slopes=[]; r2s=[]
for c in range(5):
    sl,r2=uni(c); slopes.append(sl); r2s.append(r2)
out['regression']=dict(names=names, slope_sign=[int(np.sign(s)) for s in slopes], R2_univariate=r2s)
out['r2_pen_only']=r2s[0]; out['r2_rho_only']=r2s[4]

# ---- 8760-style heatmap: hour-of-day x month coordination cost (modelled) ----
# diurnal+seasonal VRE-surplus surface -> scales coordination cost (peaks high-VRE middays)
hrs=np.arange(24); mon=np.arange(1,13)
H,M=np.meshgrid(hrs,mon)
solar=np.clip(np.sin((H-6)/12*np.pi),0,None)                      # daytime
seas=0.7+0.3*np.cos((M-1)/12*2*np.pi)                             # spring/summer higher
surplus=solar*seas
base=metrics(0.72,8,0.8)['CC']
heat=base*(0.25+0.9*surplus/surplus.max())                       # CC% surface
out['heatmap']=dict(CC=heat.tolist())
# real anchors (published AEMO) for the paper
out['real_anchor']={'neg_SA_q4_2024':38.0,'neg_SA_q4_2025':48.4,'neg_VIC_q4_2024':34.3,'neg_VIC_q4_2025':43.1,
 'neg_NEM_q4_2024':23.1,'neg_NEM_q4_2025':31.0,'battery_GW_2026':7.5,'battery_add_2025_GW':4.8,'renew_share_q4_2025':51.0}

json.dump(out, open("/sessions/admiring-lucid-euler/mnt/outputs/measure_out.json","w"), default=float, indent=1)
print("REGIONS (CC%, rho, eta, neg%):")
for r,m in reg.items(): print("  %-16s CC=%4.1f  rho=%.2f  eta=%.2f  neg=%4.1f"%(r,m['CC'],m['rho'],m['eta'],m['neg']))
print("driver variance explained (R2):", {n:round(r,2) for n,r in zip(names,r2s)})
print("R2 penetration-only=%.2f  vs  rho-only=%.2f"%(out['r2_pen_only'],out['r2_rho_only']))
