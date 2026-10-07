exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
import re, numpy as np
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from scipy.spatial import cKDTree
P=rd("work/g_P244.brep")
def free_pts(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_EDGE); pts=[]
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
        pts+= [(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; ex.Next()
    return np.array(pts)
def all_edge_pts(s):
    ex=TopExp_Explorer(s,TopAbs_EDGE); pts=[]
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
        pts+= [(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; ex.Next()
    return np.array(pts)
F=free_pts(P); T=cKDTree(F)
names=[l.split()[1] for l in open("work/parts_now.txt") if "x[" in l]
pb=Bnd_Box(); BRepBndLib.Add_s(P,pb); pb.Enlarge(5)
for n in names:
    if n=="P244": continue
    try: s=rd(f"work/g_{n}.brep")
    except: continue
    b=Bnd_Box(); BRepBndLib.Add_s(s,b)
    if pb.IsOut(b): continue
    d=BRepExtrema_DistShapeShape(P,s); d.Perform(); dist=d.Value()
    if dist>0.5: continue
    E=all_edge_pts(s); dd,_=T.query(E); frac=(dd<0.02).mean()
    print(f"{n:10s} {str(s.ShapeType()).split('.')[-1][7:]:6s} dist {dist:.3f}  edge pts on P244 holes {frac*100:5.1f}%  faces {count(s,TopAbs_FACE)}")
