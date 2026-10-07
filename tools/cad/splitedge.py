exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCP.BRepTools import BRepTools_WireExplorer, BRepTools as BT
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Face
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopAbs import TopAbs_VERTEX
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
P=lambda v:BRep_Tool.Pnt_s(v)
def ends(e): return P(TopExp.FirstVertex_s(e,True)),P(TopExp.LastVertex_s(e,True))
s=rd("work/p244_s16.brep")
fb=ShapeAnalysis_FreeBounds(s,1e-4); xs=set(); vx=TopExp_Explorer(fb.GetClosedWires(),TopAbs_VERTEX); V={}
while vx.More(): q=P(TopoDS.Vertex_s(vx.Current())); V[round(q.X(),3)]=q; vx.Next()
print(sorted(V))
F=[]; ex=TopExp_Explorer(s,TopAbs_FACE); tgt=None
while ex.More():
    f=TopoDS.Face_s(ex.Current()); hit=False
    e2=TopExp_Explorer(f,TopAbs_EDGE)
    while e2.More():
        a,b=ends(TopoDS.Edge_s(e2.Current()))
        if abs(a.Z()-256.22)<0.01 and abs(b.Z()-256.22)<0.01 and abs(a.Y()+283.1)<0.01 and abs(b.Y()+283.1)<0.01 and abs(a.X()-b.X())>25: hit=True
        e2.Next()
    if hit and tgt is None: tgt=f
    else: F.append(f)
    ex.Next()
E=[]; we=BRepTools_WireExplorer(BT.OuterWire_s(tgt),tgt)
while we.More(): E.append(TopoDS.Edge_s(we.Current())); we.Next()
mw=BRepBuilderAPI_MakeWire()
for e in E:
    a,b=ends(e)
    if abs(a.Z()-256.22)<0.01 and abs(b.Z()-256.22)<0.01 and abs(a.X()-b.X())>25:
        ks=sorted(V,reverse=a.X()>b.X()); ks=[k for k in ks if min(a.X(),b.X())+1e-3<k<max(a.X(),b.X())-1e-3]
        seq=[a]+[V[k] for k in ks]+[b]
        for p0,p1 in zip(seq[:-1],seq[1:]): mw.Add(BRepBuilderAPI_MakeEdge(p0,p1).Edge())
        print("split into",len(seq)-1)
    else: mw.Add(e)
nf=BRepBuilderAPI_MakeFace(BRep_Tool.Surface_s(tgt),mw.Wire(),True).Face()
sf=ShapeFix_Face(nf); sf.Perform(); nf=sf.Face()
print("area %.2f -> %.2f valid %s"%(area(tgt),area(nf),BRepCheck_Analyzer(nf).IsValid()))
sw=BRepBuilderAPI_Sewing(0.003)
for f in F: sw.Add(f)
sw.Add(nf); sw.Perform(); BRepTools.Write_s(sw.SewedShape(),"work/p244_s17.brep")
