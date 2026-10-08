exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.gp import gp_Ax2, gp_Dir
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return abs(p.Mass())
def onef(s):
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); n=0
    for k in range(1,m.Extent()+1):
        ed=TopoDS.Edge_s(m.FindKey(k)); L=list(m.FindFromIndex(k))
        if BRep_Tool.Degenerated_s(ed): continue
        if len(L)==1 and not BRep_Tool.IsClosed_s(ed,TopoDS.Face_s(L[0])): n+=1
    return n
def ntiny(s):
    n=0; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        if area(ex.Current())<0.01: n+=1
        ex.Next()
    return n
so=rd("work/p244_m1.brep"); P=rd("work/cur_P223.brep"); v0=vol(so)
pk=[rd("work/closed_411.brep"),rd("work/closed_421.brep"),rd("work/closed_410.brep")]
best=None
for xs in [11.3,12.3,12.65,12.8]:
  for ys in [-283.0,-282.9]:
    sides=[BRepAlgoAPI_Common(P,BRepPrimAPI_MakeBox(gp_Pnt(x0,ys,252),gp_Pnt(x1,-245,300)).Shape()).Shape() for x0,x1 in [(-25,-xs),(xs,25)]]
    lug=BRepPrimAPI_MakeBox(gp_Pnt(-12.65,-283.1,255.5),gp_Pnt(12.65,-273.69,283.5)).Shape()
    bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,255.5),gp_Dir(0,0,1)),12.7,296.63-255.5).Shape()
    tool=lug
    for t_ in sides+[bore]: tool=BRepAlgoAPI_Fuse(tool,t_).Shape()
    t=cut(so,[tool],0.0)
    if t is None or not V(t) or not (5000<v0-vol(t)<9000): print(xs,ys,"cut bad"); continue
    t2=cut(t,pk,0.0)
    if t2 is None or not V(t2): print(xs,ys,"pockets bad"); continue
    o=onef(t2); n=ntiny(t2); print("xs",xs,"ys",ys,"open edges",o,"tiny",n,"removed %.1f"%(v0-vol(t)),flush=True)
    if best is None or (o,n)<best[0]: best=((o,n),xs,ys); BRepTools.Write_s(t2,"work/p244_m3.brep")
print("best",best)
