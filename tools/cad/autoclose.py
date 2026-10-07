import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Copy
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.GeomAbs import GeomAbs_C0
from OCP.ShapeFix import ShapeFix_Face, ShapeFix_Shell, ShapeFix_Solid, ShapeFix_Shape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRep import BRep_Tool
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
def maxtol(sh):
    mt=0; e=TopExp_Explorer(sh,TopAbs_EDGE)
    while e.More(): mt=max(mt,BRep_Tool.Tolerance_s(TopoDS.Edge_s(e.Current()))); e.Next()
    return mt
s=rd(sys.argv[1]); tol=float(sys.argv[3]) if len(sys.argv)>3 else 0.003
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); new=[]
while ex.More():
    w=TopoDS.Wire_s(BRepBuilderAPI_Copy(ex.Current()).Shape()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False)
    mf=BRepBuilderAPI_MakeFace(w,True)
    if mf.IsDone(): f=mf.Face(); how="plane"
    else:
        fl=BRepOffsetAPI_MakeFilling(3,40,4,False,1e-6,1e-5,0.01,0.1,10,30); e2=TopExp_Explorer(w,TopAbs_EDGE)
        while e2.More(): fl.Add(TopoDS.Edge_s(e2.Current()),GeomAbs_C0); e2.Next()
        fl.Build(); f=TopoDS.Face_s(fl.Shape()); how="fill"
    sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
    fb2=Bnd_Box(); BRepBndLib.AddOptimal_s(f,fb2,False,False)
    print(how,"edges",count(w,TopAbs_EDGE),"area %.2f"%area(f),"tol %.4f"%maxtol(f),"bbox grow %.2f"%(max(abs(a-c) for a,c in zip(fb2.Get(),b.Get()))))
    new.append(f); ex.Next()
sw=BRepBuilderAPI_Sewing(tol); sw.Add(s)
for f in new: sw.Add(f)
sw.Perform(); sh=sw.SewedShape()
print("loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"shells",count(sh,TopAbs_SHELL))
e=TopExp_Explorer(sh,TopAbs_SHELL); she=TopoDS.Shell_s(e.Current()); fs=ShapeFix_Shell(she); fs.Perform(); she=fs.Shell()
so=BRepBuilderAPI_MakeSolid(she).Solid(); f=ShapeFix_Solid(so); f.Perform(); so=f.Solid()
if not BRepCheck_Analyzer(so).IsValid():
    f=ShapeFix_Shape(so); f.Perform(); so=f.Shape()
print("RESULT valid",BRepCheck_Analyzer(so).IsValid(),"vol %.2f"%vol(so),"solids",count(so,TopAbs_SOLID))
BRepTools.Write_s(so,sys.argv[2])
