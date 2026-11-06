"""Write a wire network (json of point lists) to STEP as B-spline edges."""
import sys, json, numpy as np
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakePolygon
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
W = json.load(open(sys.argv[1])); comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
for k, pts in W.items():
    pts = np.array(pts)
    keep = np.r_[True, np.linalg.norm(np.diff(pts, axis=0), axis=1) > 0.5]
    pts = pts[keep]
    if len(pts) < 2: continue
    if len(pts) <= 6:                                   # straight-segment wire (openings)
        pl = BRepBuilderAPI_MakePolygon()
        for p in pts: pl.Add(gp_Pnt(*map(float, p)))
        bb.Add(comp, pl.Wire()); continue
    arr = TColgp_Array1OfPnt(1, len(pts))
    for i, p in enumerate(pts): arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    try:
        bb.Add(comp, BRepBuilderAPI_MakeEdge(GeomAPI_PointsToBSpline(arr, 3, 8).Curve()).Edge())
    except Exception:
        pl = BRepBuilderAPI_MakePolygon()
        for p in pts: pl.Add(gp_Pnt(*map(float, p)))
        bb.Add(comp, pl.Wire()); print("polyline fallback:", k)
w = STEPControl_Writer(); w.Transfer(comp, STEPControl_AsIs); print(w.Write(sys.argv[2]))
