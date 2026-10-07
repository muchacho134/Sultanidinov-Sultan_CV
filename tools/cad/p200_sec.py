import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=open("p110_sec.py").read()
exec(src.split("A=rd(")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
cols={"P214":'tab:blue',"P200":'k',"P189":'tab:green',"P185":'m',"P188":'goldenrod'}
S={n:rd(f"work/x_{n}.brep") for n in cols}
fig=plt.figure(figsize=(24,14))
ax=fig.add_subplot(2,1,1)
for n,c in cols.items(): draw(ax,S[n],gp_Pln(gp_Pnt(0.0,0,0),gp_Dir(1,0,0)),lambda p:(p[2],p[1]),c,n)
free(ax,S["P200"],lambda p:(p[2],p[1])); ax.set_aspect('equal'); ax.legend(loc='upper right'); ax.set_title("section x=0 (z, y)"); ax.grid(alpha=.3)
for k,z in enumerate((115,135,160,195)):
    ax=fig.add_subplot(2,4,5+k)
    for n,c in cols.items(): draw(ax,S[n],gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),c,n)
    free(ax,S["P200"],lambda p:(p[0],p[1])); ax.set_aspect('equal'); ax.set_title(f"section z={z} (x, y)"); ax.grid(alpha=.3); ax.set_xlim(-16,42); ax.set_ylim(-283,-232)
plt.tight_layout(); plt.savefig("work/p200_sec.png",dpi=55); print("ok")
