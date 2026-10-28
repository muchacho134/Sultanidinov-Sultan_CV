"""Refined body from the AI GLB: the intersection of five cleaned, smoothed orthographic depth maps
(front, rear, top, bottom, side). Each surface is taken from the view that sees it head-on; where a
view only grazes the surface its constraint is dropped. The implicit field is contoured with
marching cubes, giving a smooth closed surface."""
import sys, numpy as np, trimesh
from scipy import ndimage
from skimage import measure
sys.path.insert(0, '.')
from depthmap import depth_map

L = 5360.0
P = 4.0                                   # map + field resolution, mm
WHEELS = (903.0, 4155.0); R_WHEEL = 362.0; ZW = 366.0
MIRROR_X = (1880.0, 2240.0)

def strip_mesh(m):
    """Drop the GLB mirror heads (only what sticks out beyond the door skin). The wheels stay in
    while the hull is built so the arches have no slits; clean wells are cut afterwards."""
    c = m.triangles_center
    mirror = (np.abs(c[:, 1]) > 935) & (c[:, 2] > 990) & (c[:, 2] < 1290) & (c[:, 0] > MIRROR_X[0] - 30) & (c[:, 0] < MIRROR_X[1] + 30)
    return trimesh.Trimesh(m.vertices, m.faces[~mirror], process=False)

def permuted(m, order, flip=None):
    v = m.vertices[:, order].copy()
    return trimesh.Trimesh(v, m.faces, process=False)

def nsmooth(F, valid, sigma):
    w = valid.astype(float)
    num = ndimage.gaussian_filter(np.where(valid, F, 0.0), sigma)
    den = ndimage.gaussian_filter(w, sigma)
    return np.where(valid, num / np.maximum(den, 1e-6), np.nan)

def inpaint(F, mask, valid, iters=3000):
    G = np.where(valid & ~mask, F, 0.0)
    G[mask] = np.nanmean(F[valid & ~mask])
    w = valid.astype(float)
    nb = lambda A: np.roll(A, 1, 0) + np.roll(A, -1, 0) + np.roll(A, 1, 1) + np.roll(A, -1, 1)
    cnt = np.maximum(nb(w), 1)
    for _ in range(iters):
        G[mask] = (nb(G * w) / cnt)[mask]
    return G

def grazing(D, limit=2.5):
    """Cells where the view only grazes the surface. Gradients are taken from real surface cells
    only, so silhouette edges (next to misses) keep their constraint."""
    gz, gy = np.gradient(D, P)                    # nan next to misses
    g = np.hypot(gz, gy)
    return np.isfinite(g) & (g > limit)

def symmetric(D, axis):
    """Average a map with its mirror image across y = 0 (misses stay misses only if both are)."""
    M = np.flip(D, axis)
    return np.where(np.isfinite(D) & np.isfinite(M), 0.5 * (D + M), np.fmax(D, M))

def end_face(D, ys, zs, front):
    """Front / rear map: erase grille block, mascot, lamp holes, plate recess, exhaust pockets."""
    Y, Z = np.meshgrid(ys, zs)
    face = np.isfinite(D) & (D < 700)
    filled = ndimage.binary_fill_holes(face)
    holes = filled & ~face
    F = np.where(face, D, np.nan)
    if front:
        box = (np.abs(Y) < 600) & (Z > 250) & (Z < 960) & face
        Fm = ndimage.minimum_filter(np.where(face, D, 1e5), size=(5, 15))
        F = np.where(box & (Fm < 1e4), Fm, F)
    col = (np.abs(Y) < 100) & (Z > (930 if front else 960)) & filled
    for i in np.nonzero(col.any(1))[0]:
        row = F[i]; jl = np.searchsorted(ys, -110); jr = np.searchsorted(ys, 110)
        if np.isfinite(row[jl]) and np.isfinite(row[jr]):
            sel = np.nonzero(col[i])[0]; row[sel] = np.interp(ys[sel], [-110, 110], [row[jl], row[jr]])
    base = nsmooth(np.nan_to_num(F, nan=0.0), np.isfinite(F) & filled, 12)
    det = (np.abs(np.nan_to_num(F - base, nan=0.0)) > 6) & (np.abs(Y) < 850) & (Z > 210) & (Z < 1000) & filled
    G = inpaint(np.nan_to_num(F, nan=0.0), (holes | det) & filled, filled)
    G = nsmooth(G, filled, 5)
    out = D.copy()
    out[filled] = G[filled]
    return out

def maps(mesh):
    m = strip_mesh(mesh)
    res = {}
    # front / rear: grid (y, z), depth along X
    ys, zs, Df, Nf = depth_map(m, 1, (-1000, 1000), (0, 1600), P, 0.0, True)
    _, _, Dr, Nr = depth_map(m, -1, (-1000, 1000), (0, 1600), P, L, True)
    Df, Dr = symmetric(Df, 1), symmetric(Dr, 1)
    res['NF'], res['NG'] = symmetric(Nf, 1), symmetric(Nr, 1)
    res['F'] = (ys, zs, end_face(Df, ys, zs, True))
    res['G'] = (ys, zs, end_face(Dr, ys, zs, False))
    # top / bottom: grid (x, y), depth along Z  (permute so the depth axis is first)
    mt = permuted(m, [2, 0, 1])                     # columns: z, x, y
    xs, ys2, Dt, Nt = depth_map(mt, -1, (0, L), (-1000, 1000), P, 1800.0, True)
    _, _, Db, Nb = depth_map(mt, 1, (0, L), (-1000, 1000), P, -200.0, True)
    res['NH'], res['NB'] = symmetric(Nt, 0), symmetric(Nb, 0)
    res['H'] = (xs, ys2, symmetric(1800.0 - Dt, 0))   # top surface height, rows = y, cols = x
    res['B'] = (xs, ys2, symmetric(Db - 200.0, 0))    # bottom surface height
    # side: grid (x, z), depth along Y from both sides, symmetrised
    ms = permuted(m, [1, 0, 2])                     # columns: y, x, z
    xs3, zs3, Dl, Nl = depth_map(ms, 1, (0, L), (0, 1600), P, -1200.0, True)
    _, _, Dr2, Nr2 = depth_map(ms, -1, (0, L), (0, 1600), P, 1200.0, True)
    res['NS'] = np.fmin(Nl, Nr2)
    left = 1200.0 - Dl; right = 1200.0 - Dr2
    res['S'] = (xs3, zs3, np.where(np.isfinite(left) & np.isfinite(right), 0.5 * (left + right), np.fmax(left, right)))
    return res

def slope_info(D):
    """Per-cell surface slope seen by this view (mm depth per mm), from the gentler of the two
    neighbours on each axis so a single depth step does not count as grazing."""
    def axis_slope(ax):
        f = (np.roll(D, -1, ax) - D) / P
        b = (D - np.roll(D, 1, ax)) / P
        # a step (silhouette / discontinuity) is steep on one side only; a grazing ramp on both
        return np.nanmin(np.abs(np.stack([f, b])), 0)          # gentler side of the cell
    s = np.hypot(np.nan_to_num(axis_slope(0), nan=0.0), np.nan_to_num(axis_slope(1), nan=0.0))
    return np.where(np.isfinite(D), s, np.nan)

def slack_from(s):
    return np.minimum(3.0 * np.nan_to_num(s, nan=0.0), 8.0)

FILL = np.hypot(*np.mgrid[-12:13, -12:13]) <= 12.5        # 100 mm disc: fills any dip narrower than that

def fill_down(D, valid):
    """Depth map (bigger = further from the viewer): remove narrow deep pits (grey opening)."""
    Dn = np.where(valid, D, 1e5)
    return np.where(valid, np.minimum(D, ndimage.grey_opening(Dn, footprint=FILL)), np.nan)

def fill_up(D, valid):
    """Height map (bigger = toward the viewer): fill narrow dips (grey closing)."""
    Dn = np.where(valid, D, -1e4)
    return np.where(valid, np.maximum(D, ndimage.grey_closing(Dn, footprint=FILL)), np.nan)

# grille / hood blend (world coordinates; matches glb_features: SY, zf(), XG)
XG = 4.0; X_HOOD = 420.0; SY = 0.976
def zf(z): return 168.0 + (z - 120.0) * (920.0 - 168.0) / (965.0 - 120.0)
def grille_top(y):
    yc = np.clip(np.abs(y) / SY, 0, 545.0)
    return zf(965.0 - 25.0 * (yc / 545.0) ** 2)
def blend_weight(y):
    t = np.clip((np.abs(y) - 520.0) / 120.0, 0, 1)
    return 1 - t * t * (3 - 2 * t)

WHEEL_HALF = 470.0                                        # bridge x in [xc - 470, xc + 470]
def bridge_wheels(D, xs, rows, raise_only=True):
    """Across each wheel zone, replace the map by a straight bridge between the values just ahead of
    and behind the wheel (only raising it), so fenders, sides and floor run solid over the arches;
    clean round wells are cut out afterwards."""
    D = D.copy()
    for xc in WHEELS:
        ia, ib = np.searchsorted(xs, xc - WHEEL_HALF), np.searchsorted(xs, xc + WHEEL_HALF)
        for r in np.nonzero(rows)[0]:
            lo, hi = D[r, ia - 1], D[r, ib + 1]
            if not (np.isfinite(lo) and np.isfinite(hi)):
                continue
            line = np.linspace(lo, hi, ib - ia + 1)
            seg = D[r, ia:ib + 1]
            D[r, ia:ib + 1] = np.fmax(np.nan_to_num(seg, nan=-1e4), line) if raise_only else line
    return D

def clean_maps(res):
    out = {}
    for k in ('F', 'G'):
        a, b, D = res[k]
        D = fill_down(D, np.isfinite(D))                         # lower-front slot, deck-lid slot, panel ripple
        s = slope_info(D)
        g = np.nan_to_num(s, nan=0.0) > 2.5
        Dc = np.where(g, -1e5, D - slack_from(s))
        if k == 'F':
            Y, Z = np.meshgrid(a, b)
            # above the grille top the hood / cowl / screen come from the top view only
            Dc = np.where((np.abs(Y) < 800) & (Z > grille_top(Y)), -1e5, Dc)
            # grille area: solid right up to the grille front plane (the vane pocket is cut later),
            # receding gently past the grille corners, so there is no slot under the hood blend
            ay = np.abs(Y)
            core = (ay <= 532) & (Z >= zf(340.0)) & (Z <= grille_top(Y))
            edge = (ay > 532) & (ay < 650) & (Z >= grille_top(Y) - 160) & (Z <= grille_top(Y))
            Dc = np.where(core, np.minimum(np.where(Dc < -1e4, 1e5, Dc), XG), Dc)
            Dc = np.where(edge, np.minimum(np.where(Dc < -1e4, 1e5, Dc), XG + 2.5 * (ay - 532)), Dc)
        out[k] = (a, b, Dc)
        out[k + '_miss'] = ~np.isfinite(D)
    out['H_raw'] = res['H'][2].copy(); out['S_raw'] = res['S'][2].copy()
    for k in ('H', 'B', 'S'):
        a, b, D = res[k]
        D = D.copy()
        valid = np.isfinite(D)
        if k in ('H', 'S'):
            # drop thin spikes (mascot, antenna, handles), then fill narrow pits
            Dn = np.where(valid, D, -1e4)
            Do = ndimage.grey_opening(Dn, size=(15, 15))
            D = np.where(valid & (Do > -1e3), np.minimum(D, Do), np.nan)
            D = fill_up(D, np.isfinite(D))
            valid = np.isfinite(D)
        if k == 'H':
            # cowl trench at the screen base: bridge straight from the hood to the screen
            ia, ib = np.searchsorted(a, 1440.0), np.searchsorted(a, 1700.0)
            rows = np.nonzero(np.abs(b) < 780)[0]
            for r in rows:
                lo, hi = D[r, ia], D[r, ib]
                if np.isfinite(lo) and np.isfinite(hi):
                    D[r, ia:ib + 1] = np.fmax(D[r, ia:ib + 1], np.linspace(lo, hi, ib - ia + 1))
            valid = np.isfinite(D)
        if k == 'H':
            D = bridge_wheels(D, a, np.abs(b) > 540)                  # fender tops over the arches
        elif k == 'S':
            D = bridge_wheels(D, a, (b > 120) & (b < 960))            # body sides over the arches
        elif k == 'B':
            # floor under the wheel zones: lift the bottom limit to the floor line ahead of / behind the wheel
            D = bridge_wheels(D, a, np.abs(b) > 540)
        valid = np.isfinite(D)
        if k in ('H', 'S'):
            raw = out[k + '_raw']
            out[k + '_raw'] = np.where(np.isfinite(D), np.fmax(np.nan_to_num(raw, nan=-1e4), D), raw)
        Ds = nsmooth(np.nan_to_num(D, nan=0.0), valid, {'H': 6, 'B': 4, 'S': 4}[k])
        s = slope_info(Ds)
        sgn = -1.0 if k == 'B' else 1.0                       # H, S are upper bounds; B is a lower bound
        out[k] = (a, b, Ds + sgn * slack_from(s))
        out[k + '_graze'] = np.nan_to_num(s, nan=0.0) > 2.5
        if k == 'H':
            out['H_smooth'] = Ds
    # ---- grille top -> hood: Hermite blend from the grille top edge to the hood at X_HOOD ----
    xs, ys2, H = out['H']; Hs = out['H_smooth']
    j0, j1 = np.searchsorted(xs, XG), np.searchsorted(xs, X_HOOD)
    xx = xs[j0:j1 + 1]
    Hb = H.copy(); Hr = out['H_raw']
    t = (xx - xx[0]) / (xx[-1] - xx[0])
    h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
    span = xx[-1] - xx[0]
    for r, y in enumerate(ys2):
        w = blend_weight(y)
        if w <= 0 or not np.isfinite(Hs[r, j1]):
            continue
        z0, z1 = grille_top(y), Hs[r, j1]
        s1 = (Hs[r, j1 + 3] - Hs[r, j1 - 3]) / (xs[j1 + 3] - xs[j1 - 3])
        curve = h00 * z0 + h10 * span * 0.25 + h01 * z1 + h11 * span * s1
        cur = np.where(np.isfinite(Hb[r, j0:j1 + 1]), Hb[r, j0:j1 + 1], curve)
        Hb[r, j0:j1 + 1] = (1 - w) * cur + w * curve
        out['H_graze'][r, j0:j1 + 1] &= w < 0.5
        Hr[r, j0:j1 + 1] = np.fmax(np.nan_to_num(Hr[r, j0:j1 + 1], nan=-1e4), Hb[r, j0:j1 + 1])
    out['H'] = (xs, ys2, Hb); out['H_raw'] = Hr
    # side view must allow the new nose: S(x, z) >= widest |y| whose blended top reaches z
    xs3, zs3, S = out['S']
    S = S.copy(); Sr = out['S_raw'].copy()
    for jj, x in enumerate(xx):
        jx = np.searchsorted(xs3, x)
        tops = Hb[:, j0 + jj]
        need = np.full(len(zs3), np.nan)
        for r, y in enumerate(ys2):
            if blend_weight(y) <= 0 or not np.isfinite(tops[r]):
                continue
            m = zs3 <= tops[r]
            need[m] = np.fmax(need[m], abs(y))
        has = np.isfinite(need) & (zs3 > 700)
        S[has, jx] = np.fmax(np.nan_to_num(S[has, jx], nan=-1e4), need[has])
        out['S_graze'][has, jx] = False
        Sr[has, jx] = np.fmax(np.nan_to_num(Sr[has, jx], nan=-1e4), need[has])
    out['S'] = (xs3, zs3, S); out['S_raw'] = Sr
    return out

def field(cm):
    ys, zs, F = cm['F']; _, _, G = cm['G']
    xs, ysh, H = cm['H']; _, _, B = cm['B']; xs3, zs3, S = cm['S']
    # body is inside every view's silhouette (misses -> outside); grazing cells add no constraint
    Fv = np.where(cm['F_miss'], 1e5, F)              # x must be >= F
    Gv = np.where(cm['G_miss'], 1e5, G)              # x must be <= L - G
    Hv = np.where(np.isfinite(H), np.where(cm['H_graze'], 1e5, H), -1e5)
    Bv = np.where(np.isfinite(B), np.where(cm['B_graze'], -1e5, B), 1e5)
    Sv = np.where(np.isfinite(S), np.where(cm['S_graze'], 1e5, S), -1e5)
    # keep silhouettes: a grazing cell next to a miss still bounds the body
    Hraw = np.where(np.isfinite(cm['H_raw']), cm['H_raw'] + 10.0, 1e5)
    Sraw = np.where(np.isfinite(cm['S_raw']), cm['S_raw'] + 10.0, 1e5)
    xg = np.arange(0, L + P, P); yg = ys; zg = zs
    phi = np.empty((len(xg), len(yg), len(zg)), np.float32)
    Fz, Gz = Fv.T, Gv.T                              # (y, z)
    for i, x in enumerate(xg):
        j = min(int(round(x / P)), H.shape[1] - 1)
        t_face = np.minimum(x - Fz, (L - Gz) - x)
        t_top = Hv[:, j][:, None] - zg[None, :]
        t_bot = zg[None, :] - Bv[:, j][:, None]
        t_side = Sv[:, j][None, :] - np.abs(yg)[:, None]
        # hard limits: never above the GLB's own top surface or outside its sides (+10 mm)
        t_top2 = Hraw[:, j][:, None] - zg[None, :]
        t_side2 = Sraw[:, j][None, :] - np.abs(yg)[:, None]
        phi[i] = np.clip(np.minimum.reduce([t_face, t_top, t_bot, t_side, t_top2, t_side2]), -40, 40)
    return xg, yg, zg, phi

if __name__ == "__main__":
    import time
    T = time.time()
    mesh = trimesh.load("out/sample_mm.stl")
    import os, pickle
    if os.path.exists("out/hull_res.pkl"):
        res = pickle.load(open("out/hull_res.pkl", "rb"))
    else:
        res = maps(mesh); pickle.dump(res, open("out/hull_res.pkl", "wb"))
    print("maps", round(time.time() - T), flush=True)
    np.savez("out/hull_maps.npz", **{k + '_' + n: v for k, t in res.items() for n, v in zip('abD', t)})
    cm = clean_maps(res)
    xg, yg, zg, phi = field(cm); print("field", phi.shape, round(time.time() - T), flush=True)
    # iso level slightly off zero: flat fills and blends land exactly on grid values, and an exact
    # zero at a grid point is what makes marching cubes emit non-manifold edges
    vtx, faces, _, _ = measure.marching_cubes(np.pad(phi, 1, constant_values=-40), 0.37)
    vtx = (vtx - 1) * P + np.array([xg[0], yg[0], zg[0]])
    m = trimesh.Trimesh(vtx, faces[:, ::-1], process=True)
    parts = m.split(only_watertight=False) if len(m.faces) < 0 else None
    trimesh.repair.fix_normals(m)
    trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=8)
    print("mesh", len(m.faces), "watertight", m.is_watertight, "volume", round(m.volume / 1e9, 3), "bounds", m.bounds.round(0).tolist(), round(time.time() - T), flush=True)
    m.export("out/glb_hull.stl")
    # also keep the cleaned F/G maps for the features
    np.savez("out/hull_ends.npz", ysf=cm['F'][0], zsf=cm['F'][1], Ff=np.where(cm['F_miss'], np.nan, res['F'][2]),
             ysr=cm['G'][0], zsr=cm['G'][1], Fr=np.where(cm['G_miss'], np.nan, res['G'][2]))
