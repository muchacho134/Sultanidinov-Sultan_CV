import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
S=rd(sys.argv[1]); out=sys.argv[2]; views=[tuple(map(float,v.split(","))) for v in sys.argv[3].split(";")]; clip=eval(sys.argv[4])
T=tris(S); c=T.mean(1); T=T[np.array([clip(p) for p in c])]
segs=[]; ex=TopExp_Explorer(S,TopAbs_EDGE)
while ex.More():
    cv=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cv,0.02)
    P=np.array([[d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()] for k in range(1,d.NbPoints()+1)])
    if len(P)>1 and clip(P.mean(0)): segs+= list(zip(P[:-1],P[1:]))
    ex.Next()
segs=np.array(segs)
n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
fig,axs=plt.subplots(1,len(views),figsize=(9*len(views),9)); axs=np.atleast_1d(axs)
for ax,(az,el) in zip(axs,views):
    a,e=np.radians(az),np.radians(el); d=np.array([np.cos(e)*np.cos(a),np.sin(e),np.cos(e)*np.sin(a)])
    r=np.cross([0,1,0],d); r/=np.linalg.norm(r); u=np.cross(d,r); M=np.stack([r,u],1)
    P=T@M; o=np.argsort((T@d).mean(1)); L=d+0.3*u; L/=np.linalg.norm(L)
    sh=(0.35+0.65*np.abs(n[o]@L))[:,None]
    ax.add_collection(PolyCollection(P[o],facecolors=np.clip(np.array([.8,.8,.82])*sh,0,1),edgecolors='none'))
    ax.add_collection(LineCollection(segs@M,colors='k',linewidths=0.5))
    q=P.reshape(-1,2); ax.set_xlim(q[:,0].min()-1,q[:,0].max()+1); ax.set_ylim(q[:,1].min()-1,q[:,1].max()+1); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(f"az {az} el {el}")
plt.tight_layout(); plt.savefig(out,dpi=60); print("ok")
