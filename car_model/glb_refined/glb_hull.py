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

# ---- squarer, fuller tail (the GLB's tail is boat-shaped in plan; the concept's rear face is flat) ----
X_T0 = 4700.0; R_TAIL = 120.0; TAPER = 60.0; CROWN = 20.0
Z_T1, Z_T2 = 1000.0, 1120.0                                # reshaped below Z_T1, blended back by Z_T2

def tail_profile(zs, G, ys):
    """Rear-face set-back at the centre line vs z: median over |y| < 300, heavily smoothed."""
    c = np.abs(ys) < 300
    prof = np.array([np.nanmedian(G[r, c]) if np.isfinite(G[r, c]).any() else np.nan for r in range(len(zs))])
    ok = np.isfinite(prof)
    prof = np.interp(zs, zs[ok], prof[ok])
    prof[zs < 420] = prof[np.searchsorted(zs, 420.0)]          # below the bumper line the face runs straight down
    return ndimage.gaussian_filter1d(prof, 25)

def square_tail(res):
    ys, zs, G = res['G']; xs3, zs3, S = res['S']; xs, ys2, H = res['H']
    G = G.copy(); S = S.copy(); H = H.copy()
    G0 = tail_profile(zs, G, ys)
    jt = np.searchsorted(xs3, X_T0)
    Y0 = np.full(len(zs3), np.nan)
    wmax = np.zeros(len(xs3))
    for r, z in enumerate(zs3):
        if z < Z_FLOOR - 4 or z > Z_T2:
            continue
        zr_ = max(z, 260.0)                                  # sides below 260 mm come from 260..600 later
        rr = np.searchsorted(zs3, zr_)
        s4 = S[rr, jt]
        if not np.isfinite(s4):
            continue
        s0 = np.clip((S[rr, jt + 5] - S[rr, jt - 5]) / (xs3[jt + 5] - xs3[jt - 5]), -0.15, 0.0)
        wt = s4 - TAPER; y0 = wt - R_TAIL
        rg = np.searchsorted(zs, z)
        g0 = G0[np.searchsorted(zs, max(z, 420.0))]            # the lower face continues the 420 mm line
        gc = g0 + CROWN
        xc = L - gc - R_TAIL                                  # corner circle centre (plan view)
        new = np.full(len(xs3), np.nan)
        x = xs3
        a = (x >= X_T0) & (x <= xc)
        t = (x[a] - X_T0) / (xc - X_T0)
        h00, h10, h01 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2
        new[a] = h00 * s4 + h10 * (xc - X_T0) * s0 + h01 * wt
        b = (x > xc) & (x <= xc + R_TAIL)
        new[b] = y0 + np.sqrt(np.maximum(R_TAIL**2 - (x[b] - xc)**2, 0.0))
        new[x > xc + R_TAIL] = y0                             # between the corners the rear view sets the face
        w = np.clip((z - Z_T1) / (Z_T2 - Z_T1), 0, 1)
        old = S[r, jt:]; nw = new[jt:]
        S[r, jt:] = np.where(np.isfinite(old) & np.isfinite(nw), (1 - w) * nw + w * old,
                             np.where(w < 0.5, nw, old))
        if z <= Z_T1:
            Y0[r] = y0
            wmax = np.fmax(wmax, np.nan_to_num(new, nan=0.0))
        # rear face: smooth set-back profile + slight plan crown + the corner circle
        ay = np.abs(ys)
        gn = g0 + CROWN * np.minimum(ay / y0, 1.0) ** 2
        gn = np.where(ay <= y0, gn, np.nan)                   # the corners come from the side view only
        go = G[rg]
        bl = np.where(np.isfinite(go) & np.isfinite(gn), (1 - w) * gn + w * go, np.where(w < 0.5, gn, go))
        G[rg] = np.where(ay <= y0, bl, np.nan)                # corners: side view only, all the way up
    # top view: cover the new, wider plan; the shoulder height continues outward from 120 mm inboard
    for j, x in enumerate(xs):
        if x < X_T0:
            continue
        jx = min(np.searchsorted(xs3, x), len(xs3) - 1)
        wn = wmax[jx]
        col = H[:, j]
        fin = np.nonzero(np.isfinite(col) & (ys2 >= 0))[0]
        if len(fin) == 0 or wn <= 0:
            continue
        ye = ys2[fin[-1]]
        if wn <= ye + 10.0:
            continue
        ref = col[np.searchsorted(ys2, max(ye - 120.0, 0.0))]
        for sg in (1, -1):
            sel = (sg * ys2 > ye - 120.0) & (sg * ys2 <= wn)
            H[sel, j] = np.fmax(np.nan_to_num(H[sel, j], nan=-1e4), ref)
    # top view of the new tail, derived from the new rear face (G) and sides (S), so all three views
    # describe one shape: H(x, y) = highest z inside both; plus the deck carried out to the face and
    # rounded over onto it with a 60 mm radius
    jd = np.searchsorted(xs, 5150.0); R_DECK = 60.0
    rows = np.nonzero((zs3 >= Z_FLOOR - 4) & (zs3 <= Z_T1))[0]
    zz = zs3[rows]
    ay = np.abs(ys2)
    y0z = Y0[rows]
    y0t = float(np.nanmin(Y0[(zs3 > Z_T1 - 60) & (zs3 <= Z_T1)]))
    g0t = G0[np.searchsorted(zs, Z_T1)]
    Grows = G[np.searchsorted(zs, zz)]                       # (z, y)
    hd = H[:, jd].copy()
    for j in range(jd, len(xs)):
        x = xs[j]
        Sz = S[rows, j]                                       # (z,)
        inside = (ay[None, :] <= np.nan_to_num(Sz, nan=-1.0)[:, None]) & \
                 ((ay[None, :] > np.nan_to_num(y0z, nan=1e4)[:, None]) | (x <= L - np.nan_to_num(Grows, nan=1e5)))
        hz = np.where(inside.any(0), zz[::-1][np.argmax(inside[::-1], 0)], np.nan)
        x1 = L - g0t - CROWN * np.minimum(ay / y0t, 1.0) ** 2 - R_DECK
        ext = np.where(x <= x1, hd, hd - R_DECK + np.sqrt(np.maximum(R_DECK**2 - (x - x1)**2, 0.0)))
        ext = np.where((x <= x1 + R_DECK) & np.isfinite(hd), ext, np.nan)   # the sides trim the corners
        hn = np.fmax(hz, ext)
        w = np.clip((x - 5150.0) / 60.0, 0, 1)                # fade in from the GLB deck
        H[:, j] = np.where(np.isfinite(H[:, j]) & np.isfinite(hn), (1 - w) * H[:, j] + w * hn,
                           np.where(w < 0.5, H[:, j], hn))
    res = dict(res)
    res['G_sil'] = silhouette(res['G'][2])                  # the rear view still sees the full body width
    res['G'] = (ys, zs, G); res['S'] = (xs3, zs3, S); res['H'] = (xs, ys2, H)
    np.savez("out/tail.npz", z=zs3, y0=Y0)
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

def smooth_slope(s, sigma=3):
    """Slope used for slack and grazing: smoothed, so neither flickers from cell to cell (that
    flicker left dots and ripples on the panels)."""
    return nsmooth(np.nan_to_num(s, nan=0.0), np.isfinite(s), sigma)

def clean_mask(g):
    """Grazing mask without specks or pin holes."""
    st = np.ones((3, 3), bool)
    g = ndimage.binary_opening(g, st, iterations=2)
    return ndimage.binary_closing(g, st, iterations=2) | g

def slack_from(s):
    return np.minimum(3.0 * np.nan_to_num(s, nan=0.0), 8.0)

FILL = np.hypot(*np.mgrid[-12:13, -12:13]) <= 12.5        # 100 mm disc: fills any dip narrower than that

def extend_nearest(D, valid):
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return D[tuple(idx)]

def fill_down(D, valid):
    """Depth map (bigger = further from the viewer): remove narrow deep pits (grey opening),
    including notches that touch the outline."""
    if not valid.any():
        return D
    Dn = extend_nearest(np.where(valid, D, 0.0), valid)
    return np.where(valid, np.minimum(D, ndimage.grey_opening(Dn, footprint=FILL)), np.nan)

def fill_up(D, valid):
    """Height map (bigger = toward the viewer): fill narrow dips (grey closing)."""
    if not valid.any():
        return D
    Dn = extend_nearest(np.where(valid, D, 0.0), valid)
    return np.where(valid, np.maximum(D, ndimage.grey_closing(Dn, footprint=FILL)), np.nan)

def extend_down(D, zs, z_floor, z_from, outward=None):
    """For each column of a (z rows, other cols) map: below its lowest surface value under z_from,
    repeat that value down to the floor, so the faces run straight down to a flat underside.
    outward='min' (depth maps) / 'max' (width maps): instead use the most outward value below z_from,
    so the lower face is a straight plane with nothing tucked under it."""
    D = D.copy()
    rows = np.nonzero((zs >= z_floor - 4) & (zs <= z_from))[0]
    if outward == 'min':
        # bumper line at z_from, fitted as an even polynomial in y so plates / tips / brackets drop out
        r = rows[-1]
        yv = np.arange(D.shape[1]) * P - 1000.0
        ok = np.isfinite(D[r]) & (np.abs(yv) < 760)
        coef = np.polyfit(yv[ok] ** 2, D[r, ok], 3) if ok.sum() > 20 else None
        line = np.where(np.abs(yv) < 760, np.polyval(coef, yv ** 2), D[r]) if coef is not None else D[r]
        line = np.where(np.isfinite(D[r]), np.maximum(line, np.nanmin(D[r, ok]) if ok.any() else line), np.nan)
    for c in range(D.shape[1]):
        col = D[rows, c]
        ok = np.nonzero(np.isfinite(col))[0]
        if len(ok) == 0:
            continue
        first = ok[0]
        if outward == 'min':
            # the lower face (floor up to z_from) continues the (smoothed) bumper line straight down
            D[rows, c] = line[c] if np.isfinite(line[c]) else col[np.nonzero(np.isfinite(col))[0][-1]]
        else:
            D[rows[:first], c] = col[first]
    return D

# grille / hood blend (world coordinates; matches glb_features: SY, zf(), XG)
XG = 4.0; X_HOOD = 540.0; SY = 0.976
def zf(z): return 168.0 + (z - 120.0) * (920.0 - 168.0) / (965.0 - 120.0)
def grille_top(y):
    yc = np.clip(np.abs(y) / SY, 0, 545.0)
    return zf(965.0 - 25.0 * (yc / 545.0) ** 2)
def blend_weight(y):
    t = np.clip((np.abs(y) - 470.0) / 230.0, 0, 1)
    return 0.5 * (1 + np.cos(np.pi * t))

SIL = np.hypot(*np.mgrid[-10:11, -10:11]) <= 10            # 80 mm disc
def silhouette(D):
    """Inside of a view's silhouette, with pin holes and narrow notches closed."""
    v = np.isfinite(D)
    return ndimage.binary_fill_holes(ndimage.binary_closing(v, structure=SIL, iterations=1) | v)

Z_FLOOR = 190.0                                            # flat underside

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
        Y, Z = np.meshgrid(a, b)
        D = np.where((Z < 420) & (np.abs(Y) > 560) & (D > 420), np.nan, D)   # tyres seen under the bumper
        if k == 'F':
            # nose corners / headlamp surround: smoother outside the grille (they wrinkled)
            # the GLB's headlamp cavities dent the fender corners: fill recesses up to ~160 mm wide there
            reg = (np.abs(Y) > 500) & (Z > 520) & (Z < 1000) & np.isfinite(D)
            Dn = extend_nearest(np.where(np.isfinite(D), D, 0.0), np.isfinite(D))
            D = np.where(reg, np.minimum(D, ndimage.grey_opening(Dn, size=(41, 41))), D)
            D = np.where(np.abs(Y) < 560, D, nsmooth(np.nan_to_num(D, nan=0.0), np.isfinite(D), 6))
        D = extend_down(D, b, Z_FLOOR, 420.0, outward='min')
        D = fill_down(D, np.isfinite(D))                         # lower-front slot, deck-lid slot, panel ripple
        s = smooth_slope(slope_info(D))
        g = clean_mask(np.nan_to_num(s, nan=0.0) > 2.5)
        Dc = np.where(g, -1e5, D - slack_from(s))
        if k == 'F':
            Y, Z = np.meshgrid(a, b)
            # above the grille top the hood / cowl / screen come from the top view only
            Dc = np.where((np.abs(Y) < 800) & (Z > grille_top(Y)), -1e5, Dc)
            # grille area: solid right up to the grille front plane (the vane pocket is cut later),
            # receding gently past the grille corners, so there is no slot under the hood blend
            ay = np.abs(Y)
            core = (ay <= 532) & (Z >= Z_FLOOR - 4) & (Z <= grille_top(Y))     # flush to the floor under the grille
            edge = (ay > 532) & (ay < 650) & (Z >= grille_top(Y) - 160) & (Z <= grille_top(Y))
            Dc = np.where(core, np.minimum(np.where(Dc < -1e4, 1e5, Dc), XG), Dc)
            Dc = np.where(edge, np.minimum(np.where(Dc < -1e4, 1e5, Dc), XG + 2.5 * (ay - 532)), Dc)
        else:
            # rear window / deck lid come from the top view only (the rear view's noise dented them)
            Dc = np.where((np.abs(Y) < 800) & (Z > 1100.0), -1e5, Dc)
        out[k] = (a, b, np.where(np.isfinite(D), Dc, -1e5))      # gap inside the outline: no constraint
        out[k + '_miss'] = ~(silhouette(D) | res.get(k + '_sil', False))
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
            # round off the kinks where the bridge meets hood and screen
            c0, c1 = ia - 20, ib + 20
            blk = D[:, c0:c1 + 1]
            sm = nsmooth(np.nan_to_num(blk, nan=0.0), np.isfinite(blk), 6)
            D[rows, c0:c1 + 1] = np.where(np.isfinite(blk[rows]), sm[rows], blk[rows])
            valid = np.isfinite(D)
        if k == 'H':
            D = bridge_wheels(D, a, np.abs(b) > 540)                  # fender tops over the arches
        elif k == 'S':
            D = bridge_wheels(D, a, (b > 120) & (b < 960))            # body sides over the arches
            # below 260 mm the sides drop vertically from their widest point between 260 and 600 mm,
            # so the floor is a straight plane out to the full body width (no tuck-under, no overhang)
            band = (b >= 260.0) & (b <= 600.0)
            ref = np.nanmax(np.where(np.isfinite(D[band]), D[band], -np.inf), axis=0)
            ref = np.where(np.isfinite(ref), ref, np.nan)
            low = (b >= Z_FLOOR - 4) & (b < 260.0)
            D[low] = np.where(np.isfinite(ref)[None, :], ref[None, :], D[low])
            D = extend_down(D, b, Z_FLOOR, 600.0)
        elif k == 'B':
            # floor under the wheel zones: lift the bottom limit to the floor line ahead of / behind the wheel
            D = bridge_wheels(D, a, np.abs(b) > 540)
        valid = np.isfinite(D)
        if k in ('H', 'S'):
            raw = out[k + '_raw']
            out[k + '_raw'] = np.where(np.isfinite(D), np.fmax(np.nan_to_num(raw, nan=-1e4), D), raw)
        Ds = nsmooth(np.nan_to_num(D, nan=0.0), valid, {'H': 9, 'B': 4, 'S': (4, 10)}[k])
        s = smooth_slope(slope_info(Ds))
        sgn = -1.0 if k == 'B' else 1.0                       # H, S are upper bounds; B is a lower bound
        out[k] = (a, b, Ds + sgn * slack_from(s))
        out[k + '_graze'] = clean_mask(np.nan_to_num(s, nan=0.0) > 2.5)
        if k in ('H', 'S'):
            # the hard limit only trims real protrusions: never below the smoothed shape itself
            raw = out[k + '_raw']
            out[k + '_raw'] = np.where(np.isfinite(Ds), np.fmax(np.nan_to_num(raw, nan=-1e4), Ds + slack_from(s)), raw)
        if k == 'H':
            out['H_smooth'] = Ds
    # the cowl bridge lifts the top above the GLB's own side outline: no side hard limit there
    xs3_, zs3_ = out['S'][0], out['S'][1]
    out['S_raw'][np.ix_(zs3_ > 900, (xs3_ >= 1400) & (xs3_ <= 1740))] = np.nan
    # ---- grille top -> hood: Hermite blend from the grille top edge to the hood at X_HOOD ----
    xs, ys2, H = out['H']; Hs = out['H_smooth']
    j0, j1 = np.searchsorted(xs, XG), np.searchsorted(xs, X_HOOD)
    xx = xs[j0:j1 + 1]
    Hb = H.copy(); Hr = out['H_raw']
    X_ARC = 230.0                                        # length of the arc from the grille top edge
    fit = (xs >= 560.0) & (xs <= 900.0)
    for r, y in enumerate(ys2):
        w = blend_weight(y)
        ok = fit & np.isfinite(Hs[r])
        if w <= 0 or ok.sum() < 20:
            continue
        # hood line (straight fit behind the GLB's nose bulge), carried forward to the grille; the nose
        # is that line minus a quadratic fall-off: one clean arc from the grille top, tangent to the
        # hood at X_ARC behind it, no hump and no dip
        p = np.polyfit(xs[ok], Hs[r, ok], 1)
        hood = np.polyval(p, xx)
        d0 = np.polyval(p, XG) - grille_top(y)
        t = np.clip((xx - XG) / X_ARC, 0, 1)
        curve = hood - d0 * (1 - t) ** 2
        s_ = np.clip((xx - 420.0) / (xx[-1] - 420.0), 0, 1)         # hand over to the real hood by X_HOOD
        hs = Hs[r, j0:j1 + 1]
        curve = np.where(np.isfinite(hs), (1 - s_) * curve + s_ * hs, curve)
        cur = Hb[r, j0:j1 + 1]
        have = np.isfinite(cur)
        # blend with surface that exists; create new surface only inside the grille width
        Hb[r, j0:j1 + 1] = np.where(have, (1 - w) * cur + w * curve, curve if abs(y) <= 540 else np.nan)
        out['H_graze'][r, j0:j1 + 1] &= w < 0.5
        Hr[r, j0:j1 + 1] = np.fmax(np.nan_to_num(Hr[r, j0:j1 + 1], nan=-1e4), Hb[r, j0:j1 + 1])
    # smooth the blended nose across y as well, so the grille corners fade into the fenders
    rows = np.nonzero(blend_weight(ys2) > 0)[0]
    r0, r1 = max(rows.min() - 20, 0), min(rows.max() + 20, len(ys2) - 1)
    c0, c1 = max(j0 - 2, 0), j1 + 20
    patch = Hb[r0:r1 + 1, c0:c1 + 1]
    ok = np.isfinite(patch)
    sm = nsmooth(np.nan_to_num(patch, nan=0.0), ok, 6)
    keep_front = np.arange(c0, c1 + 1)[None, :] <= j0 + 1                # leave the grille top edge crisp
    Hb[r0:r1 + 1, c0:c1 + 1] = np.where(ok & ~keep_front, sm, patch)
    Hr[r0:r1 + 1, c0:c1 + 1] = np.fmax(Hr[r0:r1 + 1, c0:c1 + 1], Hb[r0:r1 + 1, c0:c1 + 1])
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
    # silhouettes are grown by 12 mm: the outline of one view must never cut a surface that another
    # view defines (its jagged 4 mm edge cut dents into the roof crown); the hard limits (+10 mm) and
    # the other views still bound the body there
    grow = lambda m: ndimage.binary_dilation(m, iterations=3)
    Fv = np.where(~grow(~cm['F_miss']), 1e5, F)      # x must be >= F
    Gv = np.where(~grow(~cm['G_miss']), 1e5, G)      # x must be <= L - G
    # outside a view's silhouette: excluded; a pin hole inside it: no constraint from that view
    Hin, Sin = grow(silhouette(H)), grow(silhouette(S))
    Hv = np.where(np.isfinite(H), np.where(cm['H_graze'], 1e5, H), np.where(Hin, 1e5, -1e5))
    Sv = np.where(np.isfinite(S), np.where(cm['S_graze'], 1e5, S), np.where(Sin, 1e5, -1e5))
    # keep silhouettes: a grazing cell next to a miss still bounds the body
    Hraw = np.where(np.isfinite(cm['H_raw']), cm['H_raw'] + 10.0, 1e5)
    Sraw = np.where(np.isfinite(cm['S_raw']), cm['S_raw'] + 10.0, 1e5)
    Hraw = np.where(Hin & ~np.isfinite(cm['H_raw']), 1e5, Hraw)
    xg = np.arange(0, L + P, P); yg = ys; zg = zs
    phi = np.empty((len(xg), len(yg), len(zg)), np.float32)
    Fz, Gz = Fv.T, Gv.T                              # (y, z)
    for i, x in enumerate(xg):
        j = min(int(round(x / P)), H.shape[1] - 1)
        t_face = np.minimum(x - Fz, (L - Gz) - x)
        t_top = Hv[:, j][:, None] - zg[None, :]
        t_bot = np.broadcast_to(zg[None, :] - Z_FLOOR, (len(yg), len(zg)))      # flat floor
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
    res = square_tail(res)
    print("maps", round(time.time() - T), flush=True)
    np.savez("out/hull_maps.npz", **{k + '_' + n: v for k, t in res.items() for n, v in zip('abD', t)})
    cm = clean_maps(res)
    xg, yg, zg, phi = field(cm); print("field", phi.shape, round(time.time() - T), flush=True)
    # iso level slightly off zero: flat fills and blends land exactly on grid values, and an exact
    # zero at a grid point is what makes marching cubes emit non-manifold edges
    # values landing exactly on the level (they do: maps and grids share 4 mm steps) give degenerate,
    # non-manifold cells, which smoothing then drags into dents: nudge them off the level
    ISO = 0.37
    near = np.abs(phi - ISO) < 0.03
    phi[near] = np.where(phi[near] >= ISO, ISO + 0.03, ISO - 0.03)
    vtx, faces, _, _ = measure.marching_cubes(np.pad(phi, 1, constant_values=-40), ISO)
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
