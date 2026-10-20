import sys, numpy as np
import body as B
from occ_util import *
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.TColgp import TColgp_HArray1OfPnt
from OCP.TColStd import TColStd_HArray1OfReal
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.gp import gp_Pnt


def stations():
    xs = [0, 5, 14, 28, 48, 75, 110, 155, 210, 275, 350]
    xs += list(np.arange(430, 4330, 80))
    xs += [4330, 4380, 4420, 4450, 4472, 4486, B.LENGTH]
    return sorted(set(round(float(x), 2) for x in xs if x <= B.LENGTH))


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


def solve():
    xs = stations()
    loops = {x: B.full_loop(x) for x in xs}
    params = np.mean([chord_params(L) for L in loops.values()], axis=0)
    dz = {x: 0.0 for x in xs}
    curves = {}
    for it in range(4):
        worst = 0
        for x in xs:
            c = interp(B.full_loop(x, dz=dz[x]) if B.canopy_height(x) == 0 else
                       B.full_loop(x, hc=B.canopy_height(x) + dz[x]), params)
            zmax = sample(c)[:, 1].max()
            e = B.SIL(x) - zmax
            dz[x] += e; worst = max(worst, abs(e)); curves[x] = c
        print("silhouette fit iter", it, "max err %.2f mm" % worst)
    return xs, curves


def build():
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
