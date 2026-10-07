import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import *
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
s=rd("work/x_P189.brep")
fig,ax=plt.subplots(figsize=(14,7))
ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); e2=TopExp_Explorer(f,TopAbs_EDGE)
    col={0:'tab:blue',1:'k',2:'tab:cyan',3:'tab:red',4:'tab:green'}[i]
    while e2.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(e2.Current())); d=GCPnts_QuasiUniformDeflection(c,0.02)
        P=np.array([(d.Value(k).Z(),d.Value(k).Y()) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'-',c=col,lw=1.5); e2.Next()
    i+=1; ex.Next()
ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title("P189 face edges in side view (z,y): black = left flat x=-5.05, blue/cyan = tube R7.25, red = BSpline blend, green = front face")
plt.tight_layout(); plt.savefig("work/gk_profile.png",dpi=70); print("ok")
