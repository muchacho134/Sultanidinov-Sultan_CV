import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open("p110_sec.py").read()
exec(src.split("fig,axs=")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
fig,axs=plt.subplots(1,2,figsize=(18,8))
pz=lambda p:(p[2],p[1])
for xcut,ax in ((0.005,axs[0]),(3.0,axs[1])):
    draw(ax,A,gp_Pln(gp_Pnt(xcut,0,0),gp_Dir(1,0,0)),pz,'k',"P110"); free(ax,A,pz)
    ax.axvline(-231.4,c='orange',ls='--',lw=1,label="z=-231.4 (disc)")
    ax.set_xlim(-250,-200); ax.set_ylim(-262,-226); ax.set_aspect('equal'); ax.legend(); ax.set_title(f"section x={xcut}"); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("work/p110_zoom.png",dpi=70); print("ok")
