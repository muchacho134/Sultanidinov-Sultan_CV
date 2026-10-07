import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
files=sys.argv[1].split(","); out=sys.argv[2]
cols=[(0.75,0.75,0.78),(0.45,0.65,0.95),(0.95,0.65,0.35),(0.5,0.85,0.5)]
T=[(tris(rd(f)),cols[i%4]) for i,f in enumerate(files)]; F=np.concatenate([free(rd(f)) for f in files if len(free(rd(f)))] or [np.zeros((0,2,3))])
views=[("from -x",(2,1),0,1),("from +x",(2,1),0,-1),("from -z (front)",(0,1),2,1),("from -y (below)",(2,0),1,1)]
fig,axs=plt.subplots(1,4,figsize=(26,7))
allT=np.concatenate([t for t,_ in T]); colsA=np.concatenate([[c]*len(t) for t,c in T])
n=np.cross(allT[:,1]-allT[:,0],allT[:,2]-allT[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
for ax,(tt,(i,j),dep,sg) in zip(axs,views):
    o=np.argsort(-allT[:,:,dep].mean(1)*sg); sh=(0.45+0.55*np.abs(n[o,dep]))[:,None]
    ax.add_collection(PolyCollection([[(q[i],q[j]) for q in t] for t in allT[o]],facecolors=np.clip(colsA[o]*sh,0,1),edgecolors=(0,0,0,0.08),linewidths=0.2))
    if len(F): ax.add_collection(LineCollection([[(a[i],a[j]),(b[i],b[j])] for a,b in F],colors='red',linewidths=1.3))
    p=allT.reshape(-1,3); ax.set_xlim(p[:,i].min()-1,p[:,i].max()+1); ax.set_ylim(p[:,j].min()-1,p[:,j].max()+1); ax.set_aspect('equal'); ax.set_title(tt)
plt.tight_layout(); plt.savefig(out,dpi=60); print("ok")
