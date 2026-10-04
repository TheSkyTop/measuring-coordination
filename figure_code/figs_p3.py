import json, numpy as np, matplotlib.pyplot as plt
import matplotlib.patches as mp
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Liberation Sans','Arial','Helvetica','DejaVu Sans'],
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','axes.linewidth':0.75,'figure.dpi':600,'savefig.dpi':600,
 'axes.spines.top':False,'axes.spines.right':False,'font.size':8,'axes.titlesize':9,'axes.labelsize':7.5,
 'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'lines.linewidth':0.9})
NAVY='#1F4E79'; ORANGE='#F28E2B'; TEAL='#00897B'; GREY='#808080'; LGREY='#D9D9D9'; INK='#222222'
O=json.load(open('/sessions/admiring-lucid-euler/mnt/outputs/measure_out.json'))
OUT='/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/Submission3/Figures/'
def save(n): plt.savefig(OUT+n+'.pdf'); plt.savefig(OUT+n+'.png'); plt.close()

# ===== F1 HERO: what electricity markets measure (today -> +coordination) =====
fig,ax=plt.subplots(figsize=(7.2,3.6)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.set_position([0,0,1,1])
ax.text(50,94,'What electricity markets measure',ha='center',fontsize=11,fontweight='bold',color=NAVY)
today=['Price','Reserve margin','Congestion','Curtailment','Reliability']
# Today column
ax.add_patch(FancyBboxPatch((6,18),38,64,boxstyle="round,pad=0.5,rounding_size=2",fc='white',ec=GREY,lw=1.4))
ax.text(25,76,'Today',ha='center',fontsize=9.5,fontweight='bold',color=GREY)
for i,t in enumerate(today):
    ax.add_patch(FancyBboxPatch((10,64-i*10),30,7,boxstyle="round,pad=0.2,rounding_size=1.2",fc=LGREY,ec='none',alpha=0.5))
    ax.text(25,67.5-i*10,t,ha='center',va='center',fontsize=7.6,color=INK)
# arrow
ax.add_patch(FancyArrowPatch((45,50),(55,50),arrowstyle='-|>',mutation_scale=16,color=NAVY,lw=2))
# Future column
ax.add_patch(FancyBboxPatch((56,12),38,70,boxstyle="round,pad=0.5,rounding_size=2",fc='white',ec=NAVY,lw=1.6))
ax.text(75,76,'The coming system',ha='center',fontsize=9.5,fontweight='bold',color=NAVY)
for i,t in enumerate(today):
    ax.add_patch(FancyBboxPatch((60,64-i*10),30,7,boxstyle="round,pad=0.2,rounding_size=1.2",fc=LGREY,ec='none',alpha=0.5))
    ax.text(75,67.5-i*10,t,ha='center',va='center',fontsize=7.6,color=INK)
ax.add_patch(FancyBboxPatch((60,14),30,8,boxstyle="round,pad=0.2,rounding_size=1.2",fc=NAVY,ec='none'))
ax.text(74,18,'Coordination',ha='center',va='center',fontsize=8.0,fontweight='bold',color='white')
ax.text(92.5,18,'NEW',ha='center',va='center',fontsize=6.2,fontweight='bold',color=ORANGE)
ax.text(50,6,'Markets are richly instrumented—but coordination, an increasingly large source of inefficiency, has no metric.',ha='center',fontsize=6.8,style='italic',color=GREY)
save('Figure1')

# ===== F2 three-layer measurement framework =====
fig,ax=plt.subplots(figsize=(7.2,3.7)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.set_position([0,0,1,1])
ax.text(50,95,'A three-layer measurement framework for coordination',ha='center',fontsize=9.8,fontweight='bold',color=NAVY)
layers=[('BEHAVIOURAL','Decision correlation  ρ','are independent decisions moving together?','measured from realised deviations',TEAL,70),
        ('ECONOMIC','Coordination cost  CC = (C_dec − C_opt)/C_opt','how much is the miscoordination worth?','from the counterfactual co-optimisation',ORANGE,46),
        ('OPERATIONAL','Coordination efficiency  η = C_opt/C_dec','how well coordinated is the system now?','a 0–1 dashboard indicator (1 = perfect)',NAVY,22)]
for tag,t,q,how,c,y in layers:
    ax.add_patch(FancyBboxPatch((8,y),84,18,boxstyle="round,pad=0.3,rounding_size=2",fc=c,ec='none',alpha=0.10))
    ax.add_patch(FancyBboxPatch((8,y),84,18,boxstyle="round,pad=0.3,rounding_size=2",fc='none',ec=c,lw=1.6))
    ax.text(12,y+13,tag,ha='left',va='center',fontsize=7.0,fontweight='bold',color=c)
    ax.text(12,y+7.5,t,ha='left',va='center',fontsize=8.4,fontweight='bold',color=INK)
    ax.text(12,y+2.8,q+'   ·   '+how,ha='left',va='center',fontsize=6.5,style='italic',color=GREY)
for y in [70,46]:
    ax.add_patch(FancyArrowPatch((50,y),(50,y-4),arrowstyle='-|>',mutation_scale=11,color=GREY,lw=1.3))
ax.text(50,6,'All three derive from one counterfactual; together they make coordination legible as behaviour, economics and operations—',ha='center',fontsize=6.5,color=GREY)
ax.text(50,2.5,'the basis for a coordination-measurement science to which further metrics (e.g. a coordination index, coordination resilience) can be added.',ha='center',fontsize=6.5,color=GREY)
save('Figure2')

# ===== F3 counterfactual identification =====
fig,ax=plt.subplots(figsize=(7.2,2.6)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.set_position([0,0,1,1])
ax.text(50,90,'Counterfactual identification of coordination cost',ha='center',fontsize=9.5,fontweight='bold',color=NAVY)
b=[('Realised dispatch','D_real (independent decisions)',16,GREY),
   ('Counterfactual','D* — co-optimise the same\nfleet, network, weather',50,TEAL),
   ('Coordination cost','C(D_real) − C(D*),\nnormalised',84,ORANGE)]
for t,s,x,c in b:
    ax.add_patch(FancyBboxPatch((x-14,34),28,30,boxstyle="round,pad=0.3,rounding_size=2",fc='white',ec=c,lw=1.6))
    ax.text(x,55,t,ha='center',fontsize=7.8,fontweight='bold',color=c); ax.text(x,44,s,ha='center',fontsize=6.4,color=INK)
for x0,x1 in [(30,36),(64,70)]:
    ax.add_patch(FancyArrowPatch((x0,49),(x1,49),arrowstyle='-|>',mutation_scale=11,color=GREY,lw=1.4))
ax.text(50,22,'Same physical system in both → the difference is coordination, not capacity.',ha='center',fontsize=6.8,color=INK)
save('Figure3')

# ===== F4 heatmap (temporal/seasonal) =====
heat=np.array(O['heatmap']['CC'])
fig,ax=plt.subplots(figsize=(7.2,3.2))
im=ax.imshow(heat,aspect='auto',origin='lower',cmap='YlOrBr',extent=[0,24,0.5,12.5])
ax.set_xlabel('Hour of day'); ax.set_ylabel('Month'); ax.set_xticks([0,6,12,18,24]); ax.set_yticks(range(1,13))
ax.set_title('Coordination cost across the year (modelled, hour × month)',fontsize=8.6,fontweight='bold')
cb=plt.colorbar(im,ax=ax,fraction=0.046,pad=0.02); cb.set_label('coordination cost (% above optimum)',fontsize=7)
ax.spines['top'].set_visible(True); ax.spines['right'].set_visible(True); plt.tight_layout(); save('Figure4')

# ===== F5 regional =====
reg=O['regions']; names=list(reg.keys()); CC=[reg[r]['CC'] for r in names]
realneg={'South Australia':48.4,'Victoria':43.1,'New South Wales':None,'Queensland':None,'Tasmania':None}
fig,ax=plt.subplots(figsize=(7.2,3.3)); x=np.arange(len(names)); cols=[ORANGE,ORANGE,NAVY,NAVY,TEAL]
ax.bar(x,CC,0.6,color=cols)
for i,v in enumerate(CC): ax.text(i,v+0.6,'%.0f%%'%v,ha='center',fontsize=7.5,fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([n.replace(' ','\n') for n in names],fontsize=7)
ax.set_ylabel('Coordination cost (% above optimum)'); ax.set_ylim(0,48)
ax.set_title('Coordination cost by region (modelled), in the order of the real NEM negative-price signature',fontsize=7.8,fontweight='bold')
for i,r in enumerate(names):
    if realneg[r] is not None: ax.text(i,3,'real neg-price\n%.0f%% (Q4 2025)'%realneg[r],ha='center',fontsize=5.7,color='white',fontweight='bold')
plt.tight_layout(); save('Figure5')

# ===== F6 vs penetration =====
ps=O['pen_sweep']; pp=[d['pen']*100 for d in ps]; cc=[d['CC'] for d in ps]
fig,ax=plt.subplots(figsize=(7.2,3.1)); ax.plot(pp,cc,'-o',color=NAVY,ms=5)
z=np.polyfit(pp,cc,1); ax.plot(pp,np.polyval(z,pp),'--',color=GREY,lw=1)
ax.set_xlabel('Renewable penetration (%)'); ax.set_ylabel('Coordination cost (%)')
ax.set_title('Coordination cost rises with renewable penetration (modelled)',fontsize=8.4,fontweight='bold'); plt.tight_layout(); save('Figure6')

# ===== F7 vs battery =====
bs=O['batt_sweep']; nn=[d['N'] for d in bs]; cc=[d['CC'] for d in bs]
fig,ax=plt.subplots(figsize=(7.2,3.1)); ax.plot(nn,cc,'-o',color=ORANGE,ms=5)
ax.set_xlabel('Number of independent batteries N'); ax.set_ylabel('Coordination cost (%)')
ax.set_title('Coordination cost persists as the battery fleet grows (modelled)',fontsize=8.4,fontweight='bold'); ax.set_ylim(0,max(cc)+5); plt.tight_layout(); save('Figure7')

# ===== F8 drivers =====
rg=O['regression']; dn=rg['names']; r2=rg['R2_univariate']
order=np.argsort(r2); dn=[dn[i] for i in order]; r2=[r2[i] for i in order]
cols=[NAVY if ('correlation' in d or 'common' in d) else (ORANGE if 'neg' in d else GREY) for d in dn]
fig,ax=plt.subplots(figsize=(7.2,3.1)); ax.barh(range(len(dn)),r2,color=cols)
for i,v in enumerate(r2): ax.text(v+0.01,i,'%.2f'%v,va='center',fontsize=7.5)
ax.set_yticks(range(len(dn))); ax.set_yticklabels(dn,fontsize=7.3); ax.set_xlabel('variance of coordination cost explained (R²)'); ax.set_xlim(0,0.7)
ax.set_title('Behavioural drivers explain coordination cost better than penetration alone',fontsize=7.8,fontweight='bold'); plt.tight_layout(); save('Figure8')

# ===== F9 dashboard =====
fig,ax=plt.subplots(figsize=(7.2,3.0)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.set_position([0,0,1,1])
ax.text(50,93,'A coordination metric on the operator’s dashboard',ha='center',fontsize=9.5,fontweight='bold',color=NAVY)
tiles=[('Frequency','50.0 Hz',GREY),('Reserve','adequate',GREY),('Congestion','low',GREY),('Curtailment','6%',GREY),('Coordination\nefficiency','0.73',NAVY)]
for i,(t,v,c) in enumerate(tiles):
    x=8+i*18; hl=c==NAVY
    ax.add_patch(FancyBboxPatch((x,40),15,34,boxstyle="round,pad=0.3,rounding_size=2",fc=(NAVY if hl else 'white'),ec=NAVY,lw=1.6 if hl else 1.0))
    ax.text(x+7.5,66,t,ha='center',fontsize=6.8,fontweight='bold',color=('white' if hl else INK))
    ax.text(x+7.5,50,v,ha='center',fontsize=9,fontweight='bold',color=('white' if hl else NAVY))
ax.text(8+4*18+7.5,37,'NEW',ha='center',fontsize=6.2,fontweight='bold',color=ORANGE)
ax.text(50,28,'Coordination efficiency (η = C_opt/C_dec, 1 = perfectly coordinated) is the missing standing indicator,',ha='center',fontsize=6.8,color=INK)
ax.text(50,22,'monitorable beside reserve, congestion and curtailment.',ha='center',fontsize=6.8,color=INK)
save('Figure9')
print("Paper 3 figures rebuilt (9)")
