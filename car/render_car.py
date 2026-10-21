import sys, pickle, numpy as np
from overlay import load, overlay
from shade import render_sheet, vertex_normals
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from build_car import faces, wheel
import body as B

COL = {None: (0.93, 0.93, 0.95), 'well': (0.25, 0.25, 0.27), 'dark': (0.16, 0.16, 0.18),
       'recess': (0.55, 0.56, 0.6), 'glass': (0.22, 0.27, 0.33), 'tyre': (0.1, 0.1, 0.1),
       'disc': (0.72, 0.73, 0.76), 'lamp': (0.62, 0.72, 0.85)}


def mesh_faces(shape, labels, defl=0.5):
    BRepMesh_IncrementalMesh(shape, defl, False, 0.12, True)
    V, F, C, off = [], [], [], 0
    for f, lab in zip(faces(shape), labels):
        loc = TopLoc_Location(); t = BRep_Tool.Triangulation_s(f, loc)
        if t is None: continue
        tr = loc.Transformation()
        for i in range(1, t.NbNodes() + 1):
            p = t.Node(i).Transformed(tr); V.append((p.X(), p.Y(), p.Z()))
        rev = f.Orientation() == TopAbs_REVERSED
        for i in range(1, t.NbTriangles() + 1):
            a, b, c = t.Triangle(i).Get()
            F.append((off + a - 1, off + c - 1, off + b - 1) if rev else (off + a - 1, off + b - 1, off + c - 1))
            C.append(COL[lab])
        off += t.NbNodes()
    return V, F, C


def parts():
    body = load("out/body.brep"); tags = pickle.load(open("out/body_tags.pkl", "rb"))
    out = [(body, tags), ]
    g = load("out/glass.brep"); out.append((g, ['glass'] * len(faces(g))))
    l = load("out/lamps.brep"); out.append((l, ['lamp'] * len(faces(l))))
    g2 = load("out/grille.brep"); out.append((g2, ['dark'] * len(faces(g2))))
    for xa in (B.AXLE_F, B.AXLE_R):
        for s in (1, -1):
            wh = wheel(xa, s)
            out.append((wh, ['tyre'] * len(faces(wh))))
    return out


if __name__ == "__main__":
    V, F, C = [], [], []
    comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
    for shp, lab in parts():
        v, f, c = mesh_faces(shp, lab)
        F += [(a + len(V), b + len(V), cc + len(V)) for a, b, cc in f]; V += v; C += c
        bb.Add(comp, shp)
    V, F, C = np.array(V), np.array(F), np.array(C)
    render_sheet(V, F, C, sys.argv[1], N=vertex_normals(V, F))
    if len(sys.argv) > 2:
        overlay(comp, sys.argv[2])
