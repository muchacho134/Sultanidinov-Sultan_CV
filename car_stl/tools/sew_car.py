"""Sew the panel faces (+ exact wheel-well cylinders and slot walls) into one shell for the half car,
report open edges, then mirror across y = 0 and sew the full car; make a solid if it closes."""
import sys, json
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load
from build_car import faces
from occ_util import valid, volume
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_FACE
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.ShapeFix import ShapeFix_Shell, ShapeFix_Solid
PANELS, DONE, TOL, OUT = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
fs = list(faces(load(PANELS)))
if DONE != "-":
    names = json.load(open(DONE.replace(".brep", "_names.json")))
    fs += [f for f, n in zip(faces(load(DONE)), names) if "floor" not in n]


def sew(face_list, tol):
    sw = BRepBuilderAPI_Sewing(tol); [sw.Add(f) for f in face_list]; sw.Perform()
    return sw, sw.SewedShape()


sw, half = sew(fs, TOL)
print("half: faces %d  free edges %d  multiple edges %d" % (len(fs), sw.NbFreeEdges(), sw.NbMultipleEdges()))
BRepTools.Write_s(half, OUT.replace(".brep", "_half.brep"))
t = gp_Trsf(); t.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
mir = BRepBuilderAPI_Transform(half, t, True).Shape()
sw2, full = sew([half, mir], TOL)
print("full: free edges %d" % sw2.NbFreeEdges())
e = TopExp_Explorer(full, TopAbs_SHELL); shells = []
while e.More(): shells.append(TopoDS.Shell_s(e.Current())); e.Next()
print("shells", len(shells))
if len(shells) == 1 and sw2.NbFreeEdges() == 0:
    fx = ShapeFix_Shell(shells[0]); fx.Perform()
    so = BRepBuilderAPI_MakeSolid(fx.Shell()).Solid(); fs_ = ShapeFix_Solid(so); fs_.Perform(); so = fs_.Solid()
    print("solid valid", valid(so), "volume %.3f m3 (STL 6.42 with wheels fused)" % (volume(so) / 1e9))
    BRepTools.Write_s(so, OUT)
else:
    BRepTools.Write_s(full, OUT)
