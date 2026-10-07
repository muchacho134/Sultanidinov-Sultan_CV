import sys, numpy as np
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
ZLO,ZHI=float(sys.argv[1]),float(sys.argv[2])
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[3] if len(sys.argv)>3 else "work/shell_a.brep",BRep_Builder())
F=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More(): F.append(TopoDS.Face_s(ex.Current())); ex.Next()
def bx(f): b=Bnd_Box(); BRepBndLib.Add_s(f,b); return np.array(b.Get())
def in_pos(x): return x[0]>=6.3 and x[3]<=12.2 and x[1]>=-245.5 and x[4]<=-230.4 and x[2]>=ZLO and x[5]<=ZHI
def in_neg(x): return x[3]<=-6.3 and x[0]>=-12.2 and x[1]>=-245.5 and x[4]<=-230.4 and x[2]>=ZLO and x[5]<=ZHI
pos=[f for f in F if in_pos(bx(f))]; neg=[f for f in F if in_neg(bx(f))]
print("z range",ZLO,ZHI,"| +x faces to copy:",len(pos),"| -x faces replaced:",len(neg))
tr=gp_Trsf(); tr.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0)))
mir=[TopoDS.Face_s(BRepBuilderAPI_Transform(f,tr,True).Shape()) for f in pos]
keep=[f for f in F if not any(f.IsSame(n) for n in neg)]
def loops(sh):
    fb=ShapeAnalysis_FreeBounds(sh,1e-3); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
for tol in (1e-3,0.02):
    sw=BRepBuilderAPI_Sewing(tol)
    for f in keep+mir: sw.Add(f)
    sw.Perform(); res=sw.SewedShape(); sh=TopoDS.Shell_s(TopExp_Explorer(res,TopAbs_SHELL).Current())
    print(f"sew tol {tol}: free loops {loops(sh)}  free edges {sw.NbFreeEdges()} multiple edges {sw.NbMultipleEdges()}")
BRepTools.Write_s(sh,"work/shell_b.brep")
