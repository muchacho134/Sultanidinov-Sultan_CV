import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
orig=[tris(rd(f"work/x_{n}.brep")) for n in ("P214","P200","P189","P185","P188")]; O=np.concatenate(orig)
N=tris(rd("work/bcg_solid.brep"))
views=[("from +x (right)",(2,1),0,-1),("from -x (left)",(2,1),0,1),("from below (-y)",(2,0),1,1),("from above (+y)",(2,0),1,-1)]
fig,axs=plt.subplots(4,2,figsize=(24,22))
for r,(tt,(i,j),dep,sg) in enumerate(views):
    for c,(T,lab) in enumerate(((O,"ORIGINAL 214+200+189+185+188"),(N,"NEW single solid"))):
        ax=axs[r][c]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
        o=np.argsort(-T[:,:,dep].mean(1)*sg); sh=np.clip(0.3+0.7*np.abs(n[o,dep]),0,1)
        ax.add_collection(PolyCollection([[(q[i],q[j]) for q in t] for t in T[o]],facecolors=[(v*0.85,v*0.85,v*0.9) for v in sh],edgecolors='none'))
        ax.set_xlim(40,206); 
        ax.set_ylim((-283,-232) if j==1 else (-16,44)); ax.set_aspect('equal'); ax.set_title(f"{lab} — {tt}")
plt.tight_layout(); plt.savefig("work/bcg_compare.png",dpi=50); print("ok")
