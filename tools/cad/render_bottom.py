import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
exec(open("render_rail.py").read().split("files=sys.argv")[0])
fig,axs=plt.subplots(len(sys.argv)-2,1,figsize=(20,3.2*(len(sys.argv)-2)),squeeze=False)
for r,fn in enumerate(sys.argv[1:-1]):
    s=TopoDS_Shape(); BRepTools.Read_s(s,fn,BRep_Builder()); T=tris(s)
    n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=(np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
    order=np.argsort(-T[:,:,1].mean(1))   # view from below (-y): far (high y) first
    shade=np.clip(0.35+0.6*np.abs(n[:,1]),0,1)
    poly=[[(t[k][2],t[k][0]) for k in range(3)] for t in T[order]]
    ax=axs[r][0]; ax.add_collection(PolyCollection(poly,facecolors=[(v,v,v) for v in shade[order]*0.9],edgecolors=[(0.2,0.2,0.2,0.25)]*len(poly),linewidths=0.2))
    ax.set_xlim(-220,230); ax.set_ylim(-32,32); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(fn.split('/')[-1]+" - from below")
plt.tight_layout(); plt.savefig(sys.argv[-1],dpi=65); print("ok")
