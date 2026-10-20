"""Body skin as one approximated B-spline surface (light enough for fast booleans),
closed with planar end caps and sewn into a solid."""
import numpy as np
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCP.GeomAbs import GeomAbs_C2
from OCP.gp import gp_Pnt, gp_Pln, gp_Dir
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing,
                                BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeEdge,
                                BRepBuilderAPI_MakeWire)
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shape
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopoDS import TopoDS


def _area(f):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    g = GProp_GProps(); BRepGProp.SurfaceProperties_s(f, g); return g.Mass()


def skin_solid(grid, tol=0.3):
    """grid: (n_u, n_v, 3) points; rows are closed section loops (last == first)."""
    nu, nv, _ = grid.shape
    arr = TColgp_Array2OfPnt(1, nu, 1, nv)
    for i in range(nu):
        for j in range(nv):
            arr.SetValue(i + 1, j + 1, gp_Pnt(*map(float, grid[i, j])))
    from OCP.Approx import Approx_Centripetal
    api = GeomAPI_PointsToBSplineSurface()
    api.Interpolate(arr, Approx_Centripetal)
    surf = api.Surface()
    u0, u1, v0, v1 = surf.Bounds()
    sew = BRepBuilderAPI_Sewing(0.05)
    sew.Add(BRepBuilderAPI_MakeFace(surf, 1e-6).Face())
    for u in (u0, u1):
        # planar cap bounded by the surface's own end iso-curve
        iso = surf.UIso(u)
        w = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(iso).Edge()).Wire()
        x = iso.Value(iso.FirstParameter()).X()
        pln = gp_Pln(gp_Pnt(x, 0, 0), gp_Dir(1, 0, 0))   # exact end plane
        cap = BRepBuilderAPI_MakeFace(pln, w, True).Face()
        if _area(cap) > 1e8 or _area(cap) < 0:     # wire came out inside-out
            cap = BRepBuilderAPI_MakeFace(pln, TopoDS.Wire_s(w.Reversed()), True).Face()
        sew.Add(cap)
    sew.Perform()
    e = TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL)
    solid = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(e.Current())).Solid()
    fx = ShapeFix_Solid(solid); fx.Perform()
    f2 = ShapeFix_Shape(fx.Solid()); f2.Perform()
    return f2.Shape(), surf
