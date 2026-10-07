import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_IndexedMapOfShape
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(it.Current()); it.Next()
s=shells[123]
# faces whose z-extent overlaps the gap window; and free-bound loops locations
nm={GeomAbs_Plane:'pl',GeomAbs_Cylinder:'cy',GeomAbs_Cone:'co',GeomAbs_Torus:'to',GeomAbs_BSplineSurface:'bs'}
fb=ShapeAnalysis_FreeBounds(s,1e-3)
for tag,comp in (("closed",fb.GetClosedWires()),("open",fb.GetOpenWires())):
    ex=TopExp_Explorer(comp,TopAbs_WIRE)
    while ex.More():
        b=Bnd_Box(); BRepBndLib.Add_s(ex.Current(),b); x=b.Get()
        print("free loop",tag,[round(v,1) for v in x]); ex.Next()
