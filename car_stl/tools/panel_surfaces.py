"""One CAD face per panel, bounded exactly by its border curves from the network.

For each panel: collect the network curves naming it, chain them into its outer loop (largest
cycle), build B-spline edges, and fill with BRepOffsetAPI_MakeFilling: border edges as C0
constraints (shared exactly with the neighbours) + interior points sampled from the STL panel.
Reports per panel: valid, deviation of the STL points to the face.
"""
import sys, json, numpy as np, trimesh, networkx as nx
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from occ_util import valid
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeVertex
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.GeomAbs import GeomAbs_C0
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2], allow_pickle=True)
NET = {k: np.array(v) for k, v in json.load(open(sys.argv[3])).items()}; OUT = sys.argv[4]
ONLY = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] else None
EDGE, N_INT = 12.0, int(sys.argv[6]) if len(sys.argv) > 6 else 80
SKIP = {"wheel well"}                       # exact cylinders already exist
cut = m.slice_plane(plane_origin=[0, 0, 0], plane_normal=[0, -1, 0])
V, F = trimesh.remesh.subdivide_to_size(cut.vertices, cut.faces, max_edge=EDGE)
V[np.abs(V[:, 1]) < 1e-6, 1] = 0.0
_w = trimesh.Trimesh(V, F, process=False); _w.merge_vertices(); V, F = np.asarray(_w.vertices), np.asarray(_w.faces)
fc = V[F].mean(1)


def edge_of(Q):
    keep = np.r_[True, np.linalg.norm(np.diff(Q, axis=0), axis=1) > 0.3]; Q = Q[keep]
    arr = TColgp_Array1OfPnt(1, len(Q))
    for i, p in enumerate(Q): arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    return BRepBuilderAPI_MakeEdge(GeomAPI_PointsToBSpline(arr, 3, 8).Curve()).Edge()


def loop_of(panel):
    curves = {k: Q for k, Q in NET.items() if panel in k.split("|")[:2]}
    key = lambda p: tuple(np.round(p, 1))
    G = nx.MultiGraph()
    for k, Q in curves.items():
        a, b = key(Q[0]), key(Q[-1])
        if a == b:                                    # a closed curve is its own loop
            G.add_edge(("c", k), ("c", k), k=k); continue
        G.add_edge(a, b, k=k)
    best, bestL = None, 0
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        ks = [d["k"] for _, _, d in sub.edges(data=True)]
        L = sum(np.linalg.norm(np.diff(curves[k], axis=0), axis=1).sum() for k in ks)
        if all(sub.degree(n) % 2 == 0 for n in sub.nodes) and L > bestL:
            best, bestL = ks, L
    return [curves[k] for k in best] if best else None


names = sorted(set(lab)) if ONLY is None else ONLY
comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp); report = {}
for p in names:
    if p in SKIP: continue
    loop = loop_of(p)
    if not loop:
        print("%-26s no closed border loop" % p); report[p] = "no loop"; continue
    mf = BRepOffsetAPI_MakeFilling(3, 15, 2, False, 1e-3, 1e-2, 0.05, 0.1, 8, 9)
    for Q in loop:
        mf.Add(edge_of(Q), GeomAbs_C0)
    fi = np.where(lab == p)[0]
    loopP = np.vstack(loop); far = cKDTree(loopP).query(fc[fi])[0] > 60     # interior only, away from the border
    pts = fc[fi[far]]
    if len(pts):
        sel = pts[np.random.default_rng(0).choice(len(pts), min(N_INT, len(pts)), replace=False)]
        for q in sel: mf.Add(gp_Pnt(*map(float, q)))
    try:
        mf.Build(); ok = mf.IsDone()
    except Exception as e:
        ok = False; print("%-26s fill failed: %s" % (p, e))
    if not ok:
        report[p] = "fill failed"; continue
    face = mf.Shape()
    if not valid(face):
        from OCP.ShapeFix import ShapeFix_Shape
        fx = ShapeFix_Shape(face); fx.SetPrecision(0.01); fx.SetMaxTolerance(0.5); fx.Perform(); face = fx.Shape()
    chk = fc[fi[np.random.default_rng(1).choice(len(fi), min(60, len(fi)), replace=False)]]
    d = []
    for q in chk:
        ds = BRepExtrema_DistShapeShape(face, BRepBuilderAPI_MakeVertex(gp_Pnt(*map(float, q))).Vertex()); ds.Perform(); d.append(ds.Value())
    d = np.array(d)
    report[p] = dict(valid=bool(valid(face)), curves=len(loop), dev_median=float(np.median(d)), dev_p90=float(np.percentile(d, 90)))
    print("%-26s curves %2d  valid %s  STL deviation median %5.1f  p90 %5.1f mm" % (p, len(loop), report[p]["valid"], np.median(d), np.percentile(d, 90)), flush=True)
    bb.Add(comp, face)
BRepTools.Write_s(comp, OUT)
json.dump(report, open(OUT.replace(".brep", "_report.json"), "w"), indent=1)
