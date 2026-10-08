import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Shell, ShapeFix_Solid, ShapeFix_Shape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SHELL
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return abs(p.Mass())
s=rd(sys.argv[1])
for it in range(5):
    F=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More(): F.append(ex.Current()); ex.Next()
    keep=[f for f in F if area(f)>=1e-3]; print("iter",it,"drop",len(F)-len(keep))
    if len(keep)==len(F): break
    best=None
    for tol in [0.003,0.01,0.03,0.06]:
        sw=BRepBuilderAPI_Sewing(tol)
        for f in keep: sw.Add(f)
        sw.Perform(); sh=sw.SewedShape(); n=count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE)
        if n==0: best=sh; print("  sewn at",tol); break
    if best is None: print("  could not close"); break
    e=TopExp_Explorer(best,TopAbs_SHELL); fs=ShapeFix_Shell(TopoDS.Shell_s(e.Current())); fs.Perform()
    so=BRepBuilderAPI_MakeSolid(fs.Shell()).Solid(); g=ShapeFix_Solid(so); g.Perform(); so=g.Solid()
    if not BRepCheck_Analyzer(so).IsValid(): g=ShapeFix_Shape(so); g.Perform(); so=g.Shape()
    print("  valid",BRepCheck_Analyzer(so).IsValid()); s=so
BRepTools.Write_s(s,sys.argv[2])
