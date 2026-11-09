"""Real-world panel layout for the half car, keeping the STL's features.

Feature recesses are found first (surface sitting > DEPTH mm behind a smoothed envelope); every
remaining face gets a production panel from its direction region and the design landmarks
(hood / windshield line, canopy base, canopy side edge, fastback crease, arch positions).
"""
import sys, json, numpy as np, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from shade import render_sheet, vertex_normals
m = trimesh.load(sys.argv[1], force='mesh'); reg = np.load(sys.argv[2]); P = json.load(open(sys.argv[3]))
C = {k: np.array(v) for k, v in json.load(open(sys.argv[4])).items()}; OUT = sys.argv[5]
DEPTH = 15.0
F, c, A, V = m.faces, m.triangles_center, m.area_faces, m.vertices
half = c[:, 1] <= 5
X, Y, Z = c[:, 0], c[:, 1], c[:, 2]


def yline(curve, x):
    """|y| of a design curve at x (interpolated, held flat beyond its ends)."""
    q = curve[np.argsort(curve[:, 0])]
    return np.interp(x, q[:, 0], -q[:, 1])


# ---- 1. feature recesses: depth behind a Taubin-smoothed envelope
env = m.copy(); trimesh.smoothing.filter_taubin(env, lamb=0.5, nu=-0.53, iterations=60)
depth_v = np.sum((env.vertices - V) * env.vertex_normals, axis=1)   # > 0: surface lies behind the envelope
depth = depth_v[F].mean(1)
rec = half & (depth > DEPTH) & (reg != 5) & (reg != 0)
adj = m.face_adjacency; ok = rec[adj[:, 0]] & rec[adj[:, 1]]
_, comp = connected_components(coo_matrix((np.ones(ok.sum()), (adj[ok, 0], adj[ok, 1])), shape=(len(F), len(F))), directed=False)
panel = np.full(len(F), "", dtype=object)
for cc in np.unique(comp[rec]):
    sel = rec & (comp == cc)
    if A[sel].sum() < 0.008e6: continue
    cx, cz = np.average(X[sel], weights=A[sel]), np.average(Z[sel], weights=A[sel])
    if cx < -1700: name = "front corner intake"
    elif cx > 1850: name = "tail light recess" if cz > 480 else "diffuser opening"
    elif reg[sel].tolist().count(4) > 0.3 * sel.sum() or (-900 < cx < 900): name = "side intake"
    else: name = "recess (other)"
    panel[sel] = name
# feature outlines traced earlier: everything inside them is the pocket (rim, walls and floor)
from matplotlib.path import Path as MP
si = C["side_intake"]; pin = MP(si[:, [0, 2]]).contains_points(np.c_[X, Z], radius=-8)
pin2 = MP(si[:, [0, 2]]).contains_points(np.c_[X, Z], radius=12)        # include the lip all round
panel[half & pin2 & (Y < -620) & (reg != 5) & (reg != 0) & (Z < si[:, 2].max() + 5)] = "side intake"
fi = C["front_corner_intake"]; pin = MP(fi[:, [1, 2]]).contains_points(np.c_[Y, Z], radius=-8)
panel[half & pin & (X < -1850) & (reg != 5) & (reg != 0)] = "front corner intake"
# ---- 2. landmarks
xw0, yc0 = -1400.0, -C["canopy_base"][np.argmin(C["canopy_base"][:, 0])][1]       # windshield base at centre, canopy start |y|
xc0 = C["canopy_base"][:, 0].min()                                                   # canopy front end x (-1620)
hood_y = lambda x: np.where(x < xc0, np.interp(x, [-2040.0, xc0], [656.0, yc0]), yline(C["canopy_base"], x))
x_wind = lambda ay: xw0 + (xc0 - xw0) * np.clip(ay / yc0, 0, 1) ** 2                 # windshield base line, curved
x_fend = P["front"]["x"] + P["front"]["r"] + 120.0                                   # front fender / body-side split
x_quart = P["rear"]["x"] - P["rear"]["r"] - 120.0                                    # body-side / rear quarter split
x_can_end = C["canopy_side_edge"][:, 0].max()
can_y = lambda x: np.where(x <= C["canopy_base"][:, 0].max(), yline(C["canopy_base"], x), yline(C["canopy_side_edge"], x))
x_rear_glass = lambda ay: x_can_end + 220.0 * (1 - np.clip(ay / 634.0, 0, 1) ** 2)  # rear canopy edge, curved
fast_y = lambda x: yline(C["roof_crown_edge"], x)
# shut lines: front one leans forward from the arch up to the A-pillar foot, rear one sits just behind the intake
FRONT_CUT = ([130, 400, 650, 830, 1000], [x_fend, x_fend - 30, x_fend - 110, -1060, -1150])
REAR_CUT = ([130, 400, 650, 800, 1000], [x_quart, x_quart - 20, x_quart - 40, 880, 900])
def side_cut(x, z):
    xf = np.interp(z, *FRONT_CUT); xr = np.interp(z, *REAR_CUT)
    return np.where(x < xf, "front fender", np.where(x > xr, "rear quarter", "body side"))
ay = -Y
todo = half & (panel == "")
# bottom
b = todo & (reg == 0)
panel[b] = np.where(X[b] < -950, "front undertray", np.where(X[b] > 1700, "rear diffuser", "floor"))
panel[todo & (reg == 5)] = "wheel well"
panel[todo & (reg == 2)] = "front fascia"
panel[todo & (reg == 1)] = "tail panel"
# top
t = todo & (reg == 3)
xt, yt = X[t], ay[t]
name = np.array(side_cut(xt, Z[t]), dtype=object)
hood = (xt < x_wind(yt)) & (yt < hood_y(xt))
canopy = (xt >= x_wind(yt)) & (xt < x_rear_glass(yt)) & (yt < can_y(xt))
fast = (xt >= x_rear_glass(yt)) & (yt < fast_y(xt) + 15)
x_roof = lambda ay: -87.0 - 260.0 * np.clip(ay / 600.0, 0, 1) ** 2
name[hood] = "hood"; name[canopy & (xt < x_roof(yt))] = "windshield"; name[canopy & (xt >= x_roof(yt))] = "roof"; name[fast & ~canopy] = "engine cover / fastback"
name[(xt < -1900) & ~hood] = "front fender"
# panels that wrap over a corner are split into their top and side faces (one surface each)
name[name == "front fender"] = "front fender top"; name[name == "rear quarter"] = "rear quarter top"
panel[t] = name
# side: glass = the side-region piece standing above the belt
s = todo & (reg == 4)
ok = s[adj[:, 0]] & s[adj[:, 1]]
_, sc = connected_components(coo_matrix((np.ones(ok.sum()), (adj[ok, 0], adj[ok, 1])), shape=(len(F), len(F))), directed=False)
glass = np.zeros(len(F), bool)
for cc in np.unique(sc[s]):
    sel = s & (sc == cc)
    if np.average(Z[sel], weights=A[sel]) > 850 and A[sel].sum() > 0.05e6: glass |= sel
panel[glass] = "side glass"
s &= ~glass
name = np.array(side_cut(X[s], Z[s]), dtype=object)
name[(Z[s] < 270) & (X[s] > x_fend) & (X[s] < x_quart)] = "sill"
name[X[s] < -1900] = "front bumper corner"; name[X[s] > 1950] = "rear bumper corner"
panel[s] = name
panel[half & (panel == "")] = "body side"
# ledges and ceilings inside the tail face (below the deck edge) belong to the tail panel
tail_ledge = half & (X > 2120) & (Z < 870) & (Z > 300) & np.isin(panel, ["engine cover / fastback", "rear quarter", "rear diffuser"])
panel[tail_ledge] = "tail panel"
# ---- report + render
names = sorted(set(panel[half]))
PAL = {"floor": (0.3, 0.45, 0.85), "front undertray": (0.45, 0.55, 0.95), "rear diffuser": (0.25, 0.35, 0.7),
       "wheel well": (0.35, 0.35, 0.38), "front fascia": (0.35, 0.75, 0.45), "tail panel": (0.9, 0.4, 0.35),
       "hood": (0.95, 0.75, 0.25), "windshield": (0.2, 0.25, 0.32), "roof": (0.5, 0.55, 0.62), "side glass": (0.3, 0.38, 0.48),
       "engine cover / fastback": (0.85, 0.6, 0.2), "front fender": (0.6, 0.85, 0.35), "front fender top": (0.75, 0.92, 0.5), "rear quarter top": (0.98, 0.72, 0.78), "body side": (0.75, 0.55, 0.9),
       "rear quarter": (0.95, 0.55, 0.65), "sill": (0.55, 0.4, 0.75), "front bumper corner": (0.3, 0.65, 0.55),
       "rear bumper corner": (0.8, 0.3, 0.45), "side intake": (0.08, 0.08, 0.1), "front corner intake": (0.1, 0.1, 0.12),
       "tail light recess": (0.75, 0.1, 0.1), "diffuser opening": (0.12, 0.12, 0.14), "recess (other)": (0.5, 0.5, 0.5)}
for n_ in names:
    print("%-28s %5.2f m2" % (n_, A[half & (panel == n_)].sum() / 1e6))
np.save(OUT, panel)
Cf = np.array([PAL.get(p, (1, 0, 1)) if p else (1, 0, 1) for p in panel])
Vf = np.asarray(V, float)
img = OUT.replace(".npy", ".png")
render_sheet(Vf, F[half], Cf[half], img, N=vertex_normals(Vf, F))
from PIL import Image, ImageDraw
im = Image.open(img); W_, H_ = im.size
leg = Image.new("RGB", (W_, 30 * ((len(names) + 3) // 4) + 20), "white"); d = ImageDraw.Draw(leg)
for i, n_ in enumerate(names):
    x0, y0 = 20 + (i % 4) * (W_ // 4), 10 + (i // 4) * 30
    d.rectangle([x0, y0, x0 + 22, y0 + 22], fill=tuple(int(255 * v) for v in PAL.get(n_, (1, 0, 1))), outline="black")
    d.text((x0 + 30, y0 + 5), n_, fill="black")
out = Image.new("RGB", (W_, H_ + leg.size[1]), "white"); out.paste(im, (0, 0)); out.paste(leg, (0, H_)); out.save(img)
