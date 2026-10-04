import json, glob, numpy as np, pandas as pd, matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Liberation Sans','Arial','DejaVu Sans'],
 'pdf.fonttype':42,'figure.dpi':600,'savefig.dpi':600,'axes.linewidth':0.75,'axes.spines.top':False,
 'axes.spines.right':False,'font.size':8,'axes.titlesize':9,'axes.labelsize':7.5,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':6.5})
NAVY='#1F4E79'; ORANGE='#F28E2B'; TEAL='#00897B'; GREY='#808080'
PIPE="/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/coordination_pipeline/outputs_metrics/"
OUT="/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/Submission3/Figures/"
def save(n): plt.savefig(OUT+n+'.pdf'); plt.savefig(OUT+n+'.png'); plt.close()
REGS=['SA1','VIC1','NSW1','QLD1','TAS1']; NAMES={'SA1':'South Australia','VIC1':'Victoria','NSW1':'New South Wales','QLD1':'Queensland','TAS1':'Tasmania'}
def r2(x,y):
    A=np.c_[np.ones(len(x)),x]; b,_,_,_=np.linalg.lstsq(A,y,rcond=None); return 1-np.sum((y-A@b)**2)/np.sum((y-y.mean())**2)

# F4 heatmap (SA)
hm=pd.read_csv(PIPE+"SA1_heatmap.csv",index_col=0)
fig,ax=plt.subplots(figsize=(7.2,3.2))
im=ax.imshow(hm.values,aspect='auto',origin='lower',cmap='YlOrBr',extent=[0,24,0.5,hm.shape[0]+0.5])
ax.set_xlabel('Hour of day'); ax.set_ylabel('Month'); ax.set_xticks([0,6,12,18,24]); ax.set_yticks(range(1,hm.shape[0]+1))
ax.set_title('Coordination cost across the day and year — South Australia (pipeline output)',fontsize=8.2,fontweight='bold')
cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.02); cb.set_label('coordination cost (% above optimum)',fontsize=7)
ax.spines['top'].set_visible(True); ax.spines['right'].set_visible(True); plt.tight_layout(); save('Figure4')

# F5 regional
summ={r:json.load(open(PIPE+f"{r}_summary.json")) for r in REGS}
cc=[summ[r]['CC_mean'] for r in REGS]; cols=[ORANGE,ORANGE,NAVY,NAVY,TEAL]
fig,ax=plt.subplots(figsize=(7.2,3.3)); x=np.arange(5); ax.bar(x,cc,0.6,color=cols)
for i,v in enumerate(cc): ax.text(i,v+0.04,f'{v:.1f}%',ha='center',fontsize=7.5,fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([NAMES[r].replace(' ','\n') for r in REGS],fontsize=7)
ax.set_ylabel('Mean coordination cost (%)'); ax.set_title('Coordination cost by region (pipeline output)',fontsize=8.6,fontweight='bold')
plt.tight_layout(); save('Figure5')

# pooled daily across regions
df=pd.concat([pd.read_csv(PIPE+f"{r}_daily.csv").assign(region=r) for r in REGS],ignore_index=True).dropna(subset=['CC','rho','ren_share','neg_freq'])
cmap={'SA1':ORANGE,'VIC1':ORANGE,'NSW1':NAVY,'QLD1':NAVY,'TAS1':TEAL}
# F6 CC vs renewable share
fig,ax=plt.subplots(figsize=(7.2,3.1))
for r in REGS:
    d=df[df.region==r]; ax.scatter(d.ren_share,d.CC,s=6,alpha=0.4,color=cmap[r],label=NAMES[r])
z=np.polyfit(df.ren_share,df.CC,1); xs=np.linspace(df.ren_share.min(),df.ren_share.max(),50); ax.plot(xs,np.polyval(z,xs),'--',color=GREY,lw=1)
ax.set_xlabel('renewable share (%, daily)'); ax.set_ylabel('coordination cost (%)')
ax.set_title(f'Coordination cost vs renewable share (pipeline output; R²={r2(df.ren_share.values,df.CC.values):.2f})',fontsize=8.0,fontweight='bold')
ax.legend(fontsize=6,frameon=False,ncol=2); plt.tight_layout(); save('Figure6')
# F7 CC vs negative-price frequency (Finding 5: explains only part)
fig,ax=plt.subplots(figsize=(7.2,3.1))
for r in REGS:
    d=df[df.region==r]; ax.scatter(d.neg_freq,d.CC,s=6,alpha=0.4,color=cmap[r])
ax.set_xlabel('negative-price frequency (%, daily)'); ax.set_ylabel('coordination cost (%)')
ax.set_title(f'Negative-price frequency explains only part of coordination cost (R²={r2(df.neg_freq.values,df.CC.values):.2f})',fontsize=7.8,fontweight='bold')
plt.tight_layout(); save('Figure7')
# F8 drivers variance explained
drivers={'decision correlation ρ':r2(df.rho.values,df.CC.values),'renewable share':r2(df.ren_share.values,df.CC.values),'negative-price freq':r2(df.neg_freq.values,df.CC.values)}
dn=list(drivers); v=[drivers[k] for k in dn]; o=np.argsort(v); dn=[dn[i] for i in o]; v=[v[i] for i in o]
fig,ax=plt.subplots(figsize=(7.2,3.0)); ax.barh(range(len(dn)),v,color=[NAVY if 'ρ' in d else GREY for d in dn])
for i,val in enumerate(v): ax.text(val+0.005,i,f'{val:.2f}',va='center',fontsize=7.5)
ax.set_yticks(range(len(dn))); ax.set_yticklabels(dn,fontsize=7.3); ax.set_xlabel('variance of coordination cost explained (R²)'); ax.set_xlim(0,max(v)+0.08)
ax.set_title('What explains coordination cost (pipeline output, pooled region-days)',fontsize=7.8,fontweight='bold')
plt.tight_layout(); save('Figure8')
print("pipeline-based Figures 4-8 written; drivers:", {k:round(x,2) for k,x in drivers.items()})
