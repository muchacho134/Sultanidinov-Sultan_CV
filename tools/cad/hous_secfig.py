exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
N=rd("work/hous_solid.brep"); O=rd("work/x_P596.brep")
fig,axs=plt.subplots(1,3,figsize=(30,9))
pz=lambda p:(p[2],p[1]); px=lambda p:(p[0],p[1])
for ax,(pl,pr,t,xl) in zip(axs,[(gp_Pln(gp_Pnt(-40,0,0),gp_Dir(1,0,0)),pz,"section x=-40 (side view)",(180,290)),
                         (gp_Pln(gp_Pnt(0,0,0),gp_Dir(1,0,0)),pz,"section x=0 (cradle)",(165,290)),
                         (gp_Pln(gp_Pnt(0,0,230),gp_Dir(0,0,1)),px,"section z=230 (looking along barrel)",(-70,18))]):
    draw(ax,O,pl,pr,'tab:red',"original P596 skin"); draw(ax,N,pl,pr,'k',"rebuilt solid")
    ax.set_title(t,fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(*xl); ax.set_ylim(-350,-270); ax.legend(loc='upper left')
plt.tight_layout(); plt.savefig("work/hous_secs.png",dpi=50); print("ok")
