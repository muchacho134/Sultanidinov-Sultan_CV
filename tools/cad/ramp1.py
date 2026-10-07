import sys, numpy as np
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Copy
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.GeomFill import GeomFill
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.GeomAbs import GeomAbs_C2
from OCP.gp import gp_Pnt
from OCP.ShapeFix import ShapeFix_Face
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
s=rd(sys.argv[1]); c=[0,-269.95,276.42]
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); best=None
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get(); cc=[(x[i]+x[i+3])/2 for i in range(3)]
    d=sum((cc[i]-c[i])**2 for i in range(3))
    if best is None or d<best[0]: best=(d,w)
    ex.Next()
E=[]; we=BRepTools_WireExplorer(best[1])
while we.More(): E.append(TopoDS.Edge_s(BRepBuilderAPI_Copy(we.Current()).Shape())); we.Next()
def samp(e,rev,n=40):
    cv=BRepAdaptor_Curve(e); a,b=cv.FirstParameter(),cv.LastParameter()
    if e.Orientation()==1: a,b=b,a   # reversed edge
    ts=np.linspace(a,b,n); 
    if rev: ts=ts[::-1]
    return [[cv.Value(t).X(),cv.Value(t).Y(),cv.Value(t).Z()] for t in ts]
R=[]; 
for i in range(13,20): R+=samp(E[i],False)
L=[]
for i in range(6,-1,-1): L+=samp(E[i],True)
def clean(P):
    P=np.array(P); out=[P[0]]
    for p in P[1:]:
        if np.linalg.norm(p-out[-1])>1e-3: out.append(p)
    return np.array(out)
R=clean(R); L=clean(L)
print("R",R[0],R[-1]); print("L",L[0],L[-1])
def reparam(P,n=120):
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P[:,1:],axis=0),axis=1))]; d/=d[-1]
    u=np.linspace(0,1,n); return np.stack([np.interp(u,d,P[:,k]) for k in range(3)],1), d
def bs(P):
    arr=TColgp_Array1OfPnt(1,len(P))
    for k,p in enumerate(P): arr.SetValue(k+1,gp_Pnt(*p))
    return GeomAPI_PointsToBSpline(arr,3,8,GeomAbs_C2,1e-4).Curve()
# fit curves through all raw points (keep accuracy), parameter by yz arclength
cR=bs(R); cL=bs(L)
srf=GeomFill.Surface_s(cR,cL)
# check that original side points lie on surface
dev=0
for P in (R,L):
    for p in P[::5]:
        pr=GeomAPI_ProjectPointOnSurf(gp_Pnt(*p),srf); dev=max(dev,pr.LowerDistance())
print("side dev on surface %.5f"%dev)
mw=BRepBuilderAPI_MakeWire()
for e in E: mw.Add(e)
f=BRepBuilderAPI_MakeFace(srf,mw.Wire(),True).Face()
sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
if area(f)<0:
    f=BRepBuilderAPI_MakeFace(srf,TopoDS.Wire_s(mw.Wire().Reversed()),True).Face(); sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
print("ramp area %.2f valid %s"%(area(f),BRepCheck_Analyzer(f).IsValid()))
sw=BRepBuilderAPI_Sewing(0.003); sw.Add(s); sw.Add(f); sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("loops",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE))
