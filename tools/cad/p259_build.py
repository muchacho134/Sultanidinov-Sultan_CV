exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCP.gp import gp_Vec, gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
src=rd("work/x_P259.brep")
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
F=faces(src)
top=[f for f in F if abs(area(f)-114.56)<0.05][0]; bot=[f for f in F if abs(area(f)-99.98)<0.05][0]
plateA=BRepPrimAPI_MakePrism(bot,gp_Vec(0,0,4.0)).Shape(); plateB=BRepPrimAPI_MakePrism(top,gp_Vec(0,0,-4.0)).Shape()
print("plate prisms: %.1f / %.1f mm3"%(vol(plateA),vol(plateB)))
# knob: stadium (two R4.83 cylinders along x + box), x from -23.65 to -20.35
X0,X1,R,ZC,YA,YB=-23.65,-20.35,4.83,174.54,-274.03,-277.07
c1=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(X0,YA,ZC),gp_Dir(1,0,0)),R,X1-X0).Shape()
c2=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(X0,YB,ZC),gp_Dir(1,0,0)),R,X1-X0).Shape()
bx=BRepPrimAPI_MakeBox(gp_Pnt(X0,YB,ZC-R),gp_Pnt(X1,YA,ZC+R)).Shape()
def fuse(shapes):
    a=TopTools_ListOfShape(); a.Append(shapes[0]); t=TopTools_ListOfShape()
    for s in shapes[1:]: t.Append(s)
    f=BRepAlgoAPI_Fuse(); f.SetArguments(a); f.SetTools(t); f.SetFuzzyValue(1e-6); f.Build(); return f.Shape()
body=fuse([plateA,plateB,c1,c2,bx])
# V-grooves: 45 deg, 0.5 deep (apex at x=-23.15), 1.0 wide at x=-23.65, pitch 1.6, apex y = -281.15 + 1.6k
grooves=[]
for k in range(9):
    ya=-281.15+1.6*k
    if ya>-269.2+0.5: break
    poly=BRepBuilderAPI_MakePolygon(gp_Pnt(-23.15,ya,160),gp_Pnt(-24.65,ya-1.5,160),gp_Pnt(-24.65,ya+1.5,160),True)
    fc=BRepBuilderAPI_MakeFace(poly.Wire(),True).Face(); grooves.append(BRepPrimAPI_MakePrism(fc,gp_Vec(0,0,30)).Shape())
print("grooves cut:",len(grooves),"apex y:",[round(-281.15+1.6*k,2) for k in range(len(grooves))])
a=TopTools_ListOfShape(); a.Append(body); t=TopTools_ListOfShape()
for g in grooves: t.Append(g)
cut=BRepAlgoAPI_Cut(); cut.SetArguments(a); cut.SetTools(t); cut.SetFuzzyValue(1e-6); cut.Build()
u=ShapeUpgrade_UnifySameDomain(cut.Shape(),True,True,True); u.Build(); r=u.Shape()
so=TopExp_Explorer(r,TopAbs_SOLID).Current()
print("P259: solids",count(r,TopAbs_SOLID),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
# every original face must lie on the new surface
BRepMesh_IncrementalMesh(src,0.05,False,0.2); worst=0; n=0; wp=None
for f in F:
    loc=TopLoc_Location(); tr=BRep_Tool.Triangulation_s(f,loc)
    if tr is None: continue
    for i in range(1,tr.NbNodes()+1,max(1,tr.NbNodes()//30)):
        p=tr.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),so); d.Perform()
        if d.Value()>worst: worst=d.Value(); wp=(p.X(),p.Y(),p.Z())
        n+=1
print("original surface points checked %d: max distance to new solid surface %.4f mm at %s"%(n,worst,np.round(wp,2) if wp else None))
BRepTools.Write_s(so,"work/p259_solid.brep")
