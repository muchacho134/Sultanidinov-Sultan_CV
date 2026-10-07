import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open("p110_sec.py").read()
exec(src.split("A=rd(")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
A=rd("work/x_P154.brep"); B=rd("work/P150_solid.brep")
fig,axs=plt.subplots(1,2,figsize=(18,8))
for ax,xc in zip(axs,(0.0,1.5)):
    pz=lambda p:(p[2],p[1])
    draw(ax,B,gp_Pln(gp_Pnt(xc,0,0),gp_Dir(1,0,0)),pz,'0.6',"P150 (closed)")
    draw(ax,A,gp_Pln(gp_Pnt(xc,0,0),gp_Dir(1,0,0)),pz,'k',"P154"); free(ax,A,pz)
    ax.set_xlim(274,300); ax.set_ylim(-251,-220); ax.set_aspect('equal'); ax.legend(); ax.set_title(f"section x={xc}"); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("work/p154_sec.png",dpi=70); print("ok")
