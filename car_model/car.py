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
XF, WB = 905.0, 3300.0
XR = XF + WB                    # 4205
TRACK_F, TRACK_R = 1620.0, 1630.0
R_TIRE = 392.0                  # ~785 mm tyre (255/40 R22 class)
ZC = R_TIRE + 4.0               # 4 mm ground gap, like the reference
R_ARCH = 455.0
X0 = 50.0                       # body skin starts here; grille stands proud to X=0

def P(xs, ys):
    return PchipInterpolator(np.array(xs, float), np.array(ys, float))

# ---- longitudinal control curves -------------------------------------------------
# top centre line: blunt nose -> long flat hood -> raked screen -> flat roof -> fastback-ish C pillar -> deck
zt = P([0, 40, 150, 700, 1350, 1480, 1700, 1950, 2200, 2450, 2800, 3500, 3800, 4050, 4300, 4520, 4650, 4950, 5250, 5330, 5360],
       [940, 985, 1012, 1028, 1050, 1075, 1215, 1405, 1545, 1608, 1630, 1628, 1612, 1540, 1385, 1205, 1125, 1105, 1090, 1070, 1040])
# shoulder / waist (widest point of the section, just under the belt line)
zs = P([0, 60, 400, 1400, 2100, 4000, 4600, 5100, 5300, 5360],
       [860, 900, 935, 975, 1030, 1040, 1010, 975, 930, 900])
# underside
zb = P([0, 60, 250, 600, 4700, 5100, 5300, 5360],
       [270, 215, 180, 165, 165, 190, 240, 275])
# half width of the lower body (plan view)
hw = P([0, 40, 150, 350, 700, 4600, 5000, 5220, 5320, 5360],
       [905, 935, 972, 993, 1000, 1000, 992, 965, 925, 895])
# half width at the top surface (hood crown edge / roof rail / deck edge)
hwt = P([0, 300, 1350, 1480, 1800, 2300, 2800, 3700, 4100, 4550, 4700, 5100, 5360],
        [760, 810, 845, 835, 760, 690, 680, 680, 700, 800, 830, 820, 760])

N_STATIONS = 30
def stations():
    # denser at both ends where the shape changes fastest
    t = np.linspace(0, 1, N_STATIONS)
    s = t - 0.06 * np.sin(2 * np.pi * t)
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

def section_pts(x):
    b, s, t = float(zb(x)), float(zs(x)), float(zt(x))
    w, wt = float(hw(x)), float(hwt(x))
    dz = max(t - s, 40.0)
    crown = min(0.06 * dz, 28.0) + 6.0
    hb = s - b
    shelf = w - min(0.22 * (w - wt), 75.0)
    verts = [(0.0, b), (w - 45, b), (w, b + 0.33 * hb), (w, s), (shelf, s + 0.12 * dz), (wt, t - crown), (0.0, t)]
    radii = [0, 95, 400, 40, 60, min(0.42 * dz, 105), 0]
    nseg = [4, 5, 4, 4, 3, 3, 2, 3, 5, 4, 5]
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
    """Daylight openings: three panes per side (front door, rear door, quarter)."""
    panes = [(1640, 2935), (3015, 3905), (3965, 4440)]
    out = []
    for xa, xb in panes:
        xs = np.linspace(xa, xb, 40)
        top = [float(zt(x)) - 70 for x in xs]
        bot = [float(zs(x)) + 0.12 * max(float(zt(x) - zs(x)), 40) + 22 for x in xs]
        pts = [(x, z) for x, z, zb_ in zip(xs, top, bot) if z - zb_ > 25]
        if len(pts) < 3:
            continue
        xs_ok = [p[0] for p in pts]
        poly = pts + [(x, float(zs(x)) + 0.12 * max(float(zt(x) - zs(x)), 40) + 22) for x in reversed(xs_ok)]
        out.append(poly)
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
        s, t, w, wt = float(zs(xm)), float(zt(xm)), float(hw(xm)), float(hwt(xm))
        dz = t - s
        a = np.array([w - min(0.22 * (w - wt), 75.0), s + 0.12 * dz])
        bpt = np.array([wt, t - 0.12 * dz])
        d = (bpt - a) / np.linalg.norm(bpt - a)
        n = np.array([d[1], -d[0]])
        if n[0] < 0: n = -n
        p = a + 0.35 * (bpt - a) - depth * n
        for sg in (1, -1):
            pr = xz_prism(poly, 300, 1300)
            hs = halfspace_x_axis(p, n)
            tool = pr.intersect(hs)
            tools.append(tool if sg > 0 else tool.mirror("XZ"))
    for xa, xb, fwd in ((1560, 2240, True), (3900, 4480, False)):
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
    gw, z0, z1 = 470.0, 330.0, 975.0
    frame = cq.Workplane().add(box(0, 140, -gw, gw, z0, z1)).edges("|Y").fillet(18).edges("|X").fillet(10).val()
    frame = frame.cut(box(-1, 32, -gw + 38, gw - 38, z0 + 40, z1 - 40))
    vanes = []
    n = 21
    pitch = (2 * (gw - 38)) / n
    for i in range(n):
        yc = -gw + 38 + pitch * (i + 0.5)
        vanes.append(box(8, 40, yc - 6.5, yc + 6.5, z0 + 40, z1 - 40))
    frame = fuse_all(frame, vanes)
    return frame

def mirrors():
    out = []
    for sg in (1, -1):
        m = box(1650, 1850, 880, 1080, 1150, 1270)
        out.append(m if sg > 0 else m.mirror("XZ"))
    return out

def light_recesses():
    t = []
    # headlamps: slim horizontal slots, plus vertical air curtains below
    for sg in (1, -1):
        y0, y1 = 545.0, 865.0
        t.append(box(-10, X0 + 75, *sorted((sg * y0, sg * y1)), 790, 850))
        t.append(box(-10, X0 + 60, *sorted((sg * 770, sg * 845)), 360, 690))
        # rear lamp frame: top bar + vertical bars
        t.append(box(L - 22, L + 10, *sorted((sg * 0, sg * 845)), 955, 1000))
        t.append(box(L - 22, L + 10, *sorted((sg * 795, sg * 845)), 600, 1000))
        # exhaust finishers
        t.append(box(L - 45, L + 10, *sorted((sg * 330, sg * 610)), 315, 350))
        # door shut-lines and handle pockets
    t.append(box(L - 10, L + 10, -300, 300, 690, 900))     # plate panel
    return t

def shut_lines():
    t = []
    for xl in (1610, 2975, 3690):
        for sg in (1, -1):
            zt_ = float(zs(xl)) + 8
            t.append(box(xl - 2.5, xl + 2.5, *sorted((sg * (float(hw(xl)) - 6), sg * 1200)), 240, zt_))
    for xh in (2450, 3440):
        for sg in (1, -1):
            t.append(box(xh, xh + 170, *sorted((sg * (float(hw(xh)) - 6), sg * 1200)), 965, 990))
    return t

def body():
    import time; T=time.time()
    b = body_loft()
    print("loft", b.isValid(), time.time()-T, flush=True)
    rec = glass_recesses(b)
    b = cut_all(b, wheel_wells() + rec + light_recesses() + shut_lines())
    print("lights", b.isValid(), time.time()-T, flush=True)
    b = fuse_all(b, [grille()] + mirrors())
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
