"""Generic closing of open shells: every free boundary loop is patched (a planar
face when the loop is flat, an n-sided smooth filling otherwise), the patches
are sewn in and the result is made a solid."""
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeFace
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.BRepLib import BRepLib_FindSurface
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shape
from OCP.GeomAbs import GeomAbs_C0
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_SHELL, TopAbs_SOLID, TopAbs_FACE
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp


def free_loops(s, tol=1e-3):
    fb = ShapeAnalysis_FreeBounds(s, tol, False, False)
    out = []
    for comp in (fb.GetClosedWires(), fb.GetOpenWires()):
        e = TopExp_Explorer(comp, TopAbs_WIRE)
        while e.More(): out.append(TopoDS.Wire_s(e.Current())); e.Next()
    return out


def patch(wire):
    fs = BRepLib_FindSurface(wire, 1e-4, True)          # flat loop -> exact planar face
    if fs.Found():
        mf = BRepBuilderAPI_MakeFace(wire, True)
        if mf.IsDone(): return mf.Face(), 'plane'
    mf = BRepOffsetAPI_MakeFilling()
    e = TopExp_Explorer(wire, TopAbs_EDGE)
    while e.More(): mf.Add(TopoDS.Edge_s(e.Current()), GeomAbs_C0); e.Next()
    mf.Build()
    return mf.Shape(), 'filling'


def close(s, tol=1e-3, extra=(), exact=True, exact_only=False, fill_rest=False):
    """returns (solid or None, report)"""
    loops = free_loops(s, tol)
    sw = BRepBuilderAPI_Sewing(tol); sw.Add(s)
    for x in extra: sw.Add(x)
    kinds = []
    for w in loops:
        fs = planar_closure_split(w, fill_rest=fill_rest) if exact else None
        if fs:
            kinds.append('plane'); [sw.Add(f) for f in fs]
        elif exact_only:
            return None, dict(loops=len(loops), unresolved='loop not made of 1-2 flat pieces')
        else:
            f, kind = patch(w); kinds.append(kind); sw.Add(f)
    sw.Perform()
    r = sw.SewedShape()
    rep = dict(loops=len(loops), planes=kinds.count('plane'), fillings=kinds.count('filling'), free_edges=sw.NbFreeEdges())
    if sw.NbFreeEdges():
        return None, rep
    shells = []
    e = TopExp_Explorer(r, TopAbs_SHELL)
    while e.More(): shells.append(TopoDS.Shell_s(e.Current())); e.Next()
    ms = BRepBuilderAPI_MakeSolid()
    for sh in shells: ms.Add(sh)
    fx = ShapeFix_Solid(ms.Solid()); fx.Perform()
    so = fx.Solid()
    rep.update(shells=len(shells), **check(so))
    return so, rep


def check(so):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(so, p)
    bop_ok = BRepAlgoAPI_Check(so, True, True).IsValid()     # small edges + self-intersection
    return dict(valid=BRepCheck_Analyzer(so).IsValid(), bop_ok=bop_ok, volume=round(p.Mass(), 1))


# ---------------------------------------------------------------------------
# exact closing of loops made of flat pieces: assign every loop edge to a plane
# it lies in, then close each plane's chain(s) along the line it shares with the
# neighbouring plane(s).
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line, GeomAbs_Circle
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCP.gp import gp_Pnt, gp_Pln, gp_Dir
import itertools


def _pts(edge, n=6):
    c = BRepAdaptor_Curve(edge); u0, u1 = c.FirstParameter(), c.LastParameter()
    return [c.Value(u0 + (u1 - u0) * i / n) for i in range(n + 1)]


def _on_plane(pts, pl, tol=1e-3):
    (o, d) = pl
    return all(abs((p.X() - o[0]) * d[0] + (p.Y() - o[1]) * d[1] + (p.Z() - o[2]) * d[2]) < tol for p in pts)


def _planes_for(edge):
    """candidate planes (origin, unit normal) containing the edge"""
    c = BRepAdaptor_Curve(edge); pts = _pts(edge)
    cands = []
    if c.GetType() == GeomAbs_Circle:
        ax = c.Circle().Axis(); l = ax.Location(); d = ax.Direction()
        cands.append(((l.X(), l.Y(), l.Z()), (d.X(), d.Y(), d.Z())))
    for i in range(3):                                   # axis-aligned planes
        v = [p.Coord(i + 1) for p in pts]
        if max(v) - min(v) < 1e-4:
            o = [0, 0, 0]; o[i] = v[0]; d = [0, 0, 0]; d[i] = 1
            cands.append((tuple(o), tuple(d)))
    if c.GetType() == GeomAbs_Line:                      # 45-deg planes containing the line
        for i, j in ((0, 1), (0, 2), (1, 2)):
            for s in (1, -1):
                d = [0, 0, 0]; d[i] = 2 ** -0.5; d[j] = s * 2 ** -0.5
                p0 = pts[0]
                pl = ((p0.X(), p0.Y(), p0.Z()), tuple(d))
                if _on_plane(pts, pl): cands.append(pl)
    out = []
    for pl in cands:
        if _on_plane(pts, pl) and not any(_same_plane(pl, q) for q in out): out.append(pl)
    return out


def _same_plane(a, b):
    (o1, d1), (o2, d2) = a, b
    dot = sum(x * y for x, y in zip(d1, d2))
    if abs(abs(dot) - 1) > 1e-6: return False
    return abs(sum((o2[k] - o1[k]) * d1[k] for k in range(3))) < 1e-3


def _plane_isect_point(p1, p2, p3):
    import numpy as np
    A = np.array([p[1] for p in (p1, p2, p3)], float)
    b = np.array([sum(o * d for o, d in zip(p[0], p[1])) for p in (p1, p2, p3)], float)
    if abs(np.linalg.det(A)) < 1e-9: return None
    x = np.linalg.solve(A, b); return gp_Pnt(*x)


def planar_closure(wire):
    """faces closing a loop made of flat pieces (any number of planes), or None.

    Every loop edge is assigned to a plane it lies in (fewest plane switches
    along the loop).  Where the loop switches from plane P to Q the missing
    faces share an edge along P^Q: it runs to the other switch point on the
    same line, or to the corner where three planes meet."""
    from OCP.TopExp import TopExp
    from OCP.BRep import BRep_Tool
    from OCP.TopTools import TopTools_HSequenceOfShape
    edges = []
    we = BRepTools_WireExplorer(wire)
    while we.More():
        edges.append(TopoDS.Edge_s(we.Current())); we.Next()
    n = len(edges)
    cands = [_planes_for(e) for e in edges]
    if any(not c for c in cands): return None
    planes = []
    for c in cands:
        for pl in c:
            if not any(_same_plane(pl, q) for q in planes): planes.append(pl)
    pid = lambda pl: next(i for i, q in enumerate(planes) if _same_plane(pl, q))
    opts = [sorted({pid(pl) for pl in c}) for c in cands]
    # cyclic DP: minimise number of plane switches (small penalty for 45-deg planes)
    obl = lambda p: 0.0 if max(abs(x) for x in planes[p][1]) > 0.99 else 0.01
    best = None
    for p0 in opts[0]:
        cost = {p0: (obl(p0), [p0])}
        for i in range(1, n):
            nc = {}
            for p in opts[i]:
                cand = [(c + (q != p) + obl(p), path + [p]) for q, (c, path) in cost.items()]
                nc[p] = min(cand, key=lambda x: x[0])
            cost = nc
        for p, (c, path) in cost.items():
            c += (p != p0)
            if best is None or c < best[0]: best = (c, path)
    assign = best[1]
    used = sorted(set(assign))
    if len(used) == 1:
        mf = BRepBuilderAPI_MakeFace(wire, True)
        return [mf.Face()] if mf.IsDone() else None
    if len(used) > 12: return None
    vstart = [BRep_Tool.Pnt_s(TopExp.FirstVertex_s(e, True)) for e in edges]
    # switch vertices: start of edge i where assign[i] != assign[i-1]
    switches = [(vstart[i], frozenset((assign[i - 1], assign[i]))) for i in range(n) if assign[i] != assign[i - 1]]
    bypair = {}
    for v, pr in switches: bypair.setdefault(pr, []).append(v)
    internal = {p: [] for p in used}

    def seg(a, b, pr):
        if a.Distance(b) < 1e-6: return
        e = BRepBuilderAPI_MakeEdge(a, b).Edge()
        for p in pr: internal[p].append(e)

    single = {}
    for pr, vs in bypair.items():
        if len(vs) % 2 == 0:
            p, q = tuple(pr); d = [planes[p][1][1] * planes[q][1][2] - planes[p][1][2] * planes[q][1][1],
                                   planes[p][1][2] * planes[q][1][0] - planes[p][1][0] * planes[q][1][2],
                                   planes[p][1][0] * planes[q][1][1] - planes[p][1][1] * planes[q][1][0]]
            vs = sorted(vs, key=lambda v: v.X() * d[0] + v.Y() * d[1] + v.Z() * d[2])
            for k in range(0, len(vs), 2): seg(vs[k], vs[k + 1], pr)
        elif len(vs) == 1:
            single[pr] = vs[0]
        else:
            return None
    # corners: three single pairs over three planes meet at the planes' common point
    while single:
        pr = next(iter(single)); p, q = tuple(pr)
        found = False
        for r in used:
            if r in pr: continue
            pq, qr, pr_ = pr, frozenset((q, r)), frozenset((p, r))
            if qr in single and pr_ in single:
                o = _plane_isect_point(planes[p], planes[q], planes[r])
                if o is None: return None
                for kk in (pq, qr, pr_): seg(single.pop(kk), o, kk)
                found = True; break
        if not found: return None
    faces = []
    from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds as _FB
    for p in used:
        seq = TopTools_HSequenceOfShape()
        for i in range(n):
            if assign[i] == p: seq.Append(edges[i])
        for e in internal[p]: seq.Append(e)
        out = TopTools_HSequenceOfShape()
        _FB.ConnectEdgesToWires_s(seq, 1e-4, False, out)
        o, d = planes[p]
        for k in range(1, out.Length() + 1):              # one face per closed wire on this plane
            w = TopoDS.Wire_s(out.Value(k))
            if not BRep_Tool.IsClosed_s(w): return None
            mf = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(*o), gp_Dir(*d)), w, True)
            if not mf.IsDone(): return None
            from OCP.ShapeFix import ShapeFix_Face
            sf = ShapeFix_Face(mf.Face()); sf.Perform()
            faces.append(TopoDS.Face_s(sf.Face()))
    return faces


def _loop_from(edges, chord_from, chord_to):
    w = BRepBuilderAPI_MakeWire()
    for e in edges: w.Add(e)
    if chord_from.Distance(chord_to) > 1e-6:
        w.Add(BRepBuilderAPI_MakeEdge(chord_from, chord_to).Edge())
    return w.Wire() if w.IsDone() else None


def planar_closure_split(wire, depth=2, max_chord=12.0, fill_rest=False):
    """planar_closure, else split the loop with a short straight chord into two
    loops that each close with flat faces (fill_rest: the second loop may be
    closed with a smooth filling instead)."""
    fs = planar_closure(wire)
    if fs or depth == 0:
        if not fs and fill_rest:
            return triangulated_closure(wire)
        return fs
    from OCP.TopExp import TopExp
    from OCP.BRep import BRep_Tool
    edges = []
    we = BRepTools_WireExplorer(wire)
    while we.More(): edges.append(TopoDS.Edge_s(we.Current())); we.Next()
    n = len(edges)
    vs = [BRep_Tool.Pnt_s(TopExp.FirstVertex_s(e, True)) for e in edges]
    pairs = []
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1: continue
            d = vs[i].Distance(vs[j])
            if 1e-6 < d < max_chord:
                dv = [abs(vs[i].Coord(k + 1) - vs[j].Coord(k + 1)) for k in range(3)]
                if sorted(dv)[1] < 1e-4:            # axis-aligned chord
                    pairs.append((d, i, j))
    for d, i, j in sorted(pairs):
        w1 = _loop_from(edges[i:j], vs[j], vs[i])
        w2 = _loop_from(edges[j:] + edges[:i], vs[i], vs[j])
        if w1 is None or w2 is None: continue
        f1 = planar_closure(w1)
        if not f1: continue
        f2 = planar_closure_split(w2, depth - 1, max_chord)
        if f2: return f1 + f2
        if fill_rest:
            t = triangulated_closure(w2)
            if t: return f1 + t
    if fill_rest:
        return triangulated_closure(wire)
    return None


def triangulated_closure(wire):
    """minimum-area triangulation of a loop whose edges are all straight;
    every triangle becomes a flat face (exact, no bulging)."""
    import numpy as np
    from OCP.TopExp import TopExp
    from OCP.BRep import BRep_Tool
    edges = []
    we = BRepTools_WireExplorer(wire)
    while we.More(): edges.append(TopoDS.Edge_s(we.Current())); we.Next()
    if any(BRepAdaptor_Curve(e).GetType() != GeomAbs_Line for e in edges): return None
    P = [BRep_Tool.Pnt_s(TopExp.FirstVertex_s(e, True)) for e in edges]
    n = len(P)
    if n < 3: return None
    X = np.array([[p.X(), p.Y(), p.Z()] for p in P])
    def area(i, j, k):
        return 0.5 * np.linalg.norm(np.cross(X[j] - X[i], X[k] - X[i]))
    INF = float('inf')
    W = [[0.0] * n for _ in range(n)]; K = [[-1] * n for _ in range(n)]
    for d in range(2, n):
        for i in range(0, n - d):
            j = i + d; best = INF; bk = -1
            for k in range(i + 1, j):
                a = area(i, k, j)
                if a < 1e-9: continue                      # skip degenerate triangles
                c = W[i][k] + W[k][j] + a
                if c < best: best, bk = c, k
            W[i][j] = best; K[i][j] = bk
    if K[0][n - 1] < 0 or W[0][n - 1] == INF: return None
    tris = []
    def collect(i, j):
        if j - i < 2: return
        k = K[i][j]; tris.append((i, k, j)); collect(i, k); collect(k, j)
    collect(0, n - 1)
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
    faces = []
    for i, k, j in tris:
        pg = BRepBuilderAPI_MakePolygon(P[i], P[k], P[j], True)
        mf = BRepBuilderAPI_MakeFace(pg.Wire(), True)
        if not mf.IsDone(): return None
        faces.append(mf.Face())
    return faces


def drop_faces(shape, box, tol=1e-6):
    """shell without the faces whose bounding box lies inside box (x0,y0,z0,x1,y1,z1)"""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Shell
    b = BRep_Builder(); sh = TopoDS_Shell(); b.MakeShell(sh); n = 0
    e = TopExp_Explorer(shape, TopAbs_FACE)
    while e.More():
        bb = Bnd_Box(); BRepBndLib.Add_s(e.Current(), bb); x = bb.Get()
        inside = all(x[i] >= box[i] - tol for i in range(3)) and all(x[i + 3] <= box[i + 3] + tol for i in range(3))
        if inside: n += 1
        else: b.Add(sh, e.Current())
        e.Next()
    return sh, n
