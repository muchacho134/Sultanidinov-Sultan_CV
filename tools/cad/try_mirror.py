import sys
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import *
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
shell=TopExp_Explorer(rd("work/shell_a.brep"),TopAbs_SHELL).Current(); newc=rd("work/mirror_new.brep")
def faces(s):
    L=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def loops(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-3); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
print("before: free loops",loops(shell))
for tol in (0.02,0.1):
    sw=BRepBuilderAPI_Sewing(tol)
    for f in faces(shell)+faces(newc): sw.Add(f)
    sw.Perform(); res=sw.SewedShape()
    L=[]; ex=TopExp_Explorer(res,TopAbs_SHELL)
    while ex.More(): L.append(ex.Current()); ex.Next()
    print(f"tol {tol}: shells {len(L)} free loops {[loops(x) for x in L]} multiple-edges {sw.NbMultipleEdges()} free-edges {sw.NbFreeEdges()}")
