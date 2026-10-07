import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open("p110_sec.py").read()
exec(src.split("A=rd(")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
A=rd("work/x_P259.brep")
fig,axs=plt.subplots(1,3,figsize=(24,8))
for ax,(pln,proj,tt,xl,yl) in zip(axs,[
    (gp_Pln(gp_Pnt(0,0,174.5),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),"section z=174.5 (x,y)",(-24.5,-5.5),(-295,-268.5)),
    (gp_Pln(gp_Pnt(-23.4,0,0),gp_Dir(1,0,0)),lambda p:(p[2],p[1]),"section x=-23.4 through ridges (z,y)",(168,181),(-283,-268.5)),
    (gp_Pln(gp_Pnt(0,-288,0),gp_Dir(0,1,0)),lambda p:(p[0],p[2]),"section y=-288 through plate (x,z)",(-24.5,-5.5),(168,181))]):
    draw(ax,A,pln,proj,'k',"P259"); free(ax,A,proj)
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect('equal'); ax.legend(); ax.set_title(tt); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("work/p259_sec.png",dpi=65); print("ok")
