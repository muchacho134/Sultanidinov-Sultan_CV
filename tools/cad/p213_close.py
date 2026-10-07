exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
s=rd("work/x_P213.brep")
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopoDS.Wire_s(TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE).Current())
e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current()); nb=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First())
surf=BRep_Tool.Surface_s(nb)
patch=BRepBuilderAPI_MakeFace(surf,w,True).Face()
from OCP.ShapeFix import ShapeFix_Face
sf=ShapeFix_Face(patch); sf.Perform(); patch=sf.Face()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s); sw.Add(patch); sw.Perform()
sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
fb2=ShapeAnalysis_FreeBounds(sh,1e-4); left=count(fb2.GetClosedWires(),TopAbs_WIRE)
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
u=ShapeUpgrade_UnifySameDomain(so,True,True,True); u.Build(); so=TopExp_Explorer(u.Shape(),TopAbs_SOLID).Current()
from OCP.BRepGProp import BRepGProp
p=GProp_GProps(); BRepGProp.SurfaceProperties_s(patch,p)
print("patch area %.2f mm2 (window 5 mm x arc)"%p.Mass())
print("P213: open loops left",left,"| solids",count(so,TopAbs_SOLID),"| faces",count(so,TopAbs_FACE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
BRepTools.Write_s(so,"work/p213_solid.brep")
