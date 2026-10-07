import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
def tris(s):
    BRepMesh_IncrementalMesh(s,0.02,False,0.2); out=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            T=loc.Transformation(); P=[t.Node(i).Transformed(T) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
def free(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-4); seg=[]; ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.01)
        p=[(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; seg+=[(p[i],p[i+1]) for i in range(len(p)-1)]; ex.Next()
    return np.array(seg)
A=rd("work/x_P111.brep"); B=rd("work/x_solid_127.brep"); C=rd("work/x_solid_131.brep")
T=[(tris(A),(0.75,0.75,0.78)),(tris(B),(0.4,0.6,0.9)),(tris(C),(0.9,0.6,0.3))]; F=free(A)
views=[("front (looking +z at z=-243.5 face)",(0,1),2,1),("top (looking -y)",(0,2),1,-1),("right side (looking -x)",(2,1),0,-1)]
fig,axs=plt.subplots(1,3,figsize=(21,7))
for ax,(tt,(i,j),dep,sg) in zip(axs,views):
    allT=np.concatenate([t for t,_ in T]); cols=np.concatenate([[c]*len(t) for t,c in T])
    n=np.cross(allT[:,1]-allT[:,0],allT[:,2]-allT[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    o=np.argsort(-allT[:,:,dep].mean(1)*sg); sh=(0.5+0.5*np.abs(n[o,dep]))[:,None]
    ax.add_collection(PolyCollection([[(q[i],q[j]) for q in t] for t in allT[o]],facecolors=np.clip(cols[o]*sh,0,1),edgecolors='none'))
    ax.add_collection(LineCollection([[(a[i],a[j]),(b[i],b[j])] for a,b in F],colors='red',linewidths=1.2))
    allp=allT.reshape(-1,3); ax.set_xlim(allp[:,i].min()-1,allp[:,i].max()+1); ax.set_ylim(allp[:,j].min()-1,allp[:,j].max()+1); ax.set_aspect('equal'); ax.set_title(tt)
plt.tight_layout(); plt.savefig("work/p111.png",dpi=70); print("ok")
