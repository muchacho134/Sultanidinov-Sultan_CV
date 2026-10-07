exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S={n:rd(f"work/x_{n}.brep") for n in ["P596","P593","P594","P595"]}
C={"P596":'k',"P593":'tab:orange',"P594":'tab:green',"P595":'tab:blue'}
xs=[-67.5,-62,-50,-35,-20,-12,-5,5,12,15]; zs=[175,185,195,210,230,250,265,278]
fig,axs=plt.subplots(3,6,figsize=(36,18)); axs=axs.ravel()
pz=lambda p:(p[2],p[1]); px=lambda p:(p[0],p[1])
for i,x in enumerate(xs):
    ax=axs[i]
    for n,s in S.items(): draw(ax,s,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0)),pz,C[n],None)
    ax.set_title(f"x={x}"); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(165,290); ax.set_ylim(-350,-270)
for j,z in enumerate(zs):
    ax=axs[len(xs)+j]
    for n,s in S.items(): draw(ax,s,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),px,C[n],None)
    ax.set_title(f"z={z}"); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(-70,18); ax.set_ylim(-350,-270)
plt.tight_layout(); plt.savefig("work/p596_secs.png",dpi=45); print("ok")
