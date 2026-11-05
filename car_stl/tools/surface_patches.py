"""Surface the dough of the half car with trimmed B-spline height-field patches.

dough  = half-car mesh faces not finished yet and not superseded by the finished faces
patches = seed regions (low curvature, normal cone) grown over the dough, then split until
          every patch is a height field over its own best-fit plane (normal spread < MAX_TILT)
surface = B-spline z(u, v) over that plane, u/v = plane coordinates (GeomAPI_PointsToBSplineSurface
          on a regular grid, smoothed), so the trim curve is drawn directly in (u, v)
"""
import sys, json, numpy as np, trimesh
from collections import deque
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra, connected_components
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from occ_util import valid
from OCP.gp import gp_Pnt, gp_Pnt2d, gp_Ax3, gp_Dir, gp_Trsf
from OCP.TColStd import TColStd_Array2OfReal
from OCP.TColgp import TColgp_Array1OfPnt2d
from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCP.Geom2dAPI import Geom2dAPI_Interpolate
from OCP.TColgp import TColgp_HArray1OfPnt2d
from OCP.GeomAbs import GeomAbs_C2
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCP.BRepLib import BRepLib
from OCP.ShapeFix import ShapeFix_Face
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools

MESH, LABELS, PARTS, OUT = sys.argv[1:5]
MAX_TILT, GRID, SMOOTH = 70.0, 10.0, 1.0          # deg, mm grid step, smoothing (grid cells)
OVERLAP, CENTRE_PUSH = 6.0, 45.0                    # trim overlap with neighbours; push past y=0
m = trimesh.load(MESH, force='mesh'); lab0 = np.load(LABELS); P = json.load(open(PARTS))
F, V, c, n, A = m.faces, m.vertices, m.triangles_center, m.face_normals, m.area_faces

# ---------------------------------------------------------------- dough
dough = (lab0 < 0) & (c[:, 1] <= 5)
for k, zf in (("front", 96.8), ("rear", 114.5)):
    w = P[k]; rw = w["r"] + (12.0 if k == "front" else 8.0)
    near_well = (np.abs(c[:, 0] - w["x"]) < rw + 60) & (c[:, 2] < zf + 45) & (c[:, 1] > -w["y_out"])
    near_cyl = (np.abs(np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"]) - rw) < 30) & (c[:, 1] > -w["wall"] - 40)
    near_slot = (np.abs(c[:, 1] + w["wall"]) < 30) & (np.hypot(c[:, 0] - w["x"], c[:, 2] - w["z"]) < rw + 30)
    dough &= ~(near_well | near_cyl | near_slot)
dough &= ~((c[:, 2] < 145) & (c[:, 1] > -800) & (c[:, 0] > -1880) & (c[:, 0] < 1740) & (n[:, 2] < -0.5))
if len(sys.argv) > 5:          # fill pass: surface only what the first pass left uncovered
    unc = np.zeros(len(V), bool); unc[np.load(sys.argv[5])] = True
    dough = (c[:, 1] <= 5) & (unc[F].sum(1) >= 2)
    # never re-surface the finished faces themselves
    dough &= (lab0 < 0)
print("dough faces %d  area %.2f m2" % (dough.sum(), A[dough].sum() / 1e6))

# ---------------------------------------------------------------- patches
adj = m.face_adjacency; ok = dough[adj[:, 0]] & dough[adj[:, 1]]
a_, b_ = adj[ok, 0], adj[ok, 1]
H = trimesh.curvature.discrete_mean_curvature_measure(m, V, 40.0) / (np.pi * 1600.0)
Hf = np.abs(H[F].mean(1))
nbrs = [[] for _ in range(len(F))]
for x, y in zip(a_, b_):
    nbrs[x].append(y); nbrs[y].append(x)
cos_c = np.cos(np.radians(25)); lab = np.full(len(F), -1); k = 0
for seed in np.argsort(Hf):
    if not dough[seed] or lab[seed] >= 0 or Hf[seed] > 1 / 400.0:
        continue
    lab[seed] = k; nsum = n[seed] * A[seed]; q = deque([seed]); members = [seed]
    while q:
        f = q.popleft()
        for g in nbrs[f]:
            if lab[g] < 0 and Hf[g] < 1 / 400.0:
                mean = nsum / np.linalg.norm(nsum)
                if n[g] @ mean >= cos_c and n[g] @ n[seed] >= cos_c:
                    lab[g] = k; nsum = nsum + n[g] * A[g]; q.append(g); members.append(g)
    if A[members].sum() < 0.015e6:
        lab[members] = -2                       # too small to be a seed region
    else:
        k += 1
lab[lab == -2] = -1
# grow the seeds over the rest of the dough (geodesic)
w_ = np.linalg.norm(c[a_] - c[b_], axis=1)
G = coo_matrix((np.r_[w_, w_], (np.r_[a_, b_], np.r_[b_, a_])), shape=(len(F), len(F))).tocsr()
seeds = np.where(lab >= 0)[0]
dist, _, src = dijkstra(G, indices=seeds, min_only=True, return_predecessors=True)
lab = np.where(dough & np.isfinite(dist), lab[np.maximum(src, 0)], -1)


def tilt(sel):
    nm = (n[sel] * A[sel, None]).sum(0); nm /= np.linalg.norm(nm)
    return np.degrees(np.arccos(np.clip(n[sel] @ nm, -1, 1))).max(), nm


# split patches that are not height fields (2-means on normals, then connected pieces)
queue = list(np.unique(lab[lab >= 0])); nxt = lab.max() + 1; final = []
while queue:
    p = queue.pop()
    sel = np.where(lab == p)[0]
    t, nm = tilt(sel)
    if t <= MAX_TILT or len(sel) < 40:
        final.append(p); continue
    N_ = n[sel]; cen = N_[[np.argmax(N_ @ nm), np.argmin(N_ @ nm)]]
    for _ in range(8):
        asg = np.argmax(N_ @ cen.T, axis=1)
        cen = np.array([N_[asg == j].mean(0) if (asg == j).any() else cen[j] for j in range(2)])
        cen /= np.linalg.norm(cen, axis=1)[:, None]
    for j in range(2):
        part = sel[asg == j]
        if len(part) == 0: continue
        sub = np.isin(adj[:, 0], part) & np.isin(adj[:, 1], part)
        g2 = coo_matrix((np.ones(sub.sum()), (adj[sub, 0], adj[sub, 1])), shape=(len(F), len(F)))
        ncomp, cl = connected_components(g2, directed=False)
        for comp in np.unique(cl[part]):
            piece = part[cl[part] == comp]
            if A[piece].sum() < 3000:            # tiny crumbs: leave to the neighbours later
                lab[piece] = -1; continue
            lab[piece] = nxt; queue.append(nxt); nxt += 1
# re-grow crumbs into neighbours
seeds = np.where(lab >= 0)[0]
dist, _, src = dijkstra(G, indices=seeds, min_only=True, return_predecessors=True)
lab = np.where(dough & np.isfinite(dist), lab[np.maximum(src, 0)], -1)
# merge slivers (< MIN_PATCH m2) into the neighbour they share the most edge with
MIN_PATCH = 0.03e6
for _ in range(5):
    changed = False
    areas = {p: A[lab == p].sum() for p in np.unique(lab[lab >= 0])}
    for p, ar in sorted(areas.items(), key=lambda kv: kv[1]):
        if ar >= MIN_PATCH: continue
        e_ = (lab[adj[:, 0]] == p) ^ (lab[adj[:, 1]] == p)
        other = np.where(lab[adj[e_, 0]] == p, lab[adj[e_, 1]], lab[adj[e_, 0]])
        other = other[other >= 0]
        if len(other):
            lab[lab == p] = np.bincount(other).argmax(); changed = True
    if not changed: break
ids = [p for p in np.unique(lab[lab >= 0])]
print("patches:", len(ids))
np.save(OUT.replace(".brep", "_labels.npy"), lab)

# ---------------------------------------------------------------- fit + trim
comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
report, devs = [], np.full(len(V), np.nan)
for p in ids:
    sel = np.where(lab == p)[0]
    _, nm = tilt(sel)
    ctr = np.average(c[sel], axis=0, weights=A[sel])
    e1 = np.cross(nm, [0, 0, 1.0]) if abs(nm[2]) < 0.9 else np.cross(nm, [1.0, 0, 0])
    e1 /= np.linalg.norm(e1); e2 = np.cross(nm, e1)
    to_loc = lambda X: np.c_[(X - ctr) @ e1, (X - ctr) @ e2, (X - ctr) @ nm]
    # data: the patch's vertices plus a 40 mm overlap ring into the neighbours (continuity)
    vid = np.unique(F[sel])
    ring = np.where(np.min(np.linalg.norm(V[:, None, :] - V[vid][None, ::7, :], axis=2), axis=1) < 40)[0] \
        if len(vid) < 4000 else vid
    L = to_loc(V[np.union1d(vid, ring)])
    L = L[np.abs(L[:, 2]) < 400]
    # boundary loop (outer) of the patch
    sub = m.submesh([sel], append=True)
    loops = [q for q in sub.outline().discrete if len(q) > 3]
    outer = max(loops, key=lambda q: np.ptp(q[:, 0]) + np.ptp(q[:, 1]) + np.ptp(q[:, 2]))
    B = to_loc(outer)[:, :2]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))]
    tt = np.linspace(0, s[-1], max(int(s[-1] / 25), 12), endpoint=False)
    B = np.c_[[gaussian_filter1d(np.interp(tt, s, B[:, j]), 1.5, mode='wrap') for j in range(2)]].T
    # boundary points on the centreline: push them past y = 0 (cut back exactly to y = 0 below)
    W3 = ctr + np.outer(B[:, 0], e1) + np.outer(B[:, 1], e2)
    on_c = W3[:, 1] > -25.0
    gy = np.hypot(e1[1], e2[1])                      # how much y the patch plane carries
    on_c = on_c & (gy > 0.4)
    if on_c.any():
        B[on_c] += CENTRE_PUSH * np.array([e1[1], e2[1]]) / gy ** 2
    # small overlap with the neighbours so no cracks show between patches
    from shapely.geometry import Polygon as _Poly
    pg = _Poly(B).buffer(0).buffer(OVERLAP, join_style=1)
    if pg.geom_type != "Polygon":
        pg = max(pg.geoms, key=lambda g: g.area)
    if on_c.any():
        # clip at the centreline in (u, v): world y = ctr.y + u*e1.y + v*e2.y + z*n.y; z ~ mean height
        from shapely.geometry import Polygon as _P2
        zbar = float(np.median(L[:, 2]))
        a_, b_, c_ = e1[1], e2[1], -(ctr[1] + zbar * nm[1])        # keep a*u + b*v <= c
        g = np.array([a_, b_]) / gy; d0 = c_ / gy                   # unit normal + offset
        t_ = np.array([-g[1], g[0]]); Rr = 1e5
        hp = _P2([g * d0 + t_ * Rr, g * d0 - t_ * Rr, g * d0 - t_ * Rr - g * Rr, g * d0 + t_ * Rr - g * Rr])
        pg = pg.intersection(hp).buffer(0)
        if pg.geom_type != "Polygon":
            pg = max(pg.geoms, key=lambda q: q.area)
    B = np.array(pg.exterior.coords)[:-1]
    s2 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.r_[B, B[:1]], axis=0), axis=1))]
    tt = np.linspace(0, s2[-1], max(int(s2[-1] / 20), 12), endpoint=False)
    BB = np.r_[B, B[:1]]
    B = np.c_[[np.interp(tt, s2, BB[:, j]) for j in range(2)]].T
    # height grid over the boundary box (+margin), smoothed
    lo, hi = B.min(0) - 3 * GRID, B.max(0) + 3 * GRID
    nu, nv = int(np.ceil((hi[0] - lo[0]) / GRID)) + 1, int(np.ceil((hi[1] - lo[1]) / GRID)) + 1
    gu, gv = np.meshgrid(lo[0] + GRID * np.arange(nu), lo[1] + GRID * np.arange(nv), indexing='ij')
    Z = griddata(L[:, :2], L[:, 2], (gu, gv), method='linear')
    Zn = griddata(L[:, :2], L[:, 2], (gu, gv), method='nearest')
    Z = np.where(np.isnan(Z), Zn, Z)
    Z = gaussian_filter(Z, SMOOTH, mode='nearest')
    arr = TColStd_Array2OfReal(1, nu, 1, nv)
    for i in range(nu):
        for j in range(nv):
            arr.SetValue(i + 1, j + 1, float(Z[i, j]))
    api = GeomAPI_PointsToBSplineSurface()
    api.Init(arr, float(lo[0]), float(GRID), float(lo[1]), float(GRID), 3, 3, GeomAbs_C2, 0.3)
    srf = api.Surface()
    # trim curve in (u, v) = plane coordinates
    h = TColgp_HArray1OfPnt2d(1, len(B))
    for i, (u, v) in enumerate(B):
        h.SetValue(i + 1, gp_Pnt2d(float(u), float(v)))
    it = Geom2dAPI_Interpolate(h, True, 1e-6); it.Perform()
    e = BRepBuilderAPI_MakeEdge(it.Curve(), srf).Edge()
    BRepLib.BuildCurves3d_s(e)
    face = BRepBuilderAPI_MakeFace(srf, BRepBuilderAPI_MakeWire(e).Wire(), True).Face()
    fx = ShapeFix_Face(face); fx.Perform(); face = fx.Face()
    # local -> world
    T = gp_Trsf(); T.SetTransformation(gp_Ax3(gp_Pnt(*ctr), gp_Dir(*nm), gp_Dir(*e1)), gp_Ax3())
    face = TopoDS.Face_s(BRepBuilderAPI_Transform(face, T, True).Shape())
    # deviation of the patch's own vertices to the fitted height field
    Lv = to_loc(V[vid])
    zfit = srf
    d = np.array([Lv[i, 2] - srf.Value(float(Lv[i, 0]), float(Lv[i, 1])).Z() for i in range(len(Lv))])
    devs[vid] = np.abs(d)
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    bx = Bnd_Box(); BRepBndLib.AddOptimal_s(face, bx, True, False); x0_, y0_, z0_, x1_, y1_, z1_ = bx.Get()
    if not (x0_ > -2500 and x1_ < 2500 and y0_ > -1300 and y1_ < 25 and z0_ > -100 and z1_ < 1500):
        print("patch %d: exploded bbox %s -> skipped" % (p, [round(v) for v in bx.Get()]))
        continue
    ok_ = valid(face)
    report.append(dict(patch=int(p), faces=int(len(sel)), area_m2=float(A[sel].sum() / 1e6), tilt=float(tilt(sel)[0]),
                       dev_p50=float(np.percentile(np.abs(d), 50)), dev_p95=float(np.percentile(np.abs(d), 95)),
                       dev_max=float(np.abs(d).max()), valid=bool(ok_)))
    bb.Add(comp, face)
BRepTools.Write_s(comp, OUT)
np.save(OUT.replace(".brep", "_dev.npy"), devs)
json.dump(report, open(OUT.replace(".brep", "_report.json"), "w"), indent=1)
tot = sum(r["area_m2"] for r in report)
print("patch  area   tilt  dev p50  p95   max  valid")
for r in sorted(report, key=lambda r: -r["area_m2"]):
    print("%4d  %5.2f  %4.0f   %5.1f %5.1f %6.1f  %s" % (r["patch"], r["area_m2"], r["tilt"], r["dev_p50"], r["dev_p95"], r["dev_max"], r["valid"]))
print("surfaced %.2f m2 in %d patches; all valid: %s" % (tot, len(report), all(r["valid"] for r in report)))
