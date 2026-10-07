import math
from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Circ, gp_Pln, gp_Ax1
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet2d
from OCP.GC import GC_MakeArcOfCircle
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_VERTEX, TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.TopTools import TopTools_ListOfShape

Y0 = 0.0
YDIR = gp_Dir(0, 1, 0)
def P(x, z, y=Y0): return gp_Pnt(x, y, z)

def unify(s):
    u = ShapeUpgrade_UnifySameDomain(s, True, True, True); u.Build(); return u.Shape()
def fuse(a, b): return BRepAlgoAPI_Fuse(a, b).Shape()
def cut(a, b): return BRepAlgoAPI_Cut(a, b).Shape()
def common(a, b): return BRepAlgoAPI_Common(a, b).Shape()
def fuse_many(shapes):
    if len(shapes) == 1: return shapes[0]
    f = BRepAlgoAPI_Fuse(); a = TopTools_ListOfShape(); t = TopTools_ListOfShape()
    a.Append(shapes[0])
    for s in shapes[1:]: t.Append(s)
    f.SetArguments(a); f.SetTools(t); f.SetFuzzyValue(1e-5); f.Build()
    assert f.IsDone()
    return f.Shape()
def cut_many(base, tools):
    f = BRepAlgoAPI_Cut(); a = TopTools_ListOfShape(); t = TopTools_ListOfShape()
    a.Append(base)
    for s in tools: t.Append(s)
    f.SetArguments(a); f.SetTools(t); f.SetFuzzyValue(1e-5); f.Build()
    assert f.IsDone()
    return f.Shape()

def one_face(s):
    e = TopExp_Explorer(s, TopAbs_FACE); f = TopoDS.Face_s(e.Current()); e.Next()
    assert not e.More(), 'expected a single face'
    return f

# ---- 2D (XZ plane at Y=0) primitives ----
def plane_face(wire):
    from OCP.ShapeFix import ShapeFix_Face
    f = BRepBuilderAPI_MakeFace(gp_Pln(P(0, 0), YDIR), wire, True).Face()
    sf = ShapeFix_Face(f); sf.Perform()
    return TopoDS.Face_s(sf.Face())
def circle_face(cx, cz, r):
    c = gp_Circ(gp_Ax2(P(cx, cz), YDIR), r)
    return plane_face(BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(c).Edge()).Wire())
def poly_face(pts):
    pg = BRepBuilderAPI_MakePolygon()
    for x, z in pts: pg.Add(P(x, z))
    pg.Close()
    return plane_face(pg.Wire())
def rect_face(x0, z0, x1, z1): return poly_face([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])
def stadium_face(p0, p1, r):
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0; L = math.hypot(dx, dz); nx, nz = -dz / L * r, dx / L * r
    f = poly_face([(x0 + nx, z0 + nz), (x1 + nx, z1 + nz), (x1 - nx, z1 - nz), (x0 - nx, z0 - nz)])
    return one_face(unify(fuse(fuse(f, circle_face(x0, z0, r)), circle_face(x1, z1, r))))

def arc_edge(c, r, a, b):
    """minor arc of circle centre c radius r from point a to point b"""
    mx, mz = (a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1]
    L = math.hypot(mx, mz); m = (c[0] + mx / L * r, c[1] + mz / L * r)
    return BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(*a), P(*m), P(*b)).Value()).Edge()
def line_edge(a, b): return BRepBuilderAPI_MakeEdge(P(*a), P(*b)).Edge()
def path_face(segs):
    w = BRepBuilderAPI_MakeWire()
    for s in segs: w.Add(s)
    return plane_face(w.Wire())

def fillet_at(face, pts, r, tol=0.05):
    f2 = BRepFilletAPI_MakeFillet2d(face)
    done = 0
    e = TopExp_Explorer(face, TopAbs_VERTEX); seen = []
    while e.More():
        v = TopoDS.Vertex_s(e.Current()); p = BRep_Tool.Pnt_s(v)
        for (x, z) in pts:
            if abs(p.X() - x) < tol and abs(p.Z() - z) < tol and not any(v.IsSame(s) for s in seen):
                f2.AddFillet(v, r); seen.append(v); done += 1
        e.Next()
    if done != len(pts):
        vs=[]; e = TopExp_Explorer(face, TopAbs_VERTEX)
        while e.More():
            p = BRep_Tool.Pnt_s(TopoDS.Vertex_s(e.Current())); vs.append((round(p.X(),3), round(p.Z(),3))); e.Next()
        raise AssertionError(('fillet vertices found', done, 'expected', pts, 'have', sorted(set(vs))))
    f2.Build(); assert f2.IsDone()
    return f2.Shape()

def prism(face, y0, y1):
    from OCP.gp import gp_Trsf
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    t = gp_Trsf(); t.SetTranslation(gp_Vec(0, y0 - Y0, 0))
    f = BRepBuilderAPI_Transform(face, t, True).Shape()
    return BRepPrimAPI_MakePrism(f, gp_Vec(0, y1 - y0, 0)).Shape()
def box(x0, y0, z0, x1, y1, z1): return BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, z0), gp_Pnt(x1, y1, z1)).Shape()

def line_circle(theta_line, off, R):
    """point on line parallel to direction theta at signed perpendicular offset, where it meets circle R (forward side)"""
    d = (math.cos(theta_line), math.sin(theta_line)); n = (-d[1], d[0])
    t = math.sqrt(R * R - off * off)
    return (d[0] * t + n[0] * off, d[1] * t + n[1] * off)

# ---------------- part 270 ----------------
YF, YB, YPAD, YLUG, YPOCK, YCAV = -75.4, -82.8, -85.4, -92.8, -81.3, -76.4
def build_270():
    # main plate: rectangle + R55 half disc
    outline = one_face(unify(fuse(rect_face(-87.69, -55, 0, 55), circle_face(0, 0, 55))))
    body = prism(outline, YB, YF)
    adds = []
    for s in (1, -1):
        adds.append(box(-87.69, YPAD, 45 * s, -56.29, YB, 55 * s))       # corner pads
        adds.append(box(-87.69, YPAD, 31.9 * s, -73.39, YB, 39.9 * s))   # side pads
    # lugs: profile in YZ, extruded along X
    from OCP.gp import gp_Trsf
    for s in (1, -1):
        lug = box(-57.29, -89.8, min(30 * s, 39.9 * s), -51.39, YB, max(30 * s, 39.9 * s))
        lug = fuse(lug, box(-57.29, YLUG, min(33 * s, 37 * s), -51.39, -89.8, max(33 * s, 37 * s)))
        for zc in (33 * s, 37 * s):
            cyl = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-57.29, -89.8, zc), gp_Dir(1, 0, 0)), 3.0, 5.9).Shape()
            cyl = common(cyl, box(-58, -95, min(30 * s, 39.9 * s), -50, -80, max(30 * s, 39.9 * s)))
            lug = fuse(lug, cyl)
        adds.append(lug)
    body = unify(fuse_many([body] + adds))

    tools = []
    # 4 mounting holes R2.1
    for x in (-81.59, -63.19):
        for z in (50, -50):
            tools.append(prism(circle_face(x, z, 2.1), -86.5, -74.5))
    # lug cross holes R1.35 (axis X)
    for z in (35, -35):
        tools.append(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-58.5, -89.1, z), gp_Dir(1, 0, 0)), 1.35, 8.5).Shape())

    # ring of 8 openings between R37.5 and R52, spokes 2 mm wide every 45 deg; left bridge at 180 deg
    deg = math.pi / 180
    def wedge(a0, a1):  # area between spoke a0 (offset +1) and spoke a1 (offset -1), a0<a1
        # intersection of the two offset lines
        d0 = (math.cos(a0), math.sin(a0)); n0 = (-d0[1], d0[0])
        d1 = (math.cos(a1), math.sin(a1)); n1 = (-d1[1], d1[0])
        # solve p = n0*1 + d0*t = -n1*1 + d1*u
        ax, az = n0[0] + n1[0], n0[1] + n1[1]
        det = d0[0] * (-d1[1]) - d0[1] * (-d1[0])
        t = (-ax * (-d1[1]) - (-az) * (-d1[0])) / det
        p = (n0[0] + d0[0] * t, n0[1] + d0[1] * t)
        far = 100; am = (a0 + a1) / 2
        return poly_face([p, (n0[0] + d0[0] * far, n0[1] + d0[1] * far), (far * 1.5 * math.cos(am), far * 1.5 * math.sin(am)),
                          (-n1[0] + d1[0] * far, -n1[1] + d1[1] * far)])
    ann = lambda r0, r1: one_face(cut(circle_face(0, 0, r1), circle_face(0, 0, r0)))
    for k in range(8):
        a0, a1 = k * 45 * deg, (k + 1) * 45 * deg
        if k in (3, 4):
            continue
        f = one_face(unify(common(ann(37.5, 52), wedge(a0, a1))))
        pts = [line_circle(a0, 1, 52), line_circle(a1, -1, 52)]
        f = fillet_at(f, pts, 3.0)
        tools.append(prism(f, -84, -74))
    for s in (1, -1):   # the two openings next to the 180 deg bridge
        a = 135 * deg if s > 0 else 225 * deg
        hp = rect_face(-60, 9.5 * s, 0, 60 * s)
        d = (math.cos(a), math.sin(a)); n = (-d[1], d[0]); off = 1 if s > 0 else -1
        # half-plane on the 180-deg side of the spoke
        side = poly_face([(n[0] * off + d[0] * -100, n[1] * off + d[1] * -100), (n[0] * off + d[0] * 100, n[1] * off + d[1] * 100),
                          (n[0] * off * 200 + d[0] * 100, n[1] * off * 200 + d[1] * 100), (n[0] * off * 200 - d[0] * 100, n[1] * off * 200 - d[1] * 100)])
        f = one_face(unify(common(common(ann(41, 52), side), hp)))
        zr = 9.5 * s
        pts = [line_circle(a, off, 52), line_circle(a, off, 41),
               (-math.sqrt(52 ** 2 - zr ** 2), zr), (-math.sqrt(41 ** 2 - zr ** 2), zr)]
        f = fillet_at(f, pts, 3.0)
        tools.append(prism(f, -84, -74))

    # through slots R2.05 (8x, radial 27.5..32.5)
    angs = [k * 45 * deg for k in range(8)]
    for a in angs:
        c0 = (27.5 * math.cos(a), 27.5 * math.sin(a)); c1 = (32.5 * math.cos(a), 32.5 * math.sin(a))
        tools.append(prism(stadium_face(c0, c1, 2.05), -84, -74))

    # centre pocket (floor at Y=-81.3) with 8 slot bosses R3.5, opened to the left window
    cf = (-28.47, 19.49); T1 = (-25.93, 21.1); T2 = (-30.94, 21.19); T3 = (-35.95, 10.65)
    cw = (-42.19, 12.5); T4 = (-42.19, 6.0); T5 = (-51.65, 6.0)
    mir = lambda p: (p[0], -p[1])
    segs = [arc_edge(cf, 3, T1, T2), arc_edge((0, 0), 37.5, T2, T3), arc_edge(cw, 6.5, T3, T4),
            line_edge(T4, T5), line_edge(T5, mir(T5)), line_edge(mir(T5), mir(T4)),
            arc_edge(mir(cw), 6.5, mir(T4), mir(T3)), arc_edge((0, 0), 37.5, mir(T3), mir(T2)),
            arc_edge(mir(cf), 3, mir(T2), mir(T1)), line_edge(mir(T1), (-22.98, -22.98)),
            line_edge((-22.98, -22.98), (0, 0)), line_edge((0, 0), (-22.98, 22.98)), line_edge((-22.98, 22.98), T1)]
    W = path_face(segs)
    pocket = unify(fuse(circle_face(0, 0, 32.5), W))
    bosses = [stadium_face((27.5 * math.cos(a), 27.5 * math.sin(a)), (32.5 * math.cos(a), 32.5 * math.sin(a)), 3.5) for a in angs]
    pocket = unify(cut_many(pocket, bosses))
    # pocket = main region + 180-deg island hole -> still one face with an inner wire
    pf = one_face(pocket)
    fpts = []
    for a in angs:
        if abs(a - math.pi) < 1e-6: continue
        for off in (3.5, -3.5):
            p = line_circle(a, off, 32.5)
            if math.hypot(p[0] + 32.5, p[1]) < math.hypot(line_circle(a, -off, 32.5)[0] + 32.5, line_circle(a, -off, 32.5)[1]) and abs(a - 135 * deg) < 1e-6:
                continue
            if abs(a - 135 * deg) < 1e-6 or abs(a - 225 * deg) < 1e-6:
                q = line_circle(a, -off, 32.5)
                if math.hypot(p[0] + 32.5, p[1]) < math.hypot(q[0] + 32.5, q[1]):
                    continue
            fpts.append(p)
    pf = fillet_at(pf, fpts, 3.0)
    tools.append(prism(pf, YPOCK, -74))
    # left window (through) - top 1 mm is shorter
    tools.append(box(-54.69, -84, -6, -39.69, YCAV, 6))
    tools.append(box(-51.65, YCAV - 0.01, -6, -39.69, -74, 6))
    out = unify(cut_many(body, tools))
    return out
