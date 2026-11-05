"""Stage 2: main body skin from the wrapped mesh.

Sections every DX mm along X -> outer envelope traced by rays from the section centre
(recesses temporarily filled; they are cut back later) -> left/right averaged and smoothed
-> wheel zones bridged from clean neighbouring sections -> one cubic B-spline surface through
all sections, closed with planar end caps -> solid.
"""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from skin import skin_solid
from occ_util import valid, volume

STL, OUT = sys.argv[1], sys.argv[2]
PARTS = json.load(open(sys.argv[3]))
m = trimesh.load(STL, force='mesh')
DX, NRAY = 40.0, 90                       # station spacing, rays per half (top centre -> bottom centre)
X0, X1 = m.bounds[0, 0] + 12, m.bounds[1, 0] - 12
xs = np.r_[np.arange(X0, X1, DX), X1]
th = np.linspace(np.pi / 2, -np.pi / 2, NRAY)        # angle in the y-z plane, measured from +y


def envelope(x):
    s = m.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0])
    if s is None:
        return None
    segs = []
    for e in s.discrete:
        segs.append(np.c_[e[:-1, 1:], e[1:, 1:]])      # (y0, z0, y1, z1)
    S = np.vstack(segs)
    zc = 0.5 * (S[:, [1, 3]].min() + S[:, [1, 3]].max())
    R = np.full((2, NRAY), np.nan)
    for side, sg in enumerate((1, -1)):
        for k, t in enumerate(th):
            d = np.array([sg * np.cos(t), np.sin(t)])           # ray direction (y, z)
            p, q = S[:, :2] - [0, zc], S[:, 2:] - [0, zc]
            e_ = q - p
            den = d[0] * e_[:, 1] - d[1] * e_[:, 0]
            with np.errstate(divide='ignore', invalid='ignore'):
                u = (p[:, 0] * e_[:, 1] - p[:, 1] * e_[:, 0]) / den       # distance along the ray
                v = (p[:, 0] * d[1] - p[:, 1] * d[0]) / den               # position on the segment
            ok = (u > 0) & (v >= 0) & (v <= 1)
            if ok.any():
                R[side, k] = u[ok].max()                                   # farthest hit = envelope
    return zc, np.nanmean(R, axis=0)                                       # left/right averaged


rows = []
for x in xs:
    r = envelope(x)
    rows.append((x, *r) if r is not None else None)
xs = np.array([r[0] for r in rows if r is not None])
ZC = np.array([r[1] for r in rows if r is not None])
RR = np.array([r[2] for r in rows if r is not None])
print("stations", len(xs), "x %.0f..%.0f" % (xs[0], xs[-1]))

# bridge the wheel zones: below the axle height, outboard of the slot wall, replace the
# section by a linear blend between the clean sections just outside the wheel window
for lab in ("front", "rear"):
    w = PARTS[lab]
    half = w["r"] + 60.0
    i0 = np.searchsorted(xs, w["x"] - half) - 1
    i1 = np.searchsorted(xs, w["x"] + half)
    for i in range(i0 + 1, i1):
        a = (xs[i] - xs[i0]) / (xs[i1] - xs[i0])
        for k, t in enumerate(th):
            y = RR[i, k] * np.cos(t); z = ZC[i] + RR[i, k] * np.sin(t)
            if z < w["z"] + 40 and y > w["wall"] - 20:
                RR[i, k] = (1 - a) * RR[i0, k] + a * RR[i1, k] + ((1 - a) * ZC[i0] + a * ZC[i1] - ZC[i]) * np.sin(t)
    print(f"bridged {lab} wheel zone: stations {i0 + 1}..{i1 - 1}")

# denoise: light smoothing around each section and between neighbouring sections
RR = gaussian_filter1d(RR, 1.0, axis=1, mode='nearest')
RR = gaussian_filter1d(RR, 0.8, axis=0, mode='nearest')
ZC = gaussian_filter1d(ZC, 0.8, mode='nearest')

# closed section loops (start at the bottom centre so the surface seam runs along the floor)
grid = []
for i, x in enumerate(xs):
    yh = RR[i] * np.cos(th); zh = ZC[i] + RR[i] * np.sin(th)
    half = np.c_[yh, zh]                                     # top centre (+y side) -> bottom centre
    loop = np.r_[half[::-1], (half[1:-1] * [-1, 1])]          # bottom centre -> +y side -> top -> -y side
    loop[0, 0] = loop[NRAY - 1, 0] = 0.0
    loop = np.r_[loop, loop[:1]]
    grid.append(np.c_[np.full(len(loop), x), loop])
G = np.array(grid)
s, surf = skin_solid(G)
print("skin valid", valid(s), "vol m3 %.3f (mesh 6.424)" % (volume(s) / 1e9), "poles %d x %d" % (surf.NbUPoles(), surf.NbVPoles()))
from OCP.ShapeUpgrade import ShapeUpgrade_ShapeDivideClosed
from OCP.ShapeFix import ShapeFix_Shape
d = ShapeUpgrade_ShapeDivideClosed(s); d.SetNbSplitPoints(1); d.Perform()
fx = ShapeFix_Shape(d.Result()); fx.Perform(); s = fx.Shape()
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
an = BOPAlgo_ArgumentAnalyzer(); an.SetShape1(s); an.SelfInterMode = True; an.Perform()
print("final valid", valid(s), "self-intersections", an.HasFaulty())
from OCP.BRepTools import BRepTools
BRepTools.Write_s(s, OUT)
np.savez(OUT.replace(".brep", "_sections.npz"), xs=xs, ZC=ZC, RR=RR, th=th)
