import glob, json, numpy as np, pandas as pd, matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Liberation Sans','Arial','DejaVu Sans'],
 'pdf.fonttype':42,'figure.dpi':600,'savefig.dpi':600,'axes.linewidth':0.75,'axes.spines.top':False,
 'axes.spines.right':False,'font.size':8,'axes.titlesize':9,'axes.labelsize':7.5,'xtick.labelsize':7,'ytick.labelsize':7})
NAVY='#1F4E79'; ORANGE='#F28E2B'; TEAL='#00897B'; GREY='#808080'
OUT="figures/"; import os; os.makedirs(OUT,exist_ok=True)
def save(n): plt.savefig(OUT+n+'.pdf'); plt.savefig(OUT+n+'.png',bbox_inches='tight'); plt.close()
REGS=['SA1','VIC1','NSW1','QLD1','TAS1']; NAMES={'SA1':'South Australia','VIC1':'Victoria','NSW1':'New South Wales','QLD1':'Queensland','TAS1':'Tasmania'}

# ---- Fig A: 8760-style heatmap (SA, hour-of-day x month) ----
hm=pd.read_csv("outputs/SA1_heatmap.csv",index_col=0)
fig,ax=plt.subplots(figsize=(7.2,3.2))
im=ax.imshow(hm.values,aspect='auto',origin='lower',cmap='YlOrBr',extent=[0,24,0.5,hm.shape[0]+0.5])
ax.set_xlabel('Hour of day'); ax.set_ylabel('Month'); ax.set_xticks([0,6,12,18,24]); ax.set_yticks(range(1,hm.shape[0]+1))
ax.set_title('Coordination cost — South Australia (pipeline output, hour × month)',fontsize=8.4,fontweight='bold')
cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.02); cb.set_label('coordination cost (% above optimum)',fontsize=7)
ax.spines['top'].set_visible(True); ax.spines['right'].set_visible(True); plt.tight_layout(); save('fig_heatmap_SA')

# ---- Fig B: regional comparison ----
summ={r:json.load(open(f"outputs/{r}_summary.json")) for r in REGS}
cc=[summ[r]['CC_mean'] for r in REGS]; rho=[summ[r]['rho_mean'] for r in REGS]
cols=[ORANGE,ORANGE,NAVY,NAVY,TEAL]
fig,ax=plt.subplots(figsize=(7.2,3.3)); x=np.arange(5)
ax.bar(x,cc,0.6,color=cols)
for i,v in enumerate(cc): ax.text(i,v+0.05,f'{v:.1f}%',ha='center',fontsize=7.5,fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([NAMES[r].replace(' ','\n') for r in REGS],fontsize=7)
ax.set_ylabel('Mean coordination cost (%)'); ax.set_title('Regional coordination cost (pipeline output)',fontsize=8.6,fontweight='bold')
plt.tight_layout(); save('fig_regional')

# ---- Fig C: drivers (CC vs rho across all region-days) + variance explained ----
df=pd.concat([pd.read_csv(f"outputs/{r}_daily.csv").assign(region=r) for r in REGS],ignore_index=True)
df=df.dropna(subset=['CC','rho','ren_share','neg_freq'])
def r2(x,y):
    A=np.c_[np.ones(len(x)),x]; b,_,_,_=np.linalg.lstsq(A,y,rcond=None); return 1-np.sum((y-A@b)**2)/np.sum((y-y.mean())**2)
drivers={'decision corr ρ':r2(df.rho.values,df.CC.values),'renewable share':r2(df.ren_share.values,df.CC.values),'neg-price freq':r2(df.neg_freq.values,df.CC.values)}
fig,(a1,a2)=plt.subplots(1,2,figsize=(7.6,3.2))
cmap={'SA1':ORANGE,'VIC1':ORANGE,'NSW1':NAVY,'QLD1':NAVY,'TAS1':TEAL}
for r in REGS:
    d=df[df.region==r]; a1.scatter(d.rho,d.CC,s=6,alpha=0.4,color=cmap[r],label=NAMES[r])
a1.set_xlabel('decision correlation ρ (daily)'); a1.set_ylabel('coordination cost (%)')
a1.set_title('a  Coordination cost vs decision correlation',fontsize=8.2,fontweight='bold'); a1.legend(fontsize=5.5,frameon=False)
dn=list(drivers); r2s=[drivers[k] for k in dn]; o=np.argsort(r2s); dn=[dn[i] for i in o]; r2s=[r2s[i] for i in o]
a2.barh(range(len(dn)),r2s,color=[NAVY if 'ρ' in d else GREY for d in dn])
for i,v in enumerate(r2s): a2.text(v+0.01,i,f'{v:.2f}',va='center',fontsize=7.5)
a2.set_yticks(range(len(dn))); a2.set_yticklabels(dn,fontsize=7.2); a2.set_xlabel('variance of CC explained (R²)'); a2.set_xlim(0,1)
a2.set_title('b  What explains coordination cost',fontsize=8.2,fontweight='bold')
plt.tight_layout(); save('fig_drivers')
print("figures written:", os.listdir(OUT))
print("driver R²:", {k:round(v,2) for k,v in drivers.items()})
