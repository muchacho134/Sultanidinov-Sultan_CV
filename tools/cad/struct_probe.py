import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_IndexedDataMapOfShapeListOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
print("top type", sh.ShapeType())
# top-level children types
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID)  # shells not inside solid
shells=[]
while it.More(): shells.append(TopoDS.Shell_s(it.Current())); it.Next()
it=TopExp_Explorer(sh,TopAbs_FACE,TopAbs_SHELL)
loose=[]
while it.More(): loose.append(it.Current()); it.Next()
print("free shells (not in solid):",len(shells),"loose faces:",len(loose))
rows=[]
for i,s in enumerate(shells):
    nf=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,nf)
    a=BRepCheck_Analyzer(s)
    fb=ShapeAnalysis_FreeBounds(s,1e-4)
    fo=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_EDGE,fo)
    fc=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_EDGE,fc)
    bb=Bnd_Box(); BRepBndLib.Add_s(s,bb)
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
    rows.append((i,nf.Extent(),a.IsValid(),fc.Extent(),fo.Extent(),round(p.Mass(),1), [round(x,1) for x in bb.Get()]))
for r in rows: print(r)
