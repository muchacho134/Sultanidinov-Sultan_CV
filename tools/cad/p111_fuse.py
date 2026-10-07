exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
pieces={"collar":rd("work/collar.brep"),"solid_127":rd("work/x_solid_127.brep"),"solid_131":rd("work/x_solid_131.brep")}
for k,v in pieces.items(): print(k,"volume %.1f"%vol(v))
args=TopTools_ListOfShape(); args.Append(pieces["collar"]); tools=TopTools_ListOfShape(); tools.Append(pieces["solid_127"]); tools.Append(pieces["solid_131"])
fu=BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools); fu.SetFuzzyValue(1e-5); fu.Build(); print("fuse done:",fu.IsDone())
u=ShapeUpgrade_UnifySameDomain(fu.Shape(),True,True,True); u.Build(); r=u.Shape()
print("result: solids",count(r,TopAbs_SOLID),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE))
so=TopExp_Explorer(r,TopAbs_SOLID).Current()
print("valid:",BRepCheck_Analyzer(so).IsValid(),"| self-intersections:",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
cmp=TopoDS_Compound(); bb_=BRep_Builder(); bb_.MakeCompound(cmp)
for s in pieces.values(): bb_.Add(cmp,s)
BRepMesh_IncrementalMesh(so,0.1,False,0.3); worst=0; n=0; ex=TopExp_Explorer(so,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    if t is not None:
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//40)):
            p=t.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),cmp); d.Perform(); worst=max(worst,d.Value()); n+=1
    ex.Next()
print("checked %d surface points: max distance from collar/pin/screw surfaces %.5f mm"%(n,worst))
BRepTools.Write_s(so,"work/sight_collar_solid.brep")
