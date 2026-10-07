exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=[("P223",'k'),("P244",'tab:purple'),("P256",'tab:cyan'),("P214",'tab:green'),("P259",'tab:red'),("P596",'tab:olive')]
S=[(n,c,rd(f"work/g_{n}.brep")) for n,c in S]
fig,axs=plt.subplots(2,3,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(kind,v) in zip(axs,[("x",0.0),("x",-11.85),("z",120),("z",150),("z",175),("z",210)]):
    pl=gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)) if kind=="x" else gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)); pr=pz if kind=="x" else px
    for n,c,s in S: draw(ax,s,pl,pr,c,n)
    free(ax,S[0][2],pr) if False else None
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=10)
    ax.set_title(f"{kind}={v}",fontsize=20); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if kind=="x": ax.set_xlim(95,250); ax.set_ylim(-292,-262)
    else: ax.set_xlim(-25,25); ax.set_ylim(-292,-252)
plt.tight_layout(); plt.savefig("work/zoom35.png",dpi=40); print("ok")
