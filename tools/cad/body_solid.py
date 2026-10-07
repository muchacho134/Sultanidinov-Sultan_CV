import sys
exec(open("split_body.py").read().split("BRepTools.Write_s(sh,sys.argv[2])")[0].replace("sw=BRepBuilderAPI_Sewing(1e-4)","sw=BRepBuilderAPI_Sewing(3e-3)"))
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Solid
new=[]
for w in caps:
    f=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,Z),gp_Dir(0,0,1)),w,True).Face(); new.append(f)
sw2=BRepBuilderAPI_Sewing(3e-3); sw2.Add(sh)
for f in new: sw2.Add(f)
sw2.Perform(); sh2=sw2.SewedShape()
print("after cap loops:",count(ShapeAnalysis_FreeBounds(sh2,1e-4).GetClosedWires(),TopAbs_WIRE), sh2.ShapeType())
shell=TopoDS.Shell_s(TopExp_Explorer(sh2,TopAbs_SHELL).Current())
so=BRepBuilderAPI_MakeSolid(shell).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
print("solid valid",BRepCheck_Analyzer(so).IsValid(),"volume %.1f"%vol(so))
BRepTools.Write_s(so,sys.argv[2])
