import sys, numpy as np
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRep import BRep_Tool, BRep_Builder
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.GeomConvert import GeomConvert_ApproxCurve, GeomConvert_ApproxSurface
from OCP.GeomAbs import GeomAbs_C1, GeomAbs_C2
from OCP.ShapeAnalysis import ShapeAnalysis_CanonicalRecognition
from OCP.Geom import Geom_Plane, Geom_CylindricalSurface, Geom_BSplineCurve, Geom_BSplineSurface
from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Face, ShapeFix_Edge
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopLoc import TopLoc_Location
from OCP.BRepTopAdaptor import BRepTopAdaptor_FClass2d
from OCP.BRepTools import BRepTools as BT
from OCP.gp import gp_Pnt2d, gp_Pln, gp_Cylinder
from OCP.TopAbs import TopAbs_IN
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.Geom2d import Geom2d_Curve
V=lambda x:BRepCheck_Analyzer(x).IsValid()
src=rd(sys.argv[1]); out=sys.argv[2]
EDGE_MIN=int(sys.argv[3]) if len(sys.argv)>3 else 100; SURF_MIN=int(sys.argv[4]) if len(sys.argv)>4 else 400; MODE=sys.argv[5] if len(sys.argv)>5 else "pse"
def face_samples(f,n=5):
    u0,u1,v0,v1=BT.UVBounds_s(f); cl=BRepTopAdaptor_FClass2d(f,1e-6); sf=BRep_Tool.Surface_s(f); P=[]
    for a in np.linspace(0.1,0.9,n):
        for b in np.linspace(0.1,0.9,n):
            uv=gp_Pnt2d(u0+a*(u1-u0),v0+b*(v1-v0))
            if cl.Perform(uv)==TopAbs_IN: P.append(sf.Value(uv.X(),uv.Y()))
    return P
s=TopoDS.Solid_s(TopExp_Explorer(BRepBuilderAPI_Copy(src).Shape(),TopAbs_SOLID).Current()) if count(src,TopAbs_SOLID) else BRepBuilderAPI_Copy(src).Shape()
B=BRep_Builder(); nconv=0; napx=0; nedge=0
# --- surfaces
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if int(a.GetType())==6:
        bs=a.BSpline(); npol=bs.NbUPoles()*bs.NbVPoles()
        cr=ShapeAnalysis_CanonicalRecognition(f); done=False
        pl=gp_Pln()
        if 'p' in MODE and cr.IsPlane(1e-4,pl):
            loc=TopLoc_Location(); B.UpdateFace(f,Geom_Plane(pl),loc,BRep_Tool.Tolerance_s(f))
            # drop old pcurves -> rebuild
            e2=TopExp_Explorer(f,TopAbs_EDGE)
            while e2.More():
                ed=TopoDS.Edge_s(e2.Current()); B.UpdateEdge(ed,Geom2d_Curve.__new__(Geom2d_Curve) if False else None,f,BRep_Tool.Tolerance_s(ed)); e2.Next()
            sfe=ShapeFix_Edge(); e2=TopExp_Explorer(f,TopAbs_EDGE)
            while e2.More(): sfe.FixAddPCurve(TopoDS.Edge_s(e2.Current()),f,False,1e-4); e2.Next()
            nconv+=1; done=True
        if 's' in MODE and not done and npol>SURF_MIN:
            ap=GeomConvert_ApproxSurface(bs,1e-3,GeomAbs_C1,GeomAbs_C1,8,8,40,1)
            if ap.HasResult() and ap.MaxError()<1e-3 and ap.Surface().NbUPoles()*ap.Surface().NbVPoles()<npol*0.7:
                B.UpdateFace(f,ap.Surface(),TopLoc_Location(),max(BRep_Tool.Tolerance_s(f),ap.MaxError())); napx+=1
    ex.Next()
# --- edges
ex=TopExp_Explorer(s,TopAbs_EDGE); seen=set()
while ex.More():
    ed=TopoDS.Edge_s(ex.Current()); h=ed.__hash__()
    if h not in seen:
        seen.add(h); c=BRepAdaptor_Curve(ed)
        if 'e' in MODE and int(c.GetType())==6 and c.BSpline().NbPoles()>EDGE_MIN:
            loc=TopLoc_Location(); crv,f0,l0=BRep_Tool.Curve_s(ed,loc,0.0,0.0) if False else (None,0,0)
            g=c.BSpline(); ap=GeomConvert_ApproxCurve(g,5e-4,GeomAbs_C2,60,8)
            if ap.HasResult() and ap.MaxError()<5e-4 and ap.Curve().NbPoles()<g.NbPoles()*0.7:
                B.UpdateEdge(ed,ap.Curve(),max(BRep_Tool.Tolerance_s(ed),ap.MaxError())); nedge+=1
    ex.Next()
ok=V(s)
if not ok:
    sf=ShapeFix_Shape(s); sf.Perform(); s=sf.Shape(); ok=V(s)
# deviation check vs source
dev=0.0; fx=TopExp_Explorer(src,TopAbs_FACE); k=0
while fx.More() and k<4000:
    for p in face_samples(TopoDS.Face_s(fx.Current()),3):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),s); d.Perform(); dev=max(dev,d.Value()); k+=1
    fx.Next()
print("planes %d, surf approx %d, edges approx %d | valid %s | vol %.2f -> %.2f | max dev %.5f"%(nconv,napx,nedge,ok,vol(src),vol(s),dev))
BRepTools.Write_s(s,out)
