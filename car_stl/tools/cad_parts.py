"""Build wheels, floor and wheel-well cut volumes as B-rep and export a STEP assembly."""
import sys, json, numpy as np
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from occ_util import valid, volume, cut, fuse
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Pln
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepTools import BRepTools
P = json.load(open("parts.json"))
GAP = {"front": 12.0, "rear": 8.0}      # well clearance above the tyre (fender room is 24 / 13 mm)
SHOULDER = 30.0                          # tyre shoulder radius
parts = {}


def cyl_y(x, z, r, y0, y1):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y0, z), gp_Dir(0, 1, 0)), r, y1 - y0).Shape()


def round_all_edges(s, r):
    mf = BRepFilletAPI_MakeFillet(s); e = TopExp_Explorer(s, TopAbs_EDGE)
    while e.More():
        mf.Add(r, TopoDS.Edge_s(e.Current())); e.Next()
    mf.Build()
    return mf.Shape() if mf.IsDone() else s


for lab in ("front", "rear"):
    w = P[lab]
    for side, s in (("L", 1), ("R", -1)):
        y0, y1 = sorted((s * w["y_in"], s * w["y_out"]))
        wheel = round_all_edges(cyl_y(w["x"], w["z"], w["r"], y0, y1), SHOULDER)
        parts[f"Wheel_{lab[0].upper()}{side}"] = wheel
        # wheel region: well cylinder + everything below the axle, from the slot wall outwards
        rw = w["r"] + GAP[lab]
        wy0, wy1 = sorted((s * w["wall"], s * (w["y_out"] + 200)))
        well = cyl_y(w["x"], w["z"], rw, wy0, wy1)
        below = BRepPrimAPI_MakeBox(gp_Pnt(w["x"] - rw, wy0, -50), gp_Pnt(w["x"] + rw, wy1, w["z"])).Shape()
        parts[f"WheelRegion_{lab[0].upper()}{side}"] = fuse(well, below)
# floor: plane z = z0 + kx x, trimmed to the measured floor extent (final trim comes from the body)
f = P["floor"]
poly = BRepBuilderAPI_MakePolygon()
for x, y in ((f["x_min"], -f["y_max"]), (f["x_max"], -f["y_max"]), (f["x_max"], f["y_max"]), (f["x_min"], f["y_max"])):
    poly.Add(gp_Pnt(x, y, f["z0"] + f["kx"] * x))
poly.Close()
parts["Floor"] = BRepBuilderAPI_MakeFace(poly.Wire(), True).Face()
for k, v in parts.items():
    print("%-16s valid %s  %s" % (k, valid(v), ("vol %.1f L" % (volume(v) / 1e6)) if not k == "Floor" else "planar face"))
    BRepTools.Write_s(v, f"part_{k}.brep")
json.dump(list(parts), open("part_names.json", "w"))
