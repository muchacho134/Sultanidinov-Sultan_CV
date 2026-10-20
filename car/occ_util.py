import numpy as np
from OCP.gp import gp_Pnt, gp_Vec, gp_Ax1, gp_Ax2, gp_Dir, gp_Trsf, gp_Pln
from OCP.TColgp import TColgp_HArray1OfPnt
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire,
                                BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace,
                                BRepBuilderAPI_Transform)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common, BRepAlgoAPI_Fuse
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepCheck import BRepCheck_Analyzer


def bspline(pts, periodic=False):
    arr = TColgp_HArray1OfPnt(1, len(pts))
    for i, p in enumerate(pts):
        arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    it = GeomAPI_Interpolate(arr, periodic, 1e-6)
    it.Perform()
    return it.Curve()


def wire_from_curve(c):
    return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(c).Edge()).Wire()


def closed_spline_wire(pts):
    return wire_from_curve(bspline(pts, periodic=True))


def face_from_wire(w):
    return BRepBuilderAPI_MakeFace(w, True).Face()


def prism(face, vec):
    return BRepPrimAPI_MakePrism(face, gp_Vec(*vec)).Shape()


def profile_prism(pts2d, plane, a, b):
    """Closed smooth profile in one of the planes 'xz','yz','xy', extruded along the
    remaining axis from a to b."""
    P = []
    for u, v in pts2d:
        if plane == 'xz':
            P.append((u, a, v))
        elif plane == 'yz':
            P.append((a, u, v))
        else:
            P.append((u, v, a))
    f = face_from_wire(closed_spline_wire(P))
    d = {'xz': (0, b - a, 0), 'yz': (b - a, 0, 0), 'xy': (0, 0, b - a)}[plane]
    return prism(f, d)


def cut(a, b):
    op = BRepAlgoAPI_Cut(a, b); op.SetFuzzyValue(1e-4); op.Build()
    assert op.IsDone(); return op.Shape()


def common(a, b):
    op = BRepAlgoAPI_Common(a, b); op.SetFuzzyValue(1e-4); op.Build()
    assert op.IsDone(); return op.Shape()


def fuse(a, b):
    op = BRepAlgoAPI_Fuse(a, b); op.SetFuzzyValue(1e-4); op.Build()
    assert op.IsDone(); return op.Shape()


def volume(s):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g); return g.Mass()


def valid(s):
    return BRepCheck_Analyzer(s).IsValid()


def mirror_y(s):
    t = gp_Trsf(); t.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    return BRepBuilderAPI_Transform(s, t, True).Shape()


def translate(s, v):
    t = gp_Trsf(); t.SetTranslation(gp_Vec(*v))
    return BRepBuilderAPI_Transform(s, t, True).Shape()


def _open_spline_edge(pts):
    from OCP.GC import GC_MakeSegment
    if len(pts) == 2:
        return BRepBuilderAPI_MakeEdge(gp_Pnt(*pts[0]), gp_Pnt(*pts[1])).Edge()
    return BRepBuilderAPI_MakeEdge(bspline(pts, periodic=False)).Edge()


def loop_wire(P, corners=()):
    """Closed wire through 3D points P. Smooth (periodic spline) unless corner indices
    are given, in which case it is split into open spline segments meeting at the corners."""
    P = [tuple(map(float, p)) for p in P]
    if not corners:
        return closed_spline_wire(P)
    cs = sorted(set(c % len(P) for c in corners))
    w = BRepBuilderAPI_MakeWire()
    for k, c0 in enumerate(cs):
        c1 = cs[(k + 1) % len(cs)]
        idx = list(range(c0, c1 + 1)) if c1 > c0 else list(range(c0, len(P))) + list(range(0, c1 + 1))
        w.Add(_open_spline_edge([P[i] for i in idx]))
    return w.Wire()


def outline_prism(pts2d, corners, plane, a, b):
    P = []
    for u, v in pts2d:
        P.append({'xz': (u, a, v), 'yz': (a, u, v), 'xy': (u, v, a)}[plane])
    f = face_from_wire(loop_wire(P, corners))
    d = {'xz': (0, b - a, 0), 'yz': (b - a, 0, 0), 'xy': (0, 0, b - a)}[plane]
    return prism(f, d)
