import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
files=sys.argv[1].split(","); out=sys.argv[2]; views=[tuple(map(float,v.split(","))) for v in sys.argv[3].split(";")]
clip=eval(sys.argv[4]) if len(sys.argv)>4 else None
cols=[(0.78,0.78,0.80),(0.45,0.65,0.95),(0.95,0.65,0.35),(0.5,0.85,0.5)]
TT=[];CC=[]
for i,f in enumerate(files):
    t=tris(rd(f)); TT.append(t); CC+= [cols[i%4]]*len(t)
allT=np.concatenate(TT); CC=np.array(CC)
if clip:
    c=allT.mean(1); m=np.array([clip(p) for p in c]); allT=allT[m]; CC=CC[m]
n=np.cross(allT[:,1]-allT[:,0],allT[:,2]-allT[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
fig,axs=plt.subplots(1,len(views),figsize=(10*len(views),9)); axs=np.atleast_1d(axs)
for ax,(az,el) in zip(axs,views):
    a,e=np.radians(az),np.radians(el)
    d=np.array([np.cos(e)*np.cos(a),np.sin(e),np.cos(e)*np.sin(a)])  # view dir toward viewer (x,y,z) with y up
    r=np.cross([0,1,0],d); r/=np.linalg.norm(r); u=np.cross(d,r)
    P=allT@np.stack([r,u],1); depth=allT@d
    o=np.argsort(depth.mean(1)); L=d+0.3*u; L/=np.linalg.norm(L)
    sh=(0.35+0.65*np.abs(n[o]@L))[:,None]
    ax.add_collection(PolyCollection(P[o],facecolors=np.clip(CC[o]*sh,0,1),edgecolors=(0,0,0,0.05),linewidths=0.2))
    q=P.reshape(-1,2); ax.set_xlim(q[:,0].min()-2,q[:,0].max()+2); ax.set_ylim(q[:,1].min()-2,q[:,1].max()+2); ax.set_aspect('equal'); ax.set_title(f"az {az} el {el}"); ax.axis('off')
plt.tight_layout(); plt.savefig(out,dpi=55); print("ok")
