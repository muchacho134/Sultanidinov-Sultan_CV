exec(open("mag_build.py").read().split("Yb=-359.78")[0])
from OCP.GC import GC_MakeArcOfCircle, GC_MakeSegment
Yb=-359.775; R=1.5
def P(x,z): return gp_Pnt(x,Yb,z)
# footprint outline in the plane y=Yb (x,z), counter-clockwise, rounded corners
segs=[]
def line(a,b): segs.append(BRepBuilderAPI_MakeEdge(GC_MakeSegment(P(*a),P(*b)).Value()).Edge())
def arc(a,m,b): segs.append(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(*a),P(*m),P(*b)).Value()).Edge())
c=np.cos(np.pi/4)*R
line((-9.75,104.33),(9.75,104.33));                     arc((9.75,104.33),(9.75+c,105.83-c),(11.25,105.83))
line((11.25,105.83),(11.25,163.83));                    arc((11.25,163.83),(9.75+c,163.83+c),(9.75,165.33))
line((9.75,165.33),(5.65,165.33)); line((5.65,165.33),(5.65,167.83)); arc((5.65,167.83),(4.15+c,167.83+c),(4.15,169.33))
line((4.15,169.33),(-4.15,169.33)); arc((-4.15,169.33),(-4.15-c,167.83+c),(-5.65,167.83)); line((-5.65,167.83),(-5.65,165.33))
line((-5.65,165.33),(-9.75,165.33)); arc((-9.75,165.33),(-9.75-c,163.83+c),(-11.25,163.83))
line((-11.25,163.83),(-11.25,105.83)); arc((-11.25,105.83),(-9.75-c,105.83-c),(-9.75,104.33))
mw=BRepBuilderAPI_MakeWire()
for e in segs: mw.Add(e)
foot=BRepBuilderAPI_MakeFace(mw.Wire(),True).Face()
body=BRepPrimAPI_MakePrism(foot,gp_Vec(0,90,0)).Shape()
slot=fuse([box(-4,-293.34,165.2,4,-280,170), BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-293.34,165.2),gp_Dir(0,0,1)),4.0,5.0).Shape()])
X0,X1=-12.0,-9.25     # 2 mm deep from the wall at x=-11.25
pocket=fuse([box(X0,-308.743,143.829,X1,-302.143,153.829), box(X0,-313.993,144.079,X1,-308.743,153.579),
             BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(X0,-313.993,148.829),gp_Dir(1,0,0)),4.75,X1-X0).Shape()])
cuts=[None,pocket]
tools=[box(-20,-281.343,100,20,-260,140.829),          # top, front part
       box(-20,-282.343,140.829,20,-260,165.33),        # top, rear part (step at z=140.829)
       box(-20,-284.34,165.33,20,-260,175),             # spine top
       box(-12,-283.843,156.829,-9.75,-260,162.829),    # left-side top notch (left wall only)
       slot]
tools+=cuts[1:]                                         # magazine-catch pocket(s)
mag=cut(body,tools)
u=ShapeUpgrade_UnifySameDomain(mag,True,True,True); u.Build(); mag=u.Shape()
so=TopExp_Explorer(mag,TopAbs_SOLID).Current()
print("MAG: solids",count(mag,TopAbs_SOLID),"| faces",count(mag,TopAbs_FACE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| self-int",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
sh=TopExp_Explorer(so,TopAbs_SHELL).Current(); worst=[]
for i,f in enumerate(F):
    BRepMesh_IncrementalMesh(f,0.1,False,0.3); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc); w_=0
    for k in range(1,t.NbNodes()+1,max(1,t.NbNodes()//25)):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(t.Node(k).Transformed(loc.Transformation())).Vertex(),sh); d.Perform(); w_=max(w_,d.Value())
    worst.append(round(w_,3))
print("original faces -> new surface, max deviation per face:",worst)
from OCP.STEPControl import STEPControl_Reader
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write("work/mag_solid.step")
r=STEPControl_Reader(); r.ReadFile("work/mag_solid.step"); r.TransferRoots(); s2=r.OneShape(); print("STEP round-trip solids:",0 if s2.IsNull() else count(s2,TopAbs_SOLID),"vol %.1f"%(vol(s2) if not s2.IsNull() else 0))
BRepTools.Write_s(so,"work/mag_solid.brep")
