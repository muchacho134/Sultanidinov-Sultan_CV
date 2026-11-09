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
SKIP = set()                               # wheel wells are filled from their network borders too
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


def loops_of(curves):
    key = lambda p: tuple(np.round(p, 1))
    G = nx.MultiGraph()
    for k, Q in curves.items():
        a_, b_ = key(Q[0]), key(Q[-1])
        G.add_edge(("c", k) if a_ == b_ else a_, ("c", k) if a_ == b_ else b_, k=k)
    out = []
    for comp in nx.connected_components(G):
        sub = G.subgraph(comp)
        ks = [d["k"] for _, _, d in sub.edges(data=True)]
        if all(sub.degree(n) % 2 == 0 for n in sub.nodes):
            L = sum(np.linalg.norm(np.diff(curves[k], axis=0), axis=1).sum() for k in ks)
            out.append((L, [curves[k] for k in ks]))
    out.sort(key=lambda t: -t[0])
    return [l for _, l in out]


def loop_of(panel, faces_xyz=None):
    allc = {k: Q for k, Q in NET.items() if panel in k.split("|")[:2]}
    curves = allc
    if faces_xyz is not None:                         # only the curves that bound this piece
        tq = cKDTree(faces_xyz)
        curves = {k: Q for k, Q in allc.items() if np.median(tq.query(Q)[0]) < 20}
    L = loops_of(curves)
    if not L or len(L[0]) < 2 and len(allc) > len(curves):
        L = loops_of(allc)                            # retry with every curve of the panel
    if not L: return None, []
    return L[0], L[1:]


from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCP.TColgp import TColgp_HArray1OfPnt2d
from OCP.Geom2dAPI import Geom2dAPI_Interpolate
from OCP.gp import gp_Pnt2d
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire
from OCP.BRepLib import BRepLib
from OCP.ShapeFix import ShapeFix_Face


def add_holes(face, holes):
    """Cut each closed inner loop out of the face (projected onto its surface as a 2D trim)."""
    e = TopExp_Explorer(face, TopAbs_FACE); f0 = TopoDS.Face_s(e.Current())
    S = BRep_Tool.Surface_s(f0)
    mk = BRepBuilderAPI_MakeFace(f0)
    for loop in holes:
        P = np.vstack(loop)
        # order the loop's points by walking the curves end to end
        Q = [loop[0]]; rest = list(loop[1:])
        while rest:
            end = Q[-1][-1]
            j = min(range(len(rest)), key=lambda i: min(np.linalg.norm(rest[i][0] - end), np.linalg.norm(rest[i][-1] - end)))
            r = rest.pop(j); Q.append(r if np.linalg.norm(r[0] - end) <= np.linalg.norm(r[-1] - end) else r[::-1])
        P = np.vstack(Q); P = P[np.r_[True, np.linalg.norm(np.diff(P, axis=0), axis=1) > 2]][::2]
        if len(P) < 6: continue
        uv = []
        for p in P:
            pr = GeomAPI_ProjectPointOnSurf(gp_Pnt(*map(float, p)), S)
            if pr.NbPoints() == 0: break
            u, v = pr.LowerDistanceParameters(); uv.append((u, v))
        if len(uv) != len(P): continue
        h = TColgp_HArray1OfPnt2d(1, len(uv))
        for i, (u, v) in enumerate(uv): h.SetValue(i + 1, gp_Pnt2d(u, v))
        try:
            it = Geom2dAPI_Interpolate(h, True, 1e-6); it.Perform()
            ed = BRepBuilderAPI_MakeEdge(it.Curve(), S).Edge(); BRepLib.BuildCurves3d_s(ed)
            mk.Add(BRepBuilderAPI_MakeWire(ed).Wire())
        except Exception:
            continue
    fx = ShapeFix_Face(mk.Face()); fx.FixOrientation(); fx.Perform()
    return fx.Face()


names = sorted(set(lab)) if ONLY is None else ONLY
comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp); report = {}; retried = {}
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
_m = trimesh.Trimesh(V, F, process=False); adjF = _m.face_adjacency; Af = _m.area_faces
jobs = []
for p in names:
    if p in SKIP: continue
    sel = lab == p; ok_ = sel[adjF[:, 0]] & sel[adjF[:, 1]]
    nc, cc = connected_components(coo_matrix((np.ones(ok_.sum()), (adjF[ok_, 0], adjF[ok_, 1])), shape=(len(F), len(F))), directed=False)
    pieces = [np.where(sel & (cc == k))[0] for k in np.unique(cc[sel])]
    pieces = [q for q in pieces if Af[q].sum() > 0.01e6]
    for k, q in enumerate(sorted(pieces, key=lambda q: -Af[q].sum())):
        jobs.append((p, q, f"{p}" if len(pieces) == 1 else f"{p} #{k + 1}"))
for p, fi_piece, tag in jobs:
    loop, holes = loop_of(p, fc[fi_piece])
    if not loop:
        print("%-26s no closed border loop" % tag); report[tag] = "no loop"; continue
    def fill(n_int, seed=0):
        mf = BRepOffsetAPI_MakeFilling(3, 15, 2, False, 1e-3, 1e-2, 0.05, 0.1, 8, 9)
        for Q in loop:
            mf.Add(edge_of(Q), GeomAbs_C0)
        fi = fi_piece
        loopP = np.vstack(loop); far = cKDTree(loopP).query(fc[fi])[0] > 60
        pts = fc[fi[far]]
        if len(pts):
            sel = pts[np.random.default_rng(seed).choice(len(pts), min(n_int, len(pts)), replace=False)]
            for q in sel: mf.Add(gp_Pnt(*map(float, q)))
        mf.Build()
        return mf
    try:
        mf = fill(N_INT); ok = mf.IsDone()
    except Exception as e:
        ok = False; print("%-26s fill failed: %s" % (tag, e))
    if not ok:
        report[tag] = "fill failed"; continue
    fi = fi_piece
    face = mf.Shape()
    if holes:
        face = add_holes(face, holes)
    if not valid(face):
        from OCP.ShapeFix import ShapeFix_Shape
        fx = ShapeFix_Shape(face); fx.SetPrecision(0.01); fx.SetMaxTolerance(0.5); fx.Perform(); face = fx.Shape()
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    bx = Bnd_Box(); BRepBndLib.AddOptimal_s(face, bx, True, False); x0_, y0_, z0_, x1_, y1_, z1_ = bx.Get()
    if z1_ > 1400 or z0_ < -50 or x0_ < -2400 or x1_ > 2400 or y0_ < -1200 or y1_ > 30:
        print("%-26s rejected: leaves the car envelope" % tag); report[tag] = "out of envelope"; continue
    chk = fc[fi[np.random.default_rng(1).choice(len(fi), min(60, len(fi)), replace=False)]]
    d = []
    for q in chk:
        ds = BRepExtrema_DistShapeShape(face, BRepBuilderAPI_MakeVertex(gp_Pnt(*map(float, q))).Vertex()); ds.Perform(); d.append(ds.Value())
    d = np.array(d)
    if np.median(d) > 15 and not retried.get(tag):
        retried[tag] = True
        try:
            mf2 = fill(4 * N_INT, 7)
            if mf2.IsDone():
                f2 = mf2.Shape(); d2 = []
                for q in chk:
                    ds = BRepExtrema_DistShapeShape(f2, BRepBuilderAPI_MakeVertex(gp_Pnt(*map(float, q))).Vertex()); ds.Perform(); d2.append(ds.Value())
                if np.median(d2) < np.median(d): face, d = f2, np.array(d2)
        except Exception:
            pass
    report[tag] = dict(valid=bool(valid(face)), curves=len(loop), dev_median=float(np.median(d)), dev_p90=float(np.percentile(d, 90)))
    print("%-26s curves %2d  valid %s  STL deviation median %5.1f  p90 %5.1f mm" % (tag, len(loop), report[tag]["valid"], np.median(d), np.percentile(d, 90)), flush=True)
    bb.Add(comp, face)
BRepTools.Write_s(comp, OUT)
json.dump(report, open(OUT.replace(".brep", "_report.json"), "w"), indent=1)
