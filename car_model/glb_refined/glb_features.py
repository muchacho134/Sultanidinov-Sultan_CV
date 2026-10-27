"""Crisp front / rear (traced off the concept) and simple wheels + mirrors on the refined GLB body.
Tools are built as CAD solids (CadQuery), tessellated, and applied with exact mesh booleans."""
import sys, math, numpy as np, trimesh, manifold3d as mf
import cadquery as cq
from cadquery import Vector as V
from scipy.interpolate import RegularGridInterpolator
sys.path.insert(0, '.')
from glb_ends import to_manifold, from_manifold

L = 5360.0
st = np.load("out/hull_ends.npz")
_FI = {k: RegularGridInterpolator((st['zs' + k], st['ys' + k]), np.nan_to_num(st['F' + k], nan=1e5),
                                  bounds_error=False, fill_value=1e5) for k in ('f', 'r')}

# concept front/rear-view coordinates -> this body
SY = 0.976
def zf(z):  return 168.0 + (z - 120.0) * (920.0 - 168.0) / (965.0 - 120.0)    # front: ground line .. grille top
def zr(z):  return 216.0 + (z - 150.0) * (1094.0 - 216.0) / (1115.0 - 150.0)  # rear: ground line .. deck edge

def x_surface(y, z, front=True):
    d = float(_FI['f' if front else 'r']([[z, abs(y)]])[0])
    return d if front else L - d

def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def yz_prism(poly, x0, x1):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(poly).close().extrude(x1 - x0).val()

def xz_prism(pts, y0, y1):
    return cq.Workplane("XZ", origin=(0, y0, 0)).polyline(pts).close().extrude(-(y1 - y0)).val()

def rrect(y0, y1, z0, z1, r, n=5):
    r = min(r, 0.49 * (y1 - y0), 0.49 * (z1 - z0))
    pts = []
    for cy, cz, a0 in ((y1 - r, z0 + r, -90), (y1 - r, z1 - r, 0), (y0 + r, z1 - r, 90), (y0 + r, z0 + r, 180)):
        for j in range(n + 1):
            a = math.radians(a0 + 90 * j / n)
            pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def F(poly):  return [(y * SY, zf(z)) for y, z in poly]     # map a concept front-view outline
def Rr(poly): return [(y * SY, zr(z)) for y, z in poly]     # map a concept rear-view outline

def skin_region(y0, y1, z0, z1, d0, d1, front=True, nz=6, ny=24):
    sg = 1 if front else -1
    wires = []
    for z in np.linspace(z0, z1, nz):
        ys = np.linspace(y0, y1, ny)
        outer = [(x_surface(y, z, front) + sg * d0, y) for y in ys]
        inner = [(x_surface(y, z, front) + sg * d1, y) for y in ys[::-1]]
        wires.append(cq.Wire.makePolygon([V(x, y, z) for x, y in outer + inner], close=True))
    return cq.Solid.makeLoft(wires, ruled=True)

def pocket(poly, depth, front=True, d0=-30.0):
    ys = [p[0] for p in poly]; zs = [p[1] for p in poly]
    reg = skin_region(min(ys) - 5, max(ys) + 5, min(zs) - 5, max(zs) + 5, d0, depth, front)
    x0, x1 = (-100, 900) if front else (L - 900, L + 100)
    return reg.intersect(yz_prism(poly, x0, x1))

def layer(poly, d0, d1, front=True):
    return pocket(poly, d1, front, d0)

def mir(shapes):
    return shapes + [t.mirror("XZ") for t in shapes]

def hexagon_exhaust(inset=0.0):
    pts = [(470, 335), (800, 335), (788, 250), (522, 240), (470, 300)]
    cy = sum(p[0] for p in pts) / 5; cz = sum(p[1] for p in pts) / 5
    return [(cy + (y - cy) * (1 - inset), cz + (z - cz) * (1 - inset)) for y, z in pts]

# ---- front -------------------------------------------------------------------------
XG = 4.0                                    # grille front plane (the GLB's own grille face)
def grille():
    zc = lambda y, top: top - 25 * (y / 545.0) ** 2
    ys = np.linspace(-545, 545, 23)
    outer = F([(545, 340)] + [(y, zc(y, 965)) for y in ys[::-1]] + [(-545, 340)])
    yi = np.linspace(-495, 495, 23)
    inner = F([(495, 365)] + [(y, zc(y, 908)) for y in yi[::-1]] + [(-495, 365)])
    top = zf(965)
    shell = yz_prism(outer, XG, 620)
    # the shell's top runs back and up into the hood instead of leaving a flat ledge
    wedge = xz_prism([(XG - 5, 0), (XG - 5, top), (XG + 60, top + 22), (300, top + 55), (640, top + 95), (640, 0)], -700, 700)
    shell = shell.intersect(wedge)
    shell = shell.cut(yz_prism(inner, XG - 1, XG + 40))
    bars = []
    for k in range(-8, 9):
        w2, xf = (11, 4) if k == 0 else (8, 10)
        y = 55 * k * SY
        bars.append(box(XG + xf, XG + 42, y - w2, y + w2, zf(360), zf(960)))
    bars = cq.Compound.makeCompound(bars).intersect(yz_prism(inner, XG, XG + 45))
    return shell.fuse(bars).clean()

def grille_inner():
    zc = lambda y, top: top - 25 * (y / 545.0) ** 2
    yi = np.linspace(-495, 495, 23)
    return F([(495, 365)] + [(y, zc(y, 908)) for y in yi[::-1]] + [(-495, 365)])

def front_cuts():
    t = [yz_prism(grille_inner(), -60, XG + 40)]                            # vane pocket through the nose
    t += mir([pocket(F(rrect(563, 910, 740, 862, 32)), 40)])                # headlamp housing
    t += mir([pocket(F(rrect(825, 911, 280, 690, 34)), 12),                 # intake surround
              pocket(F(rrect(843, 893, 300, 670, 22)), 55)])                # intake opening
    t.append(pocket(F(rrect(-500, 500, 205, 338, 18)), 28))                 # lower grille band
    t += mir([pocket(F([(553, 345), (559, 345), (567, 735), (561, 735)]), 4)])   # bumper pod line
    return t

def front_adds():
    t = [grille()]
    t += mir([layer(F(rrect(583, 890, 760, 842, 22)), 16, 45)])             # headlamp inner lens
    t += mir([layer(F(rrect(600, 895, 185, 203, 8)), -5, 12)])              # chrome lower-corner strip
    t.append(layer(F(rrect(-480, 480, 282, 292, 4)), 10, 30))               # lower band slats
    t.append(layer(F(rrect(-480, 480, 242, 252, 4)), 10, 30))
    return t

# ---- rear --------------------------------------------------------------------------
def rear_cuts():
    t = []
    ubar = [(842, 545), (842, 990), (-842, 990), (-842, 545), (-671, 545), (-671, 910), (671, 910), (671, 545)]
    t.append(pocket(Rr(ubar), 30, False))                                   # tail lamp housing
    t.append(pocket(Rr(rrect(-660, 660, 640, 905, 12)), 7, False))          # recessed centre panel
    t.append(pocket(Rr(rrect(-905, 905, 499, 505, 2)), 4, False))           # bumper crease
    t.append(pocket(Rr(rrect(-790, 790, 190, 350, 30)), 22, False))         # diffuser band
    t += mir([pocket(Rr(hexagon_exhaust()), 60, False)])                    # exhausts
    t += mir([pocket(Rr([(677, 990), (683, 990), (683, 1070), (677, 1070)]), 4, False)])  # boot lid line
    return t

def rear_adds():
    t = []
    guide = [(800, 572), (800, 962), (-800, 962), (-800, 572), (-772, 572), (-772, 940), (772, 940), (772, 572)]
    t.append(layer(Rr(guide), 12, 34, False))                               # light guide inside the lamp
    ring = layer(Rr(hexagon_exhaust(-0.06)), 14, 30, False).cut(pocket(Rr(hexagon_exhaust(0.08)), 70, False))
    t += mir([ring])                                                        # exhaust surrounds
    return t

# ---- wheels, arches, mirrors (simple) --------------------------------------------------
WHEELS = (903.0, 4155.0); R_T = 362.0; ZW = R_T + 4.0; TRACK = 1630.0; W_T = 270.0; R_ARCH = 410.0

def wheel(xc, sg):
    w = cq.Workplane().add(cq.Solid.makeCylinder(R_T, W_T, V(0, -W_T / 2, 0), V(0, 1, 0))).edges().fillet(38).val()
    w = w.cut(cq.Solid.makeCylinder(255, 28, V(0, W_T / 2 - 24, 0), V(0, 1, 0)))
    w = w.fuse(cq.Solid.makeCylinder(70, 20, V(0, W_T / 2 - 30, 0), V(0, 1, 0)))
    if sg < 0:
        w = w.mirror("XZ")
    return w.translate(V(xc, sg * TRACK / 2, ZW))

def arch_cuts():
    return [cq.Solid.makeCylinder(R_ARCH, 700, V(xc, sg * 600, ZW), V(0, sg, 0)) for xc in WHEELS for sg in (1, -1)]

def mirrors():
    out = []
    for sg in (1, -1):
        m = box(1940, 2160, 860, 1025, 1040, 1160).fuse(box(1965, 2085, 700, 880, 1060, 1110))
        out.append(m if sg > 0 else m.mirror("XZ"))
    return out

def tess(shapes, tol=0.25):
    out = []
    for s in shapes:
        vs, fs = s.tessellate(tol, 0.15)
        m = trimesh.Trimesh(np.array([v.toTuple() for v in vs]), np.array(fs), process=True)
        trimesh.repair.fix_normals(m)
        out.append(m)
    return out

def union_all(ms):
    M = None
    for m in ms:
        k = to_manifold(m)
        M = k if M is None else M + k
    return M

if __name__ == "__main__":
    import time
    T = time.time()
    body = to_manifold(trimesh.load("out/glb_hull_dec.stl"))
    cuts = tess(front_cuts() + rear_cuts())          # arches come from the GLB itself
    adds = tess(front_adds() + rear_adds() + mirrors())
    print("tools", len(cuts), len(adds), round(time.time() - T, 1), flush=True)
    for i, m in enumerate(cuts + adds):
        if not m.is_watertight:
            print("  non-watertight tool", i, flush=True)
    B = body - union_all(cuts)
    B = B + union_all(adds)
    b = from_manifold(B)
    print("body", len(b.faces), "watertight", b.is_watertight, "volume", round(b.volume / 1e9, 3), round(time.time() - T, 1), flush=True)
    b.export("out/glb_refined_body.stl")
    ws = tess([wheel(xc, sg) for xc in WHEELS for sg in (1, -1)])
    for i, w in enumerate(ws):
        w.export(f"out/glb_wheel_{i}.stl")
    allm = trimesh.util.concatenate([b] + ws)
    allm.export("out/glb_refined.stl")
    print("done", round(time.time() - T, 1))
