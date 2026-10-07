exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/p244_ck4.brep")
fig,axs=plt.subplots(2,4,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("z",212),("z",224),("z",236),("z",255),("x",0.0),("x",7.0),("x",10.5),("x",12.2)]):
    pl=gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)) if k=="z" else gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)); pr=px if k=="z" else pz
    draw(ax,S,pl,pr,'k',"P244"); free(ax,S,pr) if False else None
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="z": ax.set_xlim(-20,20); ax.set_ylim(-340,-280)
    else: ax.set_xlim(185,280); ax.set_ylim(-340,-280)
plt.tight_layout(); plt.savefig("work/l9_secs.png",dpi=40); print("ok")
