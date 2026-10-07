import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
names=sys.argv[1].split(","); ctx=rd(sys.argv[3]) if len(sys.argv)>3 else None
fig,axs=plt.subplots(int(np.ceil(len(names)/5)),5,figsize=(25,5*int(np.ceil(len(names)/5)))); axs=axs.ravel()
for ax,n in zip(axs,names):
    T=tris(rd(f"work/allp/{n}.brep")); d=np.array([0.6,0.5,0.62]); d/=np.linalg.norm(d)
    r=np.cross([0,1,0],d); r/=np.linalg.norm(r); u=np.cross(d,r); M=np.stack([r,u],1)
    nn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-12
    o=np.argsort((T@d).mean(1)); sh=(0.35+0.65*np.abs(nn[o]@d))[:,None]
    P=T@M; ax.add_collection(PolyCollection(P[o],facecolors=np.clip(np.array([.5,.65,.95])*sh,0,1),edgecolors=(0,0,0,.2),linewidths=.3))
    q=P.reshape(-1,2); ax.set_xlim(q[:,0].min()-1,q[:,0].max()+1); ax.set_ylim(q[:,1].min()-1,q[:,1].max()+1); ax.set_aspect('equal'); ax.set_title(n,fontsize=14)
for ax in axs: ax.axis('off')
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=45)
