import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("render_p111.py").read().split("A=rd(")[0])
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
# opaque shaded render with painter's algorithm + edges drawn only where visible-ish (depth test via z-buffer raster)
S=rd(sys.argv[1]); out=sys.argv[2]; views=[tuple(map(float,v.split(","))) for v in sys.argv[3].split(";")]; clip=eval(sys.argv[4])
T=tris(S); T=T[np.array([clip(p) for p in T.mean(1)])]
segs=[]; ex=TopExp_Explorer(S,TopAbs_EDGE)
while ex.More():
    cv=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cv,0.02)
    P=np.array([[d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()] for k in range(1,d.NbPoints()+1)])
    if len(P)>1: segs+=[(a,b) for a,b in zip(P[:-1],P[1:]) if clip((a+b)/2)]
    ex.Next()
segs=np.array(segs)
n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
fig,axs=plt.subplots(1,len(views),figsize=(9*len(views),9)); axs=np.atleast_1d(axs)
for ax,(az,el) in zip(axs,views):
    a,e=np.radians(az),np.radians(el); d=np.array([np.cos(e)*np.cos(a),np.sin(e),np.cos(e)*np.sin(a)])
    r=np.cross([0,1,0],d); r/=np.linalg.norm(r); u=np.cross(d,r); M=np.stack([r,u],1)
    P=T@M; dep=T@d; o=np.argsort(dep.mean(1)); L=d+0.4*u+0.2*r; L/=np.linalg.norm(L)
    sh=(0.35+0.65*np.abs(n[o]@L))[:,None]
    # z-buffer for edge visibility
    W=600; q=P.reshape(-1,2); lo=q.min(0); hi=q.max(0); sc=(W-1)/max(hi-lo)
    zb=np.full((W,W),-1e9)
    for tri,dd in zip(P,dep):
        pts=((tri-lo)*sc).astype(int); x0,y0=pts.min(0); x1,y1=pts.max(0)
        zb[max(y0,0):y1+1,max(x0,0):x1+1]=np.maximum(zb[max(y0,0):y1+1,max(x0,0):x1+1],dd.max())
    vis=[]
    for s_ in segs:
        m=(s_[0]+s_[1])/2; p=((m@M-lo)*sc).astype(int)
        if 0<=p[0]<W and 0<=p[1]<W and m@d>=zb[p[1],p[0]]-0.15: vis.append(s_@M)
    ax.add_collection(PolyCollection(P[o],facecolors=np.clip(np.array([.78,.78,.8])*sh,0,1),edgecolors=np.clip(np.array([.78,.78,.8])*sh,0,1),linewidths=0.3))
    if vis: ax.add_collection(LineCollection(vis,colors='k',linewidths=0.7))
    ax.set_xlim(lo[0]-1,hi[0]+1); ax.set_ylim(lo[1]-1,hi[1]+1); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(f"az {az} el {el}")
plt.tight_layout(); plt.savefig(out,dpi=60); print("ok")
