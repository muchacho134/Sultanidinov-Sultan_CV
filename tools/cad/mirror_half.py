import sys, numpy as np, collections
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_Sewing
from OCP.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
src=sys.argv[1]; keep_side=sys.argv[2]   # '+' => keep +x half and mirror it to -x
s=TopoDS_Shape(); BRepTools.Read_s(s,src,BRep_Builder())
F=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More(): F.append(TopoDS.Face_s(ex.Current())); ex.Next()
def bx(f): b=Bnd_Box(); BRepBndLib.Add_s(f,b); return np.array(b.Get())
cen,pos,neg=[],[],[]
for f in F:
    x=bx(f)
    if x[0]<-0.01 and x[3]>0.01: cen.append(f)
    elif x[0]>=-0.01: pos.append(f)
    else: neg.append(f)
print("faces: centre",len(cen),"| +x",len(pos),"| -x",len(neg))
tr=gp_Trsf(); tr.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0)))
good=pos if keep_side=='+' else neg
mir=[TopoDS.Face_s(BRepBuilderAPI_Transform(f,tr,True).Shape()) for f in good]
def loops(sh):
    fb=ShapeAnalysis_FreeBounds(sh,1e-3); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
sw0=BRepBuilderAPI_Sewing(1e-3)
for f in F: sw0.Add(f)
sw0.Perform(); print("BASELINE shell_a: free loops",loops(TopoDS.Shell_s(TopExp_Explorer(sw0.SewedShape(),TopAbs_SHELL).Current())),"free edges",sw0.NbFreeEdges())
for tol in (1e-3,0.01):
    sw=BRepBuilderAPI_Sewing(tol)
    for f in cen+good+mir: sw.Add(f)
    sw.Perform(); res=sw.SewedShape(); L=[]; ex=TopExp_Explorer(res,TopAbs_SHELL)
    while ex.More(): L.append(TopoDS.Shell_s(ex.Current())); ex.Next()
    print(f"MIRRORED (keep {keep_side}x half) tol {tol}: shells {len(L)} free loops {[loops(x) for x in L]} free edges {sw.NbFreeEdges()} multiple {sw.NbMultipleEdges()}")
BRepTools.Write_s(L[0],"work/shell_sym.brep")
