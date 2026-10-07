from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
a=rd("work/s131_new.brep"); b=rd("work/s114_fixed.brep")
def faces(s):
    L=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More(): L.append(ex.Current()); ex.Next()
    return L
sw=BRepBuilderAPI_Sewing(1e-3)
for f in faces(a)+faces(b): sw.Add(f)
sw.Perform(); sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p)
print("combined 131+114: faces",len(faces(sh)),"valid",BRepCheck_Analyzer(so).IsValid(),"volume %.2f mm3"%p.Mass())
c=BRepAlgoAPI_Check(so,True,True); print("self-intersections:",sum(1 for _ in c.Result()))
BRepTools.Write_s(so,"work/merged.brep"); print("saved merged solid")
