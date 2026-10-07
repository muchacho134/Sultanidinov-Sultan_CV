import numpy as np, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape, TopTools_IndexedMapOfShape
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepTools import BRepTools as BT
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
s=rd("work/x_P111.brep")
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def bx(f): b=Bnd_Box(); BRepBndLib.Add_s(f,b); return np.array(b.Get())
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
def nwires(f):
    n=0; ex=TopExp_Explorer(f,TopAbs_WIRE)
    while ex.More(): n+=1; ex.Next()
    return n
def outer_only(f):
    a=BRepAdaptor_Surface(f); surf=BRep_Tool.Surface_s(f); ow=BT.OuterWire_s(f)
    nf=BRepBuilderAPI_MakeFace(surf,ow,True).Face()
    if f.Orientation()==TopAbs_REVERSED: nf.Reverse()
    return nf
F=faces(s); keep=[]; dropped=collections.Counter()
for f in F:
    x=bx(f); a=BRepAdaptor_Surface(f); t=a.GetType(); ar=area(f)
    if x[2]>=-243.51 and x[5]<=-243.34 and not (t==GeomAbs_Plane and ar>100): dropped['letter faces']+=1; continue
    if x[1]>=-234.80 and ar<8: dropped['top-mark faces']+=1; continue
    keep.append(f)
new=[]
for f in keep:
    if nwires(f)>1: new.append(outer_only(f)); dropped['inner wires removed (faces rebuilt)']+=1
    else: new.append(f)
print(dict(dropped))
def sew(fs,tol=1e-4):
    sw=BRepBuilderAPI_Sewing(tol)
    for f in fs: sw.Add(f)
    sw.Perform(); return sw.SewedShape()

sh=sew(new); BRepTools.Write_s(sh,"work/p111_pass0.brep")
fb=ShapeAnalysis_FreeBounds(sh,1e-4); w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,w); print("pass0 faces",len(faces(sh)),"loops",w.Extent())
