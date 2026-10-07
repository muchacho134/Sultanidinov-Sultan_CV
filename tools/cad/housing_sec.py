import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open("p110_sec.py").read()
exec(src.split("A=rd(")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
cols={"P596":'k',"P593":'tab:red',"P594":'tab:green',"P595":'tab:blue',"P247":'tab:orange',"P244":'0.7',"P256":'tab:purple'}
S={n:rd(f"work/x_{n}.brep") for n in cols if n not in ("P244","P256")}
import subprocess
fig,axs=plt.subplots(2,3,figsize=(26,16))
plans=[(gp_Pln(gp_Pnt(0,0,200),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),"z=200 (x,y)"),
       (gp_Pln(gp_Pnt(0,0,240),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),"z=240 (x,y)"),
       (gp_Pln(gp_Pnt(0,0,270),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),"z=270 (x,y)"),
       (gp_Pln(gp_Pnt(-25,0,0),gp_Dir(1,0,0)),lambda p:(p[2],p[1]),"x=-25 (z,y)"),
       (gp_Pln(gp_Pnt(-50,0,0),gp_Dir(1,0,0)),lambda p:(p[2],p[1]),"x=-50 (z,y)"),
       (gp_Pln(gp_Pnt(0,-320,0),gp_Dir(0,1,0)),lambda p:(p[0],p[2]),"y=-320 (x,z)")]
for ax,(pln,proj,tt) in zip(axs.flat,plans):
    for n,s in S.items(): draw(ax,s,pln,proj,cols[n],n)
    ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=8); ax.set_title("section "+tt)
plt.tight_layout(); plt.savefig("work/housing_sec.png",dpi=50); print("ok")
