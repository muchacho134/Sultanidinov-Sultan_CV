"""Parametric luxury saloon built from the blueprint (mm).
Axes match the DrivAer reference: X = front(0) -> rear, Y = lateral (symmetric), Z = up, ground at Z=0.
Overall: L 5360, W 2000, H 1630, front overhang 905, wheelbase 3300, rear overhang 1155,
track 1620 front / 1630 rear.
"""
import math, sys
import numpy as np
from scipy.interpolate import PchipInterpolator
import cadquery as cq
from cadquery import Vector as V

L, W, H = 5360.0, 2000.0, 1630.0
# axle positions taken from the drawing itself (the 905/5300/1155 labels do not add up to 5360)
XF, XR = 700.0, 4130.0
WB = XR - XF
TRACK_F, TRACK_R = 1620.0, 1630.0
R_TIRE = 395.0
ZC = R_TIRE + 4.0               # 4 mm ground gap, like the reference
R_ARCH = 445.0
X0 = 50.0                       # body skin starts here; grille stands proud to X=0

def P(xs, ys):
    return PchipInterpolator(np.array(xs, float), np.array(ys, float))

# ---- longitudinal control curves -------------------------------------------------
# Heights/widths traced off the concept's side, front, rear and top views, with each view's
# axes scaled to the labelled 5360 x 2000 x 1630 envelope.
# top centre line: hood leading edge, hood rising to the cowl, screen, roof, backlight, deck
zt = P([0, 40, 150, 600, 1000, 1300, 1380, 1600, 1850, 2050, 2300, 2600, 3300, 3800, 4000, 4200, 4450, 4630, 4800, 5100, 5300, 5340, 5360],
       [975, 995, 1005, 1040, 1080, 1105, 1125, 1290, 1445, 1560, 1615, 1632, 1632, 1620, 1590, 1480, 1300, 1195, 1172, 1140, 1112, 1085, 1045])
# shoulder top / shelf height (fenders, waist, rear haunches)
zs = P([0, 100, 600, 1300, 2000, 4000, 4600, 5100, 5300, 5360],
       [955, 985, 1030, 1080, 1090, 1090, 1085, 1070, 1045, 1005])
# underside: low front bumper, sill, rear bumper
zb = P([0, 60, 300, 700, 1200, 3800, 4600, 5100, 5300, 5360],
       [175, 140, 130, 170, 180, 180, 180, 155, 150, 175])
# maximum half width (plan view): full 2000 between tight, rounded corners
hw = P([0, 30, 100, 200, 400, 700, 1600, 2600, 3600, 4200, 4800, 5000, 5150, 5260, 5320, 5350, 5360],
       [745, 805, 900, 955, 990, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 992, 965, 925, 870, 830])
# half width at the top surface: hood / roof rail / deck (kept inside the shoulder shelf)
hwt = P([0, 300, 1300, 1380, 1700, 2100, 2500, 3500, 3900, 4200, 4630, 5000, 5300, 5360],
        [600, 680, 760, 780, 750, 690, 680, 680, 690, 715, 730, 740, 720, 680])

N_STATIONS = 36
def stations():
    # denser at both ends where the shape changes fastest
    t = np.linspace(0, 1, N_STATIONS)
    s = t - 0.08 * np.sin(2 * np.pi * t)
    return np.clip(s * L, 0, L)

def rounded_poly(verts, radii, nseg):
    """Open polyline with filleted interior corners, sampled with a fixed number of
    points per primitive so every section has the same parametrisation."""
    v = [np.array(p, float) for p in verts]
    prims = []   # list of ('L', p0, p1) / ('A', centre, r, a0, a1)
    cur = v[0]
    for i in range(1, len(v) - 1):
        p, a, b = v[i], v[i - 1], v[i + 1]
        u1 = (a - p) / np.linalg.norm(a - p); u2 = (b - p) / np.linalg.norm(b - p)
        ang = math.acos(np.clip(u1 @ u2, -1, 1))
        r = radii[i]
        d = r / math.tan(ang / 2)
        d = min(d, 0.48 * np.linalg.norm(a - p), 0.48 * np.linalg.norm(b - p))
        r = d * math.tan(ang / 2)
        t1, t2 = p + u1 * d, p + u2 * d
        bis = (u1 + u2) / np.linalg.norm(u1 + u2)
        c = p + bis * (r / math.sin(ang / 2))
        prims.append(('L', cur, t1))
        prims.append(('A', c, r, t1, t2))
        cur = t2
    prims.append(('L', cur, v[-1]))
    out = []
    for k, pr in enumerate(prims):
        n = nseg[k]
        for j in range(n):
            s = j / n
            if pr[0] == 'L':
                out.append(pr[1] + (pr[2] - pr[1]) * s)
            else:
                _, c, r, t1, t2 = pr
                a0 = math.atan2(*(t1 - c)[::-1]); a1 = math.atan2(*(t2 - c)[::-1])
                da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                a = a0 + da * s
                out.append(c + r * np.array([math.cos(a), math.sin(a)]))
    out.append(v[-1])
    return out

def section_geom(x):
    b, s, t = float(zb(x)), float(zs(x)), float(zt(x))
    w = float(hw(x))
    dz = max(t - s, 40.0)
    crown = min(0.08 * dz, 45.0) + 8.0
    inset = min(200.0, 0.2 * w)                 # width of the shoulder shelf
    shelf = (w - inset, s + 15)
    wt = min(float(hwt(x)), shelf[0] - 60)
    rail = (wt, t - crown)
    return b, s, t, w, wt, dz, crown, shelf, rail

def section_pts(x):
    b, s, t, w, wt, dz, crown, shelf, rail = section_geom(x)
    k = shelf[0] / (w - 200) if w > 1000 else (w - shelf[0]) / 200.0   # shrink the shoulder at the ends
    # full-width, upright lower body; big rounded shoulder up to a flat shelf; cabin on the shelf
    verts = [(0.0, b), (w - 20, b), (w, s - 250 * k), (w - 15 * k, s - 130 * k), (w - 60 * k, s - 50 * k),
             (w - 120 * k, s), shelf, rail, (0.0, t)]
    radii = [0, 110, 260, 140, 90, 60, 35, min(0.4 * dz, 110), 0]
    nseg = [3, 5, 4, 3, 3, 3, 2, 3, 2, 3, 2, 3, 3, 5, 5]
    half = rounded_poly(verts, radii, nseg)
    half = [(float(y), float(z)) for y, z in half]
    pts = half + [(-y, z) for (y, z) in reversed(half[1:-1])]
    return [V(x, y, z) for (y, z) in pts]

def body_loft():
    wires = []
    for x in stations():
        pts = [V(X0 + p.x * (L - X0) / L, p.y, p.z) for p in section_pts(x)]
        e = cq.Edge.makeSpline(pts, periodic=True)
        wires.append(cq.Wire.assembleEdges([e]))
    return cq.Solid.makeLoft(wires, ruled=False)

# ---- helpers ---------------------------------------------------------------------
def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def both(f):
    """f(sign) -> solid; returns list for left and right."""
    return [f(1), f(-1)]

def _bop(op, s, tools):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
    from OCP.TopTools import TopTools_ListOfShape
    args, tl = TopTools_ListOfShape(), TopTools_ListOfShape()
    args.Append(s.wrapped)
    for t in tools:
        tl.Append(t.wrapped)
    b = BRepAlgoAPI_Cut() if op == "cut" else BRepAlgoAPI_Fuse()
    b.SetArguments(args); b.SetTools(tl)
    b.SetRunParallel(True)
    b.Build()
    return cq.Shape.cast(b.Shape())

def cut_all(s, tools):
    return _bop("cut", s, tools) if tools else s

def fuse_all(s, tools):
    return _bop("fuse", s, tools).clean() if tools else s

def scaled_y(shape, k):
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    g = gp_GTrsf(); g.SetVectorialPart(gp_Mat(1, 0, 0, 0, k, 0, 0, 0, 1))
    return cq.Shape.cast(BRepBuilderAPI_GTransform(shape.wrapped, g, True).Shape())

def xz_prism(pts, y0, y1):
    w = cq.Workplane("XZ", origin=(0, y0, 0)).polyline(pts).close()
    return w.extrude(-(y1 - y0)).val()   # XZ normal is -Y

# ---- body details ----------------------------------------------------------------
def wheel_wells():
    tools = []
    for xc in (XF, XR):
        for sg in (1, -1):
            y0 = 640.0
            c = cq.Solid.makeCylinder(R_ARCH, 600, V(xc, sg * y0, ZC), V(0, sg, 0))
            tools.append(c)
    return tools

def side_windows():
    """Daylight openings: front door, rear door, quarter light (X ranges read off the side view)."""
    panes = [(1400, 2630), (2715, 3545), (3610, 3900)]
    out = []
    for xa, xb in panes:
        xs = np.linspace(xa, xb, 40)
        top = [float(zt(x)) - 75 for x in xs]
        bot = [section_geom(x)[7][1] + 15 for x in xs]
        keep = [(x, zt_, zb_) for x, zt_, zb_ in zip(xs, top, bot) if zt_ - zb_ > 25]
        if len(keep) < 3:
            continue
        out.append([(x, z) for x, z, _ in keep] + [(x, z) for x, _, z in reversed(keep)])
    return out

def halfspace_x_axis(p, n, x0=0.0, x1=L):
    """Big box occupying {q : (q - p).n > 0} for a normal n lying in the YZ plane."""
    phi = math.degrees(math.atan2(n[1], n[0]))
    b = cq.Solid.makeBox(x1 - x0, 3000, 6000, V(x0, 0, -3000)).rotate(V(0, 0, 0), V(1, 0, 0), phi)
    return b.translate(V(0, p[0], p[1]))

def halfspace_y_axis(p, n):
    """Big box occupying {q : (q - p).n > 0} for a normal n = (nx, nz) in the XZ plane."""
    phi = math.degrees(math.atan2(n[0], n[1]))      # rotate +Z toward +X
    b = cq.Solid.makeBox(6000, 3000, 3000, V(-3000, -1500, 0)).rotate(V(0, 0, 0), V(0, 1, 0), phi)
    return b.translate(V(p[0], 0, p[1]))

def glass_recesses(body, depth=9.0):
    tools = []
    for poly in side_windows():
        xm = 0.5 * (min(x for x, _ in poly) + max(x for x, _ in poly))
        g = section_geom(xm)
        a = np.array(g[7]); bpt = np.array(g[8])
        d = (bpt - a) / np.linalg.norm(bpt - a)
        n = np.array([d[1], -d[0]])
        if n[0] < 0: n = -n
        p = a + 0.35 * (bpt - a) - depth * n
        for sg in (1, -1):
            pr = xz_prism(poly, 300, 1300)
            hs = halfspace_x_axis(p, n)
            tool = pr.intersect(hs)
            tools.append(tool if sg > 0 else tool.mirror("XZ"))
    for xa, xb, fwd in ((1450, 2200, True), (4080, 4560, False)):
        pa = np.array([xa, float(zt(xa))]); pb = np.array([xb, float(zt(xb))])
        d = (pb - pa) / np.linalg.norm(pb - pa)
        n = np.array([-d[1], d[0]])
        if n[1] < 0: n = -n
        p = 0.5 * (pa + pb) - (depth + 6) * n
        xs = np.linspace(xa - 60, xb + 60, 30)
        half = [(x, float(hwt(x)) - 85) for x in xs]
        poly = half + [(x, -y) for x, y in reversed(half)]
        pr = cq.Workplane("XY", origin=(0, 0, 1060)).polyline(poly).close().extrude(800).val()
        tools.append(pr.intersect(halfspace_y_axis(p, n)))
    return tools

def yz_prism(poly, x0, x1):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(poly).close().extrude(x1 - x0).val()

def rrect(y0, y1, z0, z1, r, n=4):
    """Rounded rectangle in the YZ plane as a polygon."""
    r = min(r, 0.49 * (y1 - y0), 0.49 * (z1 - z0))
    pts = []
    for cy, cz, a0 in ((y1 - r, z0 + r, -90), (y1 - r, z1 - r, 0), (y0 + r, z1 - r, 90), (y0 + r, z0 + r, 180)):
        for j in range(n + 1):
            a = math.radians(a0 + 90 * j / n)
            pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def grille():
    """Upright grille shell: arched-top surround, 17 vanes and a centre bar, standing proud."""
    zc = lambda y, top: top - 25 * (y / 545.0) ** 2          # gently arched top edge
    ys = np.linspace(-545, 545, 23)
    outer = [(545, 340)] + [(y, zc(y, 965)) for y in ys[::-1]] + [(-545, 340)]
    yi = np.linspace(-495, 495, 23)
    inner = [(495, 365)] + [(y, zc(y, 908)) for y in yi[::-1]] + [(-495, 365)]
    shell = yz_prism(outer, 0, 160)
    pocket = yz_prism(inner, -1, 40)
    shell = shell.cut(pocket)
    bars = []
    for k in range(-8, 9):
        w2, xf = (11, 4) if k == 0 else (8, 10)
        bars.append(box(xf, 42, 55 * k - w2, 55 * k + w2, 360, 960))
    bars = cq.Compound.makeCompound(bars).intersect(yz_prism(inner, 0, 45))
    return shell.fuse(bars).clean()

def mirrors():
    out = []
    for sg in (1, -1):
        m = box(1600, 1790, 880, 1095, 1135, 1250).fuse(box(1620, 1740, 700, 900, 1150, 1200))
        out.append(m if sg > 0 else m.mirror("XZ"))
    return out

_XS = {}
def x_surface(y, z, front=True):
    """World X of the body skin at half-width |y| and height z near the front / rear end."""
    key = front
    if key not in _XS:
        xs = np.linspace(0, 1100, 111) if front else np.linspace(L, L - 1100, 111)
        zz = np.arange(100, 1201, 20.0)
        tab = np.array([[skin_y(x, z_) for z_ in zz] for x in xs])
        _XS[key] = (xs, zz, tab)
    xs, zz, tab = _XS[key]
    col = np.array([np.interp(z, zz, tab[i]) for i in range(len(xs))])
    y = abs(y)
    ok = np.nonzero(col >= y)[0]
    i = ok[0] if len(ok) else len(xs) - 1
    if 0 < i < len(xs):                              # linear refine between stations
        c0, c1 = col[i - 1], col[i]
        f = (y - c0) / (c1 - c0) if c1 != c0 else 1.0
        xr = xs[i - 1] + (xs[i] - xs[i - 1]) * np.clip(f, 0, 1)
    else:
        xr = xs[i]
    return X0 + xr * (L - X0) / L

def skin_region(y0, y1, z0, z1, d0, d1, front=True, nz=5, ny=20):
    """Solid between depth d0 and d1 under the front/rear skin (negative d = outside)."""
    sg = 1 if front else -1
    wires = []
    for z in np.linspace(z0, z1, nz):
        ys = np.linspace(y0, y1, ny)
        outer = [(x_surface(y, z, front) + sg * d0, y) for y in ys]
        inner = [(x_surface(y, z, front) + sg * d1, y) for y in ys[::-1]]
        wires.append(cq.Wire.makePolygon([V(x, y, z) for x, y in outer + inner], close=True))
    return cq.Solid.makeLoft(wires, ruled=True)

def pocket(poly, depth, front=True, d0=-30.0):
    """Recess with a YZ outline whose floor follows the skin at the given depth."""
    ys = [p[0] for p in poly]; zs_ = [p[1] for p in poly]
    reg = skin_region(min(ys) - 5, max(ys) + 5, min(zs_) - 5, max(zs_) + 5, d0, depth, front)
    x0, x1 = (-100, 700) if front else (L - 700, L + 100)
    return reg.intersect(yz_prism(poly, x0, x1))

def layer(poly, d0, d1, front=True):
    """Solid with a YZ outline between depths d0 and d1 (lenses, trims; d0 < 0 stands proud)."""
    return pocket(poly, d1, front, d0)

def mir(shapes):
    return shapes + [t.mirror("XZ") for t in shapes]

def hexagon_exhaust(inset=0.0):
    pts = [(470, 335), (800, 335), (788, 250), (522, 240), (470, 300)]
    cy = sum(p[0] for p in pts) / 5; cz = sum(p[1] for p in pts) / 5
    return [(cy + (y - cy) * (1 - inset), cz + (z - cz) * (1 - inset)) for y, z in pts]

def light_recesses():
    t = []
    # ---- front ----
    t += mir([pocket(rrect(563, 910, 740, 862, 32), 40)])                   # headlamp housing
    t += mir([pocket(rrect(825, 911, 280, 690, 34), 12),                    # intake surround
              pocket(rrect(843, 893, 300, 670, 22), 55)])                   # intake opening
    t.append(pocket(rrect(-500, 500, 205, 338, 18), 28))                    # lower grille band
    t += mir([pocket([(553, 345), (559, 345), (567, 735), (561, 735)], 4)])  # bumper pod line
    # ---- rear ----
    ubar = [(842, 545), (842, 990), (-842, 990), (-842, 545), (-671, 545), (-671, 910), (671, 910), (671, 545)]
    t.append(pocket(ubar, 30, False))                                       # tail lamp housing
    t.append(pocket(rrect(-660, 660, 640, 905, 12), 7, False))              # recessed centre panel
    t.append(pocket(rrect(-905, 905, 499, 505, 2), 4, False))               # bumper crease
    t.append(pocket(rrect(-790, 790, 190, 350, 30), 22, False))             # diffuser band
    t += mir([pocket(hexagon_exhaust(), 60, False)])                        # exhaust
    t += mir([pocket([(677, 990), (683, 990), (683, 1070), (677, 1070)], 4, False)])   # boot lid line
    return t

def hood_lines():
    """Hood shut-lines running from the grille shoulders back to the cowl."""
    t = []
    xs = np.linspace(160, 1320, 14)
    yl = np.interp(xs, [160, 1320], [560, 700])
    wires = []
    for x, y in zip(xs, yl):
        top = [(p.y, p.z) for p in section_pts((x - X0) * L / (L - X0))]
        top = top[:len(top) // 2 + 1]
        top = [q for q in top if q[1] > float(zs((x - X0) * L / (L - X0))) - 5]
        zq = float(np.interp(y, [q[0] for q in reversed(top)], [q[1] for q in reversed(top)]))
        pts = [V(x, y - 3, zq - 4), V(x, y + 3, zq - 4), V(x, y + 3, zq + 80), V(x, y - 3, zq + 80)]
        wires.append(cq.Wire.makePolygon(pts, close=True))
    g = cq.Solid.makeLoft(wires, ruled=False)
    return [g, g.mirror("XZ")]

def lamp_lenses():
    t = []
    t += mir([layer(rrect(583, 890, 760, 842, 22), 16, 45)])                # headlamp inner lens
    t += mir([layer(rrect(600, 895, 185, 203, 8), -5, 12)])                 # chrome lower-corner strip
    # tail lamp light guide: a U strip floating inside the housing
    guide = [(800, 572), (800, 962), (-800, 962), (-800, 572), (-772, 572), (-772, 940), (772, 940), (772, 572)]
    t.append(layer(guide, 12, 34, False))
    t += mir([layer(hexagon_exhaust(-0.06), 14, 30, False).cut(pocket(hexagon_exhaust(0.08), 70, False))])  # exhaust surround
    t.append(layer(rrect(-480, 480, 282, 292, 4), 10, 30))                  # lower band slats
    t.append(layer(rrect(-480, 480, 242, 252, 4), 10, 30))
    return t

def skin_y(x, z):
    """Half width of the section skin at height z on the outer side (z below the shelf)."""
    pts = [(p.y, p.z) for p in section_pts(x)]
    right = pts[:len(pts) // 2 + 1]
    for (ya, za), (yb, zb_) in zip(right[:-1], right[1:]):
        if za <= z <= zb_ and zb_ > za:
            return ya + (yb - ya) * (z - za) / (zb_ - za)
    return max(q[0] for q in right)

def groove(xl, z0, z1, depth=6.0, width=5.0):
    zz = np.linspace(z0, z1, 14)
    outer = [(skin_y(xl, z) + 60, z) for z in zz]
    inner = [(skin_y(xl, z) - depth, z) for z in reversed(zz)]
    w = cq.Workplane("YZ", origin=(xl - width / 2, 0, 0)).polyline(outer + inner).close()
    return w.extrude(width).val()

def shut_lines():
    t = []
    for xl in (1360, 2600, 3690):
        top = section_geom(xl)[7][1] - 5
        g = groove(xl, 240, top)
        t += [g, g.mirror("XZ")]
    for xh in (2300, 3320):
        y = skin_y(xh + 85, 1017)
        h = box(xh, xh + 170, y - 8, y + 80, 1005, 1030)
        t += [h, h.mirror("XZ")]
    return t

# ---- concept details: feature lines, trims, lenses, ornament ----------------------
def side_line(xs, zs_, h=6.0, depth=3.0):
    """Shallow feature-line groove: one lofted tool that follows the side skin."""
    xs = np.linspace(xs[0], xs[-1], 3 * len(xs))
    zz = np.interp(xs, np.linspace(xs[0], xs[-1], len(zs_)), zs_)
    wires = []
    for x, z in zip(xs, zz):
        yin = skin_y(x, z) - depth
        pts = [V(x, yin, z - h / 2), V(x, yin + 120, z - h / 2), V(x, yin + 120, z + h / 2), V(x, yin, z + h / 2)]
        wires.append(cq.Wire.makePolygon(pts, close=True))
    g = cq.Solid.makeLoft(wires, ruled=False)
    return [g, g.mirror("XZ")]

def feature_lines():
    t = []
    # chrome belt line under the side glass
    xs = np.linspace(1420, 3900, 11)
    t += side_line(xs, [section_geom(x)[7][1] - 4 for x in xs], h=9, depth=3)
    # fender line: from the headlamp rising to the belt
    xs = np.linspace(170, 1330, 6)
    t += side_line(xs, list(np.interp(xs, [170, 1330], [880, 1040])), h=6, depth=3)
    # shoulder / waft line from the rear door to the tail lamp
    xs = np.linspace(3950, 5250, 6)
    t += side_line(xs, list(np.interp(xs, [3950, 5250], [1020, 975])), h=6, depth=3)
    # lower door character line (chrome sill strip)
    xs = np.linspace(1180, 3660, 9)
    t += side_line(xs, [330.0] * len(xs), h=10, depth=3)
    return t

def roof_fin():
    x0 = 3820.0
    poly = [(x0, float(zt(x0)) - 25), (x0 + 190, float(zt(x0 + 190)) - 25), (x0 + 175, float(zt(x0 + 175)) + 12),
            (x0 + 120, float(zt(x0)) + 30), (x0 + 30, float(zt(x0)) + 10)]
    return xz_prism(poly, -22, 22)

def body():
    import time; T=time.time()
    b = body_loft()
    print("loft", b.isValid(), time.time()-T, flush=True)
    rec = glass_recesses(b)
    import os
    if os.path.exists("out/body_cut.brep"):
        b = cq.Shape.importBrep("out/body_cut.brep")
    else:
        b = cut_all(b, wheel_wells() + rec + light_recesses() + hood_lines() + shut_lines() + feature_lines())
        b.exportBrep("out/body_cut.brep")
    print("lights", b.isValid(), time.time()-T, flush=True)
    b = fuse_all(b, [grille()] + mirrors() + lamp_lenses() + [roof_fin()])
    print("fused", b.isValid(), time.time()-T, flush=True)
    return b
# ---- wheels ------------------------------------------------------------------------
def wheel(xc, sg, track, width):
    # plain tyre cylinder with rounded shoulders and a shallow rim recess on the outer face
    w = cq.Workplane().add(cq.Solid.makeCylinder(R_TIRE, width, V(0, -width / 2, 0), V(0, 1, 0)))
    w = w.edges().fillet(40).val()
    w = w.cut(cq.Solid.makeCylinder(280, 30, V(0, width / 2 - 25, 0), V(0, 1, 0)))
    if sg < 0:
        w = w.mirror("XZ")
    return w.translate(V(xc, sg * track / 2, ZC))

def wheels():
    return [wheel(XF, 1, TRACK_F, 255), wheel(XF, -1, TRACK_F, 255),
            wheel(XR, 1, TRACK_R, 285), wheel(XR, -1, TRACK_R, 285)]

if __name__ == "__main__":
    import time
    t0 = time.time()
    b = body()
    ws = wheels()
    print("built in", time.time() - t0)
    cq.exporters.export(cq.Workplane().add(b), "out/body.brep") if False else None
    b.exportBrep("out/body.brep")
    for i, w in enumerate(ws):
        w.exportBrep(f"out/wheel_{i}.brep")
    allc = cq.Compound.makeCompound([b] + ws)
    cq.exporters.export(cq.Workplane().add(allc), "out/preview.stl", tolerance=0.8, angularTolerance=0.15)
