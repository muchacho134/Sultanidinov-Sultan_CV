import sys, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape
from OCP.BRep import BRep_Builder
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); s=r.OneShape()
e=TopExp_Explorer(s,TopAbs_SHELL); shell=e.Current()
extra=None
if len(sys.argv)>4:
    extra=TopoDS_Shape(); BRepTools.Read_s(extra,sys.argv[4],BRep_Builder())
def tris(shape):
    BRepMesh_IncrementalMesh(shape,0.3,False,0.3)
    out=[]
    ex=TopExp_Explorer(shape,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            tr=loc.Transformation()
            P=[t.Node(i).Transformed(tr) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
T=tris(shell)
fb=ShapeAnalysis_FreeBounds(shell,1e-3)
segs=[]
for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
    ex=TopExp_Explorer(comp,TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.1)
        pts=[(d.Value(i).X(),d.Value(i).Y(),d.Value(i).Z()) for i in range(1,d.NbPoints()+1)]
        segs+= [ (pts[i],pts[i+1]) for i in range(len(pts)-1)]; ex.Next()
views={"under":(-90,-90),"side":(0,0),"oblique":(-135,25)}
fig=plt.figure(figsize=(16,11))
# axes: plot with z as long axis horizontally -> use (z, x, y) mapping
def m(a): a=np.asarray(a); return a[...,[2,0,1]]
lo,hi=float(sys.argv[2]),float(sys.argv[3])
for k,(name,(az,el)) in enumerate({"from below":(-90,-80),"oblique below":(-60,-35),"from side":(0,0)}.items()):
    ax=fig.add_subplot(3,1,k+1,projection='3d')
    sel=T[(T[:,:,2].min(1)>=lo)&(T[:,:,2].max(1)<=hi)]
    pc=Poly3DCollection(m(sel),facecolor=(0.75,0.78,0.82,0.55),edgecolor=(0.3,0.3,0.3,0.15),linewidths=0.2); ax.add_collection3d(pc)
    S=np.array([[a,b] for a,b in segs if lo<=a[2]<=hi]); 
    if len(S): ax.add_collection3d(Line3DCollection(m(S),colors='red',linewidths=1.5))
    if extra is not None:
        T2=tris(extra); ax.add_collection3d(Poly3DCollection(m(T2),facecolor=(0.1,0.3,1,0.5),edgecolor='b'))
    ax.set_xlim(lo,hi); ax.set_ylim(-30,30); ax.set_zlim(-280,-215)
    ax.set_box_aspect((hi-lo,60,65)); ax.view_init(elev=el,azim=az); ax.set_title(name); ax.set_axis_off()
plt.tight_layout(); plt.savefig(sys.argv[1].rsplit('/',1)[0]+"/../render.png" if False else "/tmp/claude-0/-home-user-Sultanidinov-Sultan-CV/ee98767e-bf30-59cd-9d8f-10a3e03f94c6/scratchpad/work/rail.png",dpi=70)
print("ok")
