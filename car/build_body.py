import sys, numpy as np
import body as B
from occ_util import *
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.TColgp import TColgp_HArray1OfPnt
from OCP.TColStd import TColStd_HArray1OfReal
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.gp import gp_Pnt


def stations():
    xs = [0, 18, 45, 85, 135, 195, 265, 345]
    xs += list(np.arange(430, 1300, 80))
    xs += list(np.arange(1300, 3560, 40))      # the side hollow needs dense sections
    xs += list(np.arange(3560, B.LENGTH - 40, 80))
    return sorted(set(round(float(x), 2) for x in xs if x <= B.LENGTH))


TAIL_R = 60.0   # quarter-round on the tail edge
NOSE_R = 30.0   # quarter-round on the nose edge
ROUND_BY_SECTIONS = False   # end rounding breaks the skin (see IMPROVEMENT_PLAN.md)


def offset_loop(L, d):
    """Offset a closed (x, y, z) section loop inwards by d in its plane."""
    P = L[:, 1:]
    n = len(P)
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    nrm = np.c_[t[:, 1], -t[:, 0]]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
    c = P.mean(0)
    if np.mean(np.sum((P - c) * nrm, 1)) < 0:
        nrm = -nrm
    Q = P - d * nrm
    return np.c_[L[:, 0], Q]


def end_loops(base_loop, x0, r, sign):
    """Quarter-round an end: sections beyond x0 (towards sign) shrink like a fillet."""
    out = []
    for k in (0.25, 0.5, 0.75, 1.0):      # evenly spaced rows interpolate stably
        x = x0 + sign * r * k
        L = offset_loop(base_loop, r * (1 - np.sqrt(1 - (0.9 * k) ** 2)))
        L[:, 0] = x
        out.append((x, L))
    return out


def chord_params(P):
    Q = np.r_[P, P[:1]]
    d = np.linalg.norm(np.diff(Q, axis=0), axis=1) ** 0.5   # centripetal
    t = np.r_[0, np.cumsum(d)]
    return t / t[-1]


def interp(P, params):
    arr = TColgp_HArray1OfPnt(1, len(P))
    for i, p in enumerate(P):
        arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    pr = TColStd_HArray1OfReal(1, len(P) + 1)
    for i, v in enumerate(params):
        pr.SetValue(i + 1, float(v))
    it = GeomAPI_Interpolate(arr, pr, True, 1e-6); it.Perform()
    return it.Curve()


def sample(c, n=500):
    us = np.linspace(c.FirstParameter(), c.LastParameter(), n)
    return np.array([[c.Value(u).Y(), c.Value(u).Z()] for u in us])


def solve(extra=(), offset=0.0):
    ends = [B.LENGTH - TAIL_R, NOSE_R]
    # stations crowding the end stations make the interpolation overshoot
    xs = [x for x in stations() + list(extra) if min(abs(x - e) for e in ends) > 30] + ends + [B.LENGTH]
    xs = sorted(set(xs))
    loops = {x: B.full_loop(x) for x in xs}
    params = np.mean([chord_params(L) for L in loops.values()], axis=0)
    dz = {x: 0.0 for x in xs}
    curves = {}
    for it in range(4):
        worst = 0
        for x in xs:
            L = (B.full_loop(x, dz=dz[x]) if B.canopy_height(x) == 0 else
                 B.full_loop(x, hc=B.canopy_height(x) + dz[x]))
            c = interp(L, params)
            if offset and it == 3:
                c = interp(offset_loop(L, -offset), params)
            zmax = sample(c)[:, 1].max()
            e = B.SIL(x) - zmax
            dz[x] += e; worst = max(worst, abs(e)); curves[x] = c
        print("silhouette fit iter", it, "max err %.2f mm" % worst)
    # rounded ends: replace the end stations with shrinking sections
    for x0, r, sign in ((B.LENGTH - TAIL_R, TAIL_R, 1), (NOSE_R, NOSE_R, -1)):
        base = (B.full_loop(x0, hc=B.canopy_height(x0) + dz.get(x0, 0.0)) if B.canopy_height(x0)
                else B.full_loop(x0, dz=dz.get(x0, 0.0)))
        if offset:
            base = offset_loop(base, -offset)
        for x in [x for x in xs if (x - x0) * sign > -1e-6]:
            xs.remove(x); curves.pop(x, None)
        xs.append(x0); curves[x0] = interp(base, params)
        if ROUND_BY_SECTIONS:
            for x, L in end_loops(base, x0, r, sign):
                xs.append(x); curves[x] = interp(L, params)
    xs.sort()
    return xs, curves


SPLIT_X = 2110.0   # extra section mid-cabin (kept for repeatable station sets)


def build(offset=0.0):
    """Body solid: one cubic surface interpolated through the fitted sections
    (a high-degree loft oscillates between sections), periodic faces split.
    offset > 0 grows every section outwards (used for skins laid over the body)."""
    from OCP.ShapeUpgrade import ShapeUpgrade_ShapeDivideClosed
    from OCP.ShapeFix import ShapeFix_Shape
    xs, curves = solve(extra=[SPLIT_X], offset=offset)
    s = build_skin(sorted(set(xs)), curves)
    d = ShapeUpgrade_ShapeDivideClosed(s); d.SetNbSplitPoints(1); d.Perform()
    fx = ShapeFix_Shape(d.Result()); fx.Perform()
    return fx.Shape()


def build_skin(xs, curves, nv=121):
    """Sample every fitted section at common parameters (seam at the bottom centre)
    and approximate one surface through the grid."""
    from skin import skin_solid
    c0 = curves[xs[0]]
    a, b = c0.FirstParameter(), c0.LastParameter()
    # loops start at the top centre; start the grid half way round = bottom centre
    us = a + ((np.linspace(0, 1, nv) + 0.5) % 1.0) * (b - a)
    us[-1] = us[0]
    G = np.array([[[curves[x].Value(u).X(), curves[x].Value(u).Y(), curves[x].Value(u).Z()]
                   for u in us] for x in xs])
    s, surf = skin_solid(G)
    print("skin valid", valid(s), "vol m3 %.3f" % (volume(s) / 1e9),
          "poles %d x %d" % (surf.NbUPoles(), surf.NbVPoles()))
    return s


def build_thrusections():
    xs, curves = solve()
    ts = BRepOffsetAPI_ThruSections(True, False, 1e-4)
    for x in xs:
        ts.AddWire(wire_from_curve(curves[x]))
    ts.Build()
    s = ts.Shape()
    print("loft valid", valid(s), "vol m3 %.3f" % (volume(s) / 1e9))
    return s


if __name__ == "__main__":
    from OCP.BRepTools import BRepTools
    s = build()
    BRepTools.Write_s(s, sys.argv[1] if len(sys.argv) > 1 else "out/body_loft.brep")
