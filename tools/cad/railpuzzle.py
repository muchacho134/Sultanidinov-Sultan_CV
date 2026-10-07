import sys
exec(open("puzzle.py").read().split("print(\"parts\",len(parts))")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_Transform
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.gp import gp_Trsf, gp_Vec
from OCP.TopoDS import TopoDS_Shape
from OCP.BRep import BRep_Builder
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
def loops(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-3); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
def bb(s): b=Bnd_Box(); BRepBndLib.Add_s(s,b); return [round(v,1) for v in b.Get()]
for k in ("P262","P266","P267","P268"): print(k,"bbox",bb(parts[k]))
rail=TopoDS_Shape(); BRepTools.Read_s(rail,"work/shell_a.brep",BRep_Builder())  # rail with rib fix + 266 already sewn in
print("rail(+ribs+266) free loops:",loops(rail))
for combo in (("P267",),("P268",),("P267","P268")):
    for tol in (0.01,0.05,0.2):
        sw=BRepBuilderAPI_Sewing(tol); sw.Add(rail)
        for k in combo: sw.Add(parts[k])
        sw.Perform(); r=sw.SewedShape(); L=[]; ex=TopExp_Explorer(r,TopAbs_SHELL)
        while ex.More(): L.append(ex.Current()); ex.Next()
        print(f"+{'+'.join(combo)} tol {tol}: shells {len(L)} free loops {[loops(x) for x in L]} multiple-edges {sw.NbMultipleEdges()}")
def flen(s):
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); L=0
    for i in range(1,m.Extent()+1):
        if m.FindFromIndex(i).Size()==1: L+=GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(TopoDS.Edge_s(m.FindKey(i))))
    return L
print("open boundary length: rail %.0f | 267 %.0f | 268 %.0f"%(flen(rail),flen(parts['P267']),flen(parts['P268'])))
sw=BRepBuilderAPI_Sewing(0.05); sw.Add(rail); sw.Add(parts['P267']); sw.Add(parts['P268']); sw.Perform(); r=sw.SewedShape()
print("rail+267+268 sewn @0.05: open boundary %.0f mm (sum before %.0f)"%(flen(r),flen(rail)+flen(parts['P267'])+flen(parts['P268'])))
BRepTools.Write_s(r,"work/rail_267_268.brep")
