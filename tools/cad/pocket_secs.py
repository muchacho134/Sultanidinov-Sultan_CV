exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/p223_ckpt7.brep"); R=rd("work/rs_solid.brep")
fig,axs=plt.subplots(2,4,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("x",-7.0),("x",-6.0),("x",0.0),("x",6.0),("z",217),("z",220),("z",223),("z",226.5)]):
    pl=gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)) if k=="x" else gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)); pr=pz if k=="x" else px
    draw(ax,S,pl,pr,'k',"P223"); draw(ax,R,pl,pr,'tab:orange',"rear sight")
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="x": ax.set_xlim(205,235); ax.set_ylim(-235,-210)
    else: ax.set_xlim(-14,14); ax.set_ylim(-235,-210)
plt.tight_layout(); plt.savefig("work/pocket_secs.png",dpi=45); print("ok")
