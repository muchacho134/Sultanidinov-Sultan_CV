import sys, numpy as np
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/shell_a.brep",BRep_Builder())
fb=ShapeAnalysis_FreeBounds(s,1e-3); ws=[]
for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
    ex=TopExp_Explorer(comp,TopAbs_WIRE)
    while ex.More(): ws.append(TopoDS.Wire_s(ex.Current())); ex.Next()
for i,w in enumerate(ws):
    P=[]; ex=TopExp_Explorer(w,TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
        P+=[(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; ex.Next()
    P=np.array(P); c=P.mean(0); u,sv,vt=np.linalg.svd(P-c); n=vt[2]
    dev=np.abs((P-c)@n); ext=[round(sv[0]/len(P)**.5*3.46,1),round(sv[1]/len(P)**.5*3.46,1)]
    print(i,"n=(%.2f,%.2f,%.2f)"%tuple(n),"max dev from best plane %.2f mm"%dev.max(),"in-plane size ~",ext)
