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

# ---- longitudinal control curves (measured off the blueprint side / top views) ------
# top centre line: upright nose, hood rising to the cowl, raked screen, long flat roof,
# backlight, deck falling gently to the tail
zt = P([0, 40, 150, 600, 1000, 1300, 1380, 1600, 1850, 2050, 2300, 2600, 3300, 3800, 4000, 4200, 4450, 4630, 4800, 5100, 5300, 5340, 5360],
       [930, 975, 1000, 1050, 1095, 1130, 1160, 1300, 1450, 1560, 1615, 1632, 1632, 1620, 1590, 1480, 1300, 1190, 1165, 1120, 1080, 1050, 1000])
# shoulder: top of the lower body, just under the belt line
zs = P([0, 100, 600, 1300, 2000, 4000, 4600, 5100, 5300, 5360],
       [850, 920, 980, 1045, 1060, 1060, 1050, 1010, 960, 900])
# underside
zb = P([0, 60, 300, 700, 1200, 3800, 4600, 5100, 5300, 5360],
       [260, 235, 210, 185, 180, 180, 195, 235, 265, 290])
# maximum half width of the lower body (plan view, rounded corners front and rear)
hw = P([0, 30, 80, 150, 250, 400, 700, 1600, 2600, 3600, 4200, 4800, 5000, 5150, 5260, 5330, 5360],
       [720, 790, 850, 905, 950, 985, 1000, 995, 990, 995, 1000, 990, 975, 940, 890, 830, 760])
# half width at the top: hood edge / roof rail / deck edge
hwt = P([0, 200, 800, 1300, 1380, 1700, 2100, 2500, 3500, 3900, 4200, 4630, 5000, 5250, 5360],
        [700, 790, 850, 840, 800, 740, 660, 640, 640, 655, 700, 780, 800, 760, 700])

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
    w, wt = float(hw(x)), float(hwt(x))
    dz = max(t - s, 40.0)
    crown = min(0.08 * dz, 45.0) + 8.0
    rail = (wt, t - crown)
    sh = (w - 70, s)
    belt = (sh[0] + 0.12 * (rail[0] - sh[0]), sh[1] + 0.12 * (rail[1] - sh[1]))
    return b, s, t, w, wt, dz, crown, belt, rail

def section_pts(x):
    b, s, t, w, wt, dz, crown, belt, rail = section_geom(x)
    hb = s - b
    # lower body bulges at about door-handle-minus height and leans inward to the shoulder
    verts = [(0.0, b), (w - 40, b), (w, b + 0.45 * hb), (w - 70, s), rail, (0.0, t)]
    radii = [0, 150, 1500, 130, min(0.4 * dz, 140), 0]
    nseg = [3, 5, 3, 6, 4, 5, 6, 5, 6]
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

def cut_all(s, tools):
    return s.cut(*tools) if tools else s

def fuse_all(s, tools):
    return s.fuse(*tools).clean() if tools else s

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

def grille():
    gw, z0, z1 = 515.0, 325.0, 968.0
    frame = cq.Workplane().add(box(0, 140, -gw, gw, z0, z1)).edges("|Y").fillet(18).edges("|X").fillet(10).val()
    frame = frame.cut(box(-1, 32, -gw + 36, gw - 36, z0 + 38, z1 - 38))
    vanes = []
    n = 23
    pitch = (2 * (gw - 36)) / n
    for i in range(n):
        yc = -gw + 36 + pitch * (i + 0.5)
        vanes.append(box(8, 40, yc - 6.5, yc + 6.5, z0 + 38, z1 - 38))
    return fuse_all(frame, vanes)

def mirrors():
    out = []
    for sg in (1, -1):
        m = box(1600, 1790, 880, 1095, 1135, 1250).fuse(box(1620, 1740, 700, 900, 1150, 1200))
        out.append(m if sg > 0 else m.mirror("XZ"))
    return out

def x_surface(y, front=True):
    """Plan-view X of the lower body skin at half-width y (front or rear end)."""
    xs = np.linspace(0, 900, 901) if front else np.linspace(L, L - 900, 901)
    w = hw(xs)
    i = int(np.argmax(w >= y)) if (w >= y).any() else len(xs) - 1
    return X0 + xs[i] * (L - X0) / L

def plan_recess(y0, y1, z0, z1, depth, front=True):
    """Pocket of roughly constant depth into the rounded front/rear corners."""
    ys = np.linspace(y0, y1, 12)
    if front:
        inner = [(x_surface(y) + depth, y) for y in ys]
        poly = [(-20.0, y0)] + inner + [(-20.0, y1)]
    else:
        inner = [(x_surface(y, False) - depth, y) for y in ys]
        poly = [(L + 20.0, y0)] + inner + [(L + 20.0, y1)]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(poly).close().extrude(z1 - z0).val()

def light_recesses():
    t = []
    for sg in (1, -1):
        m = (lambda s: s) if sg > 0 else (lambda s: s.mirror("XZ"))
        t.append(m(plan_recess(556, 900, 748, 852, 45)))            # headlamp slot
        t.append(m(plan_recess(834, 905, 265, 660, 40)))            # vertical air curtain
        t.append(m(plan_recess(0, 815, 905, 990, 22, False)))      # rear lamp top bar
        t.append(m(plan_recess(660, 815, 557, 990, 22, False)))    # rear lamp vertical bar
        t.append(m(plan_recess(462, 720, 300, 360, 45, False)))    # exhaust finisher
    t.append(box(L - 8, L + 10, -650, 650, 600, 895))             # recessed tail panel
    t.append(box(-10, X0 + 8, -480, 480, 270, 312))               # lower intake below grille
    return t

def skin_y(x, z):
    """Half width of the section skin at height z on the outer side (below the roof rail)."""
    pts = [(p.y, p.z) for p in section_pts(x)]
    n = len(pts)
    right = [q for q in pts[:n // 2 + 1] if q[0] >= 0]
    top_i = int(np.argmax([q[0] for q in right]))
    # walk up from the widest point toward the rail / down toward the floor
    lower = sorted(right[:top_i + 1], key=lambda q: q[1])
    upper = sorted(right[top_i:], key=lambda q: q[1])
    seq = upper if z >= right[top_i][1] else lower
    return float(np.interp(z, [q[1] for q in seq], [q[0] for q in seq]))

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
    """Shallow feature-line groove along the side skin, as short straight segments."""
    t = []
    for xa, xb, za, zb_ in zip(xs[:-1], xs[1:], zs_[:-1], zs_[1:]):
        yin = min(skin_y(xa, za), skin_y(xb, zb_), skin_y(0.5 * (xa + xb), 0.5 * (za + zb_))) - depth
        poly = [(xa, za - h / 2), (xb, zb_ - h / 2), (xb, zb_ + h / 2), (xa, za + h / 2)]
        g = xz_prism(poly, yin, yin + 200)
        t += [g, g.mirror("XZ")]
    return t

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
    # rear: lower chrome strip across the bumper
    t.append(box(L - 4, L + 10, -700, 700, 440, 450))
    return t

def plan_band(y0, y1, z0, z1, d0, d1, front=True):
    """Solid between depth d0 and d1 below the rounded front/rear skin (a lamp lens)."""
    ys = np.linspace(y0, y1, 12)
    if front:
        outer = [(x_surface(y) + d0, y) for y in ys]
        inner = [(x_surface(y) + d1, y) for y in reversed(ys)]
    else:
        outer = [(x_surface(y, False) - d0, y) for y in ys]
        inner = [(x_surface(y, False) - d1, y) for y in reversed(ys)]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(outer + inner).close().extrude(z1 - z0).val()

def lamp_lenses():
    t = []
    for sg in (1, -1):
        m = (lambda s: s) if sg > 0 else (lambda s: s.mirror("XZ"))
        t.append(m(plan_band(585, 880, 763, 837, 22, 50)))            # headlamp inner lens
        t.append(m(plan_band(20, 790, 918, 977, 10, 26, False)))      # rear lamp bar lens
        t.append(m(plan_band(675, 800, 575, 975, 10, 26, False)))     # rear lamp upright lens
    return t

def ornament():
    """Stylised hood mascot on the grille shell."""
    base = box(150, 230, -22, 22, 955, 990)
    fig = xz_prism([(165, 985), (215, 985), (205, 1035), (185, 1100), (172, 1095), (180, 1040)], -9, 9)
    wing = cq.Workplane("YZ", origin=(178, 0, 0)).polyline(
        [(-8, 1030), (8, 1030), (38, 1085), (30, 1092), (0, 1060), (-30, 1092), (-38, 1085)]).close().extrude(22).val()
    return base.fuse(fig, wing).clean()

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
    b = cut_all(b, wheel_wells() + rec + light_recesses() + shut_lines() + feature_lines())
    print("lights", b.isValid(), time.time()-T, flush=True)
    b = fuse_all(b, [grille()] + mirrors() + lamp_lenses() + [ornament(), roof_fin()])
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
