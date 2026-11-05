"""Render a STEP with every B-rep face in its own colour (patch layout), half car only."""
import sys, numpy as np
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load
from shade import render_sheet, vertex_normals
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
s = load(sys.argv[1])
b = Bnd_Box(); BRepBndLib.Add_s(s, b); print("bbox", [round(v) for v in b.Get()])
e = TopExp_Explorer(s, TopAbs_SOLID); k = 0
while e.More():
    bb = Bnd_Box(); BRepBndLib.Add_s(e.Current(), bb)
    n = 0; f = TopExp_Explorer(e.Current(), TopAbs_FACE)
    while f.More(): n += 1; f.Next()
    print(" solid", k, "faces", n, "bbox", [round(v) for v in bb.Get()]); k += 1; e.Next()
BRepMesh_IncrementalMesh(s, float(sys.argv[3]), False, 0.3, True)
rng = np.random.default_rng(7)
V, F, C, off = [], [], [], 0
f = TopExp_Explorer(s, TopAbs_FACE)
while f.More():
    fa = TopoDS.Face_s(f.Current()); loc = TopLoc_Location(); t = BRep_Tool.Triangulation_s(fa, loc)
    if t is not None:
        tr = loc.Transformation()
        P = np.array([[t.Node(i).Transformed(tr).X(), t.Node(i).Transformed(tr).Y(), t.Node(i).Transformed(tr).Z()] for i in range(1, t.NbNodes() + 1)])
        T = np.array([t.Triangle(i).Get() for i in range(1, t.NbTriangles() + 1)]) - 1
        if fa.Orientation() == TopAbs_REVERSED: T = T[:, [0, 2, 1]]
        col = rng.uniform(0.25, 0.95, 3)
        V.append(P); F.append(T + off); C.append(np.tile(col, (len(T), 1))); off += len(P)
    f.Next()
V, F, C = np.vstack(V), np.vstack(F), np.vstack(C)
if sys.argv[4] == "tesla":                    # Tesla file: X = width, Y = length (nose at +Y) -> X length, Y width
    V = np.c_[-V[:, 1], V[:, 0], V[:, 2]]; F = F[:, [0, 2, 1]]
keep = V[F].mean(1)[:, 1] <= 5.0              # half car (y <= 0)
render_sheet(V, F[keep], C[keep], sys.argv[2], N=vertex_normals(V, F))
