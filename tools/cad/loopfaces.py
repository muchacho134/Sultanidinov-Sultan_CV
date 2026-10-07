import sys
exec(open("p110_diag.py").read().split("s=rd(")[0] if False else "")
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_IndexedMapOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE).Current()
seen=[]; ex=TopExp_Explorer(w,TopAbs_EDGE)
while ex.More():
    f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(ex.Current())).First())
    if not any(f.IsSame(g) for g in seen): seen.append(f)
    ex.Next()
for f in seen:
    a=BRepAdaptor_Surface(f); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get(); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    nw=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_WIRE,nw)
    t=str(a.GetType()).split('.')[-1][8:]
    if a.GetType()==GeomAbs_Plane: n=a.Plane().Axis().Direction(); t+=" n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
    print("  %-26s area %8.3f wires %d x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(t,p.Mass(),nw.Extent(),x[0],x[3],x[1],x[4],x[2],x[5]))
