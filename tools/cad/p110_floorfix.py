exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Wire
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire
from OCP.GeomAbs import *
from OCP.Geom import Geom_CylindricalSurface
from OCP.gp import gp_Ax3, gp_Pnt, gp_Dir
s=rd("work/x_P110.brep"); P213=rd("work/p213_solid.brep")
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
F=faces(s)
floor=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(area(f)-45.06)<0.05][0]
# socket outline = floor edges except the R7.35 circle
mw=BRepBuilderAPI_MakeWire(); ex=TopExp_Explorer(floor,TopAbs_EDGE); kept=0
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e)
    if not (c.GetType()==GeomAbs_Circle and abs(c.Circle().Radius()-7.35)<0.01): mw.Add(e); kept+=1
    ex.Next()
print("socket outline edges:",kept,"| wire ok:",mw.IsDone())
newfloor=BRepBuilderAPI_MakeFace(mw.Wire(),True).Face(); sf=ShapeFix_Face(newfloor); sf.Perform(); newfloor=sf.Face()
print("new floor area %.2f (old ring %.2f; R7.35 disc would be 169.72)"%(area(newfloor),area(floor)))
others=[f for f in F if not f.IsSame(floor)]
sw=BRepBuilderAPI_Sewing(1e-4)
for f in others+[newfloor]: sw.Add(f)
sw.Perform(); s2=sw.SewedShape()
fb=ShapeAnalysis_FreeBounds(s2,1e-4); print("open loops after floor fix:",count(fb.GetClosedWires(),TopAbs_WIRE))
# remaining loops: two pin-hole ends -> R8 bore patches; rear R8 circle -> planar disc
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s2,TopAbs_EDGE,TopAbs_FACE,m)
patches=[]; ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current())
    nb=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); a=BRepAdaptor_Surface(nb)
    if a.GetType()==GeomAbs_Cylinder and a.Cylinder().Radius()<2:
        f=BRepBuilderAPI_MakeFace(Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0.005,-267.9,-300),gp_Dir(0,0,1)),8.0),w,True).Face(); kind="R8 bore patch"
    else: f=BRepBuilderAPI_MakeFace(w,True).Face(); kind="flat disc"
    sff=ShapeFix_Face(f); sff.Perform(); f=sff.Face(); patches.append(f); print("  patch: %-14s area %.2f"%(kind,area(f))); ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s2)
for f in patches: sw.Add(f)
sw.Perform(); sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
print("open loops after patches:",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE))
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
print("P110 solid: valid",BRepCheck_Analyzer(so).IsValid(),"| volume %.1f"%vol(so),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()))
args=TopTools_ListOfShape(); args.Append(P213); tools=TopTools_ListOfShape(); tools.Append(so)
fu=BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools); fu.SetFuzzyValue(1e-5); fu.Build()
u=ShapeUpgrade_UnifySameDomain(fu.Shape(),True,True,True); u.Build(); r=u.Shape()
res=TopExp_Explorer(r,TopAbs_SOLID).Current()
print("MERGED: solids",count(r,TopAbs_SOLID),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE),"| valid",BRepCheck_Analyzer(res).IsValid(),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(res,True,True).Result()),"| volume %.1f"%vol(res))
cmp=TopoDS_Compound(); bb_=BRep_Builder(); bb_.MakeCompound(cmp); bb_.Add(cmp,s); bb_.Add(cmp,P213); bb_.Add(cmp,newfloor)
for f in patches: bb_.Add(cmp,f)
BRepMesh_IncrementalMesh(res,0.2,False,0.3); worst=0; n=0; ex=TopExp_Explorer(res,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    if t is not None:
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//20)):
            p=t.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),cmp); d.Perform(); worst=max(worst,d.Value()); n+=1
    ex.Next()
print("checked %d surface points: max distance from original/patch surfaces %.5f mm"%(n,worst))
BRepTools.Write_s(res,"work/p213_p110_solid.brep")
