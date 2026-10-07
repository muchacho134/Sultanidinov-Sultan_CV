exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.ShapeFix import ShapeFix_Face
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder
s=rd("work/x_P110.brep"); P213=rd("work/p213_solid.brep")
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); patches=[]
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current())
    nb=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); a=BRepAdaptor_Surface(nb)
    f=BRepBuilderAPI_MakeFace(BRep_Tool.Surface_s(nb),w,True).Face(); sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    kind="plane" if a.GetType()==GeomAbs_Plane else ("cylinder R%.2f"%a.Cylinder().Radius() if a.GetType()==GeomAbs_Cylinder else str(a.GetType()))
    print("patch on %-14s area %6.2f  z[%.2f,%.2f] y[%.2f,%.2f]"%(kind,p.Mass(),x[2],x[5],x[1],x[4])); patches.append(f); ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s)
for f in patches: sw.Add(f)
sw.Perform(); sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
print("P110 open loops after patching:",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE))
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
print("P110 solid: valid",BRepCheck_Analyzer(so).IsValid(),"| volume %.1f"%vol(so),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()))
args=TopTools_ListOfShape(); args.Append(P213); tools=TopTools_ListOfShape(); tools.Append(so)
fu=BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools); fu.SetFuzzyValue(1e-5); fu.Build(); print("fuse done:",fu.IsDone())
u=ShapeUpgrade_UnifySameDomain(fu.Shape(),True,True,True); u.Build(); r=u.Shape()
print("result: solids",count(r,TopAbs_SOLID),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE))
res=TopExp_Explorer(r,TopAbs_SOLID).Current()
print("valid:",BRepCheck_Analyzer(res).IsValid(),"| self-intersections:",sum(1 for _ in BRepAlgoAPI_Check(res,True,True).Result()),"| volume %.1f (P213 %.1f + P110 %.1f)"%(vol(res),vol(P213),vol(so)))
cmp=TopoDS_Compound(); bb_=BRep_Builder(); bb_.MakeCompound(cmp); bb_.Add(cmp,s); bb_.Add(cmp,P213)
for f in patches: bb_.Add(cmp,f)
BRepMesh_IncrementalMesh(res,0.2,False,0.3); worst=0; n=0; ex=TopExp_Explorer(res,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    if t is not None:
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//20)):
            p=t.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),cmp); d.Perform(); worst=max(worst,d.Value()); n+=1
    ex.Next()
print("checked %d surface points: max distance from P110/P213/patch surfaces %.5f mm"%(n,worst))
BRepTools.Write_s(res,"work/p213_p110_solid.brep")
