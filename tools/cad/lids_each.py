import sys, numpy as np, mapbox_earcut as ec
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools, BRepTools_WireExplorer
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.BRepBuilderAPI import *
from OCP.gp import gp_Pnt
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
src,out_brep,out_step,tol=sys.argv[1],'x','y',0.05
s=TopoDS_Shape(); BRepTools.Read_s(s,src,BRep_Builder())
shell=TopoDS.Shell_s(TopExp_Explorer(s,TopAbs_SHELL).Current())
def wires(sh):
    fb=ShapeAnalysis_FreeBounds(sh,1e-3); L=[]
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More(): L.append(TopoDS.Wire_s(ex.Current())); ex.Next()
    return L
def ordered_points(w,defl=0.02):
    P=[]; we=BRepTools_WireExplorer(w)
    while we.More():
        e=we.Current(); c=BRepAdaptor_Curve(e); d=GCPnts_QuasiUniformDeflection(c,defl)
        pts=[np.array([d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()]) for k in range(1,d.NbPoints()+1)]
        if e.Orientation()==TopAbs_REVERSED: pts=pts[::-1]
        if P and np.linalg.norm(P[-1]-pts[0])>1e-6: pts=pts[::-1] if np.linalg.norm(P[-1]-pts[-1])<np.linalg.norm(P[-1]-pts[0]) else pts
        P+= pts if not P else pts[1:]
        we.Next()
    P=np.array(P)
    if np.linalg.norm(P[0]-P[-1])<1e-6: P=P[:-1]
    return P

def lid_pass(shell,only=None):
    faces=[]; report=[]
    for i,w in enumerate(wires(shell)):
        if only is not None and i not in only: continue
        P=ordered_points(w); c=P.mean(0); u,sv,vt=np.linalg.svd(P-c); n=vt[2]
        XY=((P-c)@vt[:2].T).astype(np.float64)
        tri=ec.triangulate_float64(XY,np.array([len(XY)],dtype=np.uint32)).reshape(-1,3)
        ok=0
        for a,b,cc in tri:
            pts=[P[a],P[b],P[cc]]
            if np.linalg.norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))<1e-9: continue
            mp=BRepBuilderAPI_MakePolygon(*[gp_Pnt(*p) for p in pts],True)
            mf=BRepBuilderAPI_MakeFace(mp.Wire(),True)
            if mf.IsDone(): faces.append(mf.Face()); ok+=1
        report.append((i,len(P),len(tri),ok))
    sw=BRepBuilderAPI_Sewing(tol); sw.Add(shell)
    for f in faces: sw.Add(f)
    sw.Perform(); res=sw.SewedShape()
    L=[]; ex=TopExp_Explorer(res,TopAbs_SHELL)
    while ex.More(): L.append(TopoDS.Shell_s(ex.Current())); ex.Next()
    return L,report

from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
for i in range(len(wires(shell))):
    L,rep=lid_pass(shell,[i])
    c=BRepAlgoAPI_Check(L[0],True,True)
    n=sum(1 for _ in c.Result())
    b=Bnd_Box(); BRepBndLib.Add_s(wires(shell)[i],b)
    print("loop",i,"bbox",[round(v) for v in b.Get()],"-> self-intersections",n,flush=True)
