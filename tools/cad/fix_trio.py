exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Wire
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.BRep import BRep_Tool
from OCP.BRepTools import BRepTools as BT
from OCP.GeomAbs import *
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.TopTools import TopTools_IndexedMapOfShape
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
def si(sh): return sum(1 for _ in BRepAlgoAPI_Check(sh,True,True).Result())
def loops(sh): return count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE)
def sew(fs):
    sw=BRepBuilderAPI_Sewing(1e-4)
    for f in fs: sw.Add(f)
    sw.Perform(); return sw.SewedShape()
def solidify(sh):
    sh=TopoDS.Shell_s(TopExp_Explorer(sh,TopAbs_SHELL).Current())
    so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); return fx.Solid()
def report(nm,so): print(f"{nm}: valid {BRepCheck_Analyzer(so).IsValid()} | self-int {si(so)} | faces {count(so,TopAbs_FACE)} | volume {vol(so):.1f}")
# ---- P152: end face stored as ring R3..3.7 -> rebuild as disc from the rod's R3 edge
s=rd("work/x_P152.brep"); F=faces(s)
ring=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(area(f)-14.734)<0.01][0]
wires=[]; ex=TopExp_Explorer(ring,TopAbs_WIRE)
while ex.More(): wires.append(TopoDS.Wire_s(ex.Current())); ex.Next()
def wr(w):
    e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current()); return BRepAdaptor_Curve(e).Circle().Radius()
inner=[w for w in wires if abs(wr(w)-3.0)<0.05][0]
disc=BRepBuilderAPI_MakeFace(inner,True).Face(); print("P152 new end disc area %.3f (R3 disc = %.3f)"%(area(disc),np.pi*9))
sh=sew([f for f in F if not f.IsSame(ring)]+[disc]); print("P152 loops",loops(sh)); P152=solidify(sh); report("P152",P152)
# ---- P150: back face at z=296.09 bounded by the open loop
s=rd("work/x_P150.brep"); w=TopoDS.Wire_s(TopExp_Explorer(ShapeAnalysis_FreeBounds(s,1e-4).GetClosedWires(),TopAbs_WIRE).Current())
sfw=ShapeFix_Wire(); sfw.Load(w); sfw.FixReorder(); sfw.FixConnected(); w=sfw.Wire()
pf=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,-240,296.09),gp_Dir(0,0,1)),w,True).Face()
sf=ShapeFix_Face(pf); sf.FixOrientation(); sf.Perform(); pf=sf.Face(); print("P150 back face area %.3f"%area(pf))
sh=sew(faces(s)+[pf]); print("P150 loops",loops(sh),"| shell self-int",si(sh)); P150=solidify(sh); report("P150",P150)
BRepTools.Write_s(P152,"work/P152_solid.brep"); BRepTools.Write_s(P150,"work/P150_solid.brep")
