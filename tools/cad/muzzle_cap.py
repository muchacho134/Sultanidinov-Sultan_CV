import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
P221=rd("work/mz_P221.brep")
fb=ShapeAnalysis_FreeBounds(P221,1e-4); w=TopoDS.Wire_s(TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE).Current())
cap=BRepBuilderAPI_MakeFace(w,True).Face()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(P221); sw.Add(cap); sw.Perform()
sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p)
print("P221 capped: valid",BRepCheck_Analyzer(so).IsValid(),"volume %.1f mm3"%p.Mass())
BRepTools.Write_s(so,"work/mz_P221_solid.brep")
# longitudinal section through the axis (plane x=0) of all 4 parts
fig,ax=plt.subplots(figsize=(14,6))
for nm,c in (("P221",'k'),("solid_220",'tab:blue'),("solid_222",'tab:red'),("P215",'tab:green')):
    s=rd(f"work/mz_{nm}.brep"); sec=BRepAlgoAPI_Section(s,gp_Pln(gp_Pnt(0,0,0),gp_Dir(1,0,0))); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE)
    first=True
    while ex.More():
        cc=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cc,0.02)
        P=np.array([(d.Value(k).Z(),d.Value(k).Y()) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'-',c=c,lw=1.2,label=nm if first else None); first=False; ex.Next()
ax.set_aspect('equal'); ax.legend(); ax.set_title("muzzle: section through the axis (x=0)"); ax.set_xlabel("z"); ax.set_ylabel("y")
plt.tight_layout(); plt.savefig("work/muzzle_section.png",dpi=70); print("ok")
