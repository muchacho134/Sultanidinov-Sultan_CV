import sys
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'work/Gun_final.step'"))
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
s114=[v[0] for k,v in parts.items() if k.endswith("114")][0]; s131=parts["solid_131"][0]
print("131 type:",str(s131.ShapeType()).split('.')[-1]," 114 type:",str(s114.ShapeType()).split('.')[-1])
def nfree(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-4); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m); o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
print("free loops alone: 131 =",nfree(s131)," 114 =",nfree(s114))
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(s131); sw.Add(s114); sw.Perform(); res=sw.SewedShape()
sh=TopoDS.Shell_s(TopExp_Explorer(res,TopAbs_SHELL).Current()); print("together: free loops =",nfree(sh))
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p); print("valid",BRepCheck_Analyzer(so).IsValid(),"volume %.2f"%p.Mass())
