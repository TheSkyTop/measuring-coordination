import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge, Circle, Rectangle
import numpy as np
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Liberation Sans','Arial','DejaVu Sans'],
 'pdf.fonttype':42,'figure.dpi':600,'savefig.dpi':600})
NAVY='#1F4E79'; ORANGE='#F28E2B'; TEAL='#00897B'; GREY='#808080'; LGREY='#C9CfD6'; INK='#222222'
OUT="/sessions/admiring-lucid-euler/mnt/Nature Energy Publication/Submission3/Figures/"
fig,ax=plt.subplots(figsize=(7.2,2.55)); ax.set_xlim(0,100); ax.set_ylim(0,40); ax.axis('off')
ax.set_position([0,0,1,1])

panels=[2,26.5,51,75.5]; W=21.5; y0=4.5; H=30
titles=["The measurement gap","The counterfactual","The metric set","The dashboard"]
sub=["what markets do\nand don't measure","co-optimise the same\nfleet; read the gap","behaviour → economics\n→ operation","a standing indicator\noperators can act on"]
cols=[GREY,NAVY,ORANGE,TEAL]
for i,(x,t,s,c) in enumerate(zip(panels,titles,sub,cols)):
    box=FancyBboxPatch((x,y0),W,H,boxstyle="round,pad=0.3,rounding_size=1.4",
        linewidth=1.0,edgecolor=c,facecolor='white'); ax.add_patch(box)
    # number badge
    ax.add_patch(Circle((x+2.4,y0+H-2.4),1.7,color=c,zorder=5))
    ax.text(x+2.4,y0+H-2.4,str(i+1),ha='center',va='center',color='white',fontsize=8,fontweight='bold',zorder=6)
    ax.text(x+W/2+1.2,y0+H-2.4,t,ha='center',va='center',fontsize=7.6,fontweight='bold',color=INK)
    ax.text(x+W/2,y0+1.6,s,ha='center',va='bottom',fontsize=5.7,color=GREY,linespacing=1.25)

# Panel 1: measured ticks + coordination gap
items=["price","reserve","congestion","curtailment","reliability"]
x=panels[0]; yy=y0+H-7
for it in items:
    ax.text(x+3.2,yy,"✓",ha='center',va='center',fontsize=6.2,color=TEAL,fontweight='bold')
    ax.text(x+4.8,yy,it,ha='left',va='center',fontsize=5.9,color=INK); yy-=2.9
ax.add_patch(Rectangle((x+2.4,yy-0.4),W-4.6,3.0,facecolor='#F4E3CF',edgecolor=ORANGE,linewidth=0.8))
ax.text(x+3.2,yy+1.1,"?",ha='center',va='center',fontsize=6.5,color=ORANGE,fontweight='bold')
ax.text(x+4.8,yy+1.1,"coordination",ha='left',va='center',fontsize=5.9,color=ORANGE,fontweight='bold')

# Panel 2: two bars D_real vs D* + gap
x=panels[1]; bx=x+4.5; bw=4.0; base=y0+8.0; 
ax.bar(bx,16,bw,bottom=base,color=NAVY,zorder=3); ax.text(bx,base-1.5,"$D_{real}$",ha='center',fontsize=6,color=NAVY)
ax.bar(bx+8,11,bw,bottom=base,color=TEAL,zorder=3); ax.text(bx+8,base-1.5,"$D^{*}$",ha='center',fontsize=6,color=TEAL)
ax.annotate("",xy=(bx+8+bw/2+0.6,base+11),xytext=(bx+8+bw/2+0.6,base+16),
    arrowprops=dict(arrowstyle='<->',color=ORANGE,lw=1.0))
ax.text(bx+8+bw/2+1.4,base+13.5,"gap\n= CC",ha='left',va='center',fontsize=5.6,color=ORANGE,fontweight='bold',linespacing=1.0)

# Panel 3: three chips
x=panels[2]; chips=[("ρ","behaviour",NAVY),("CC","economics",ORANGE),("η","operation",TEAL)]
cy=y0+H-7.5
for sym,lab,c in chips:
    ax.add_patch(FancyBboxPatch((x+2.6,cy-1.7),W-5.2,3.4,boxstyle="round,pad=0.15,rounding_size=0.8",
        linewidth=0.9,edgecolor=c,facecolor='white'))
    ax.text(x+5.0,cy,sym,ha='center',va='center',fontsize=7.2,color=c,fontweight='bold')
    ax.text(x+8.0,cy,lab,ha='left',va='center',fontsize=6.0,color=INK); cy-=5.4

# Panel 4: gauge
x=panels[3]; cx=x+W/2; gy=y0+12; r=6.2
ax.add_patch(Wedge((cx,gy),r,0,180,width=1.7,facecolor=LGREY,edgecolor='none'))
ax.add_patch(Wedge((cx,gy),r,40,180,width=1.7,facecolor=TEAL,edgecolor='none'))
ang=np.deg2rad(40+8)
ax.plot([cx,cx+(r-1.0)*np.cos(ang)],[gy,gy+(r-1.0)*np.sin(ang)],color=INK,lw=1.4)
ax.add_patch(Circle((cx,gy),0.7,color=INK))
ax.text(cx,gy+r+1.2,"η  coordination",ha='center',fontsize=6.0,color=INK,fontweight='bold')
ax.text(cx,gy-2.2,"0",ha='center',fontsize=5,color=GREY); ax.text(cx+r,gy-0.2,"1",ha='left',fontsize=5,color=GREY)

# arrows between panels
for i in range(3):
    xa=panels[i]+W+0.2; xb=panels[i+1]-0.2
    ax.add_patch(FancyArrowPatch((xa,y0+H/2),(xb,y0+H/2),arrowstyle='-|>',mutation_scale=11,color=INK,lw=1.1))
plt.savefig(OUT+'Figure1.pdf'); plt.savefig(OUT+'Figure1.png',dpi=600); plt.close()
print("Figure1 (4-step conceptual) written")
