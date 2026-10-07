import sys
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.ShapeFix import ShapeFix_Face
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
s=rd(sys.argv[1])
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); patches=[]
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); ex2=TopExp_Explorer(w,TopAbs_EDGE); adj=[]
    while ex2.More():
        e=TopoDS.Edge_s(ex2.Current()); f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); a=BRepAdaptor_Surface(f)
        t=str(a.GetType()).split('.')[-1][8:]
        if a.GetType()==GeomAbs_Cylinder: t+=" R%.3f"%a.Cylinder().Radius()
        if a.GetType()==GeomAbs_Cone: t+=" semi%.1f"%np.degrees(a.Cone().SemiAngle())
        adj.append((t,f)); ex2.Next()
    print("loop edges' neighbour faces:",[t for t,_ in adj])
    # try: patch on each distinct neighbour surface; keep the first that gives a valid, positive-area face
    best=None
    for t,f in adj:
        try:
            pf=BRepBuilderAPI_MakeFace(BRep_Tool.Surface_s(f),w,True).Face(); sf=ShapeFix_Face(pf); sf.Perform(); pf=sf.Face()
            p=GProp_GProps(); BRepGProp.SurfaceProperties_s(pf,p)
            sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s); sw.Add(pf); sw.Perform(); sh=sw.SewedShape()
            nl=count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE); si=sum(1 for _ in BRepAlgoAPI_Check(sh,True,True).Result())
            print("   try surface %-14s -> patch area %.3f, loops left %d, self-int %d"%(t,p.Mass(),nl,si))
            if p.Mass()>0 and si==0 and best is None: best=pf
        except Exception as ex_: print("   try",t,"failed",ex_)
    if best is None:
        pf=BRepBuilderAPI_MakeFace(w,True); best=pf.Face() if pf.IsDone() else None; print("   fallback planar:",best is not None)
    patches.append(best); ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s)
for f in patches: sw.Add(f)
sw.Perform(); sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
u=ShapeUpgrade_UnifySameDomain(so,True,True,True); u.Build(); so=TopExp_Explorer(u.Shape(),TopAbs_SOLID).Current()
print("RESULT: loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| faces",count(so,TopAbs_FACE),"| volume %.1f"%vol(so))
BRepTools.Write_s(so,sys.argv[2])
