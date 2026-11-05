"""Build the finished (carved) areas as exact CAD faces for the half car:
floor planes trimmed by the well cylinders, well cylinders down to the floor, slot walls.
Writes a BREP compound + a render with the remaining dough mesh."""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from occ_util import valid, cut, common, fuse
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Pln, gp_Vec
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.BRepTools import BRepTools
m = trimesh.load(sys.argv[1], force='mesh'); lab = np.load(sys.argv[2]); P = json.load(open(sys.argv[3]))
names = json.load(open(sys.argv[2].replace(".npy", "_names.json")))
GAP = {"front": 12.0, "rear": 8.0}
FL = {"front floor plane": (-1950, -1000, 96.8), "main floor plane": (-950, 1700, 114.5)}
c = m.triangles_center
YOUT = 1150.0           # outboard limit for the well tools (body side trims it later)
faces = []              # (name, face)


def outline_xy(sel):
    """Outer boundary of a set of faces, projected to XY, smoothed and resampled."""
    sub = m.submesh([np.where(sel)[0]], append=True)
    paths = sub.outline().discrete
    loop = max(paths, key=lambda p: len(p))[:, :2]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(loop, axis=0), axis=1))]
    t = np.linspace(0, s[-1], max(int(s[-1] / 40), 20), endpoint=False)
    Q = np.c_[[gaussian_filter1d(np.interp(t, s, loop[:, k]), 3, mode='wrap') for k in range(2)]].T
    return Q


# well tools (cylinder from the slot wall outwards), used to trim the floors
wells = []
for k in ("front", "rear"):
    w = P[k]; rw = w["r"] + GAP[k]
    wells.append((w, rw, BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(w["x"], -w["wall"], w["z"]), gp_Dir(0, -1, 0)), rw, YOUT - w["wall"]).Shape()))
# floor faces: smoothed outline of the carved area (half car, y <= 0) clipped at y = 0, minus wells
# floors from straight design lines (idealised, not the mesh outline)
from shapely.geometry import Polygon, box as sbox
D = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else {}
Y_SILL = D.get("y_sill", 825.0)                 # straight outer edge of the main floor
X_FRONT, X_RAMP0, X_RAMP1, X_REAR = D.get("x_front", -1900.0), -1000.0, -950.0, D.get("x_rear", 1750.0)
Y_NOSE = D.get("y_nose", 780.0)                 # outer edge of the front floor ahead of the front well


def chord(w, rw, zf):
    return np.sqrt(max(rw * rw - (w["z"] - zf) ** 2, 0.0))


wf, rwf, _ = wells[0]; wr, rwr, _ = wells[1]
zf1, zf2 = FL["front floor plane"][2], FL["main floor plane"][2]
cf, cr = chord(wf, rwf, zf1), chord(wr, rwr, zf2)
plans = {
    # front floor: inboard of the slot wall from the nose end to the ramp, plus the strip ahead of the well
    "front floor plane": (zf1, Polygon([(X_FRONT, 0), (X_RAMP0, 0), (X_RAMP0, -wf["wall"]), (wf["x"] - cf, -wf["wall"]),
                                        (wf["x"] - cf, -Y_NOSE), (X_FRONT, -Y_NOSE)])),
    # main floor: ramp -> rear end, straight sill edge between the wells, notched by the rear well opening
    "main floor plane": (zf2, Polygon([(X_RAMP1, 0), (X_REAR, 0), (X_REAR, -wr["wall"]), (wr["x"] + cr, -wr["wall"]),
                                       (wr["x"] + cr, -Y_SILL), (X_REAR, -Y_SILL)][:4] +
                                      [(wr["x"] - cr, -wr["wall"]), (wr["x"] - cr, -Y_SILL), (X_RAMP1, -Y_SILL)])),
}
for name, (zf, poly2) in plans.items():
    poly2 = poly2.buffer(0)
    Q = np.array(poly2.exterior.coords)[:-1]
    poly = BRepBuilderAPI_MakePolygon()
    for x, y in Q: poly.Add(gp_Pnt(float(x), float(y), zf))
    poly.Close()
    faces.append((name, BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0, 0, zf), gp_Dir(0, 0, -1)), poly.Wire(), True).Face()))
    print("%-18s outline: %s" % (name, np.round(Q).astype(int).tolist()))
# well walls: ruled between the arc on the slot wall and the arch lip found on the mesh;
# both curves lie on the cylinder and the rulings run along its axis -> exactly the cylinder
from OCP.BRepFill import BRepFill
from OCP.GeomAPI import GeomAPI_PointsToBSpline
from OCP.TColgp import TColgp_Array1OfPnt
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire


def spline_edge(pts):
    arr = TColgp_Array1OfPnt(1, len(pts))
    for i, p in enumerate(pts): arr.SetValue(i + 1, gp_Pnt(*map(float, p)))
    return BRepBuilderAPI_MakeEdge(GeomAPI_PointsToBSpline(arr, 3, 8).Curve()).Edge()


v_all = m.vertices
for (w, rw, cyl), k in zip(wells, ("front", "rear")):
    zf = FL["front floor plane"][2] if k == "front" else FL["main floor plane"][2]
    a0 = np.arcsin(np.clip((zf - w["z"]) / rw, -1, 1))          # angle where the arch meets the floor
    th = np.linspace(np.pi - a0, a0, 121)                         # front foot -> over the top -> rear foot
    # arch lip: outermost |y| of mesh vertices lying on this cylinder, per angle
    vv = v_all[(v_all[:, 1] < 0) & (np.abs(np.hypot(v_all[:, 0] - w["x"], v_all[:, 2] - w["z"]) - rw) < 4)]
    ang = np.arctan2(vv[:, 2] - w["z"], vv[:, 0] - w["x"])
    ylip = np.array([(-vv[np.abs(ang - t) < 0.06, 1]).max() if (np.abs(ang - t) < 0.06).any() else np.nan for t in th])
    ylip = np.interp(np.arange(len(th)), np.where(~np.isnan(ylip))[0], ylip[~np.isnan(ylip)])
    ylip = gaussian_filter1d(ylip, 3, mode='nearest')
    ring = lambda yy: [(w["x"] + rw * np.cos(t), -y_, w["z"] + rw * np.sin(t)) for t, y_ in zip(th, yy)]
    e_in = spline_edge(ring(np.full(len(th), w["wall"])))
    e_out = spline_edge(ring(ylip))
    face = BRepFill.Face_s(e_in, e_out)
    faces.append((f"{k} well cylinder", face))
    print(f"{k}: arch lip |y| {ylip.min():.0f}..{ylip.max():.0f} mm")
    # slot wall: plane y = -wall, bounded by the arc and the floor line
    pts = ring(np.full(len(th), w["wall"]))
    poly = BRepBuilderAPI_MakePolygon()
    for p in pts: poly.Add(gp_Pnt(*map(float, p)))
    poly.Close()
    sw = BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0, -w["wall"], 0), gp_Dir(0, -1, 0)), poly.Wire(), True).Face()   # faces the wheel
    faces.append((f"{k} slot wall plane", sw))
comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
for n_, f in faces:
    bb.Add(comp, f); print("%-20s valid %s" % (n_, valid(f)))
BRepTools.Write_s(comp, sys.argv[4])
json.dump([n_ for n_, _ in faces], open(sys.argv[4].replace(".brep", "_names.json"), "w"))
