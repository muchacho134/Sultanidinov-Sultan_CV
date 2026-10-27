"""Overlay CAD line render (red) on the concept front / rear views at the concept's pixel scale."""
import sys, numpy as np, trimesh
from PIL import Image
sys.path.insert(0, '.')
from render2 import render

L = 5360.0
concept = Image.open(sys.argv[1]).convert("RGB")
mesh = trimesh.load(sys.argv[2], force='mesh')
S = 4
# name, crop (orig px), centre px, ground px, mm/px horizontal, mm/px vertical, camera x, image-right sign
VIEWS = [("front", (75, 25, 455, 268), 262.5, 265, 5.556, 6.97, -12000.0, -1),
         ("rear", (515, 25, 880, 268), 696.25, 265, 5.839, 6.97, L + 12000.0, 1)]
outs = []
for name, (x0, y0, x1, y1), cx, gy, sx, sz, camx, sgn in VIEWS:
    c = concept.crop((x0, y0, x1, y1)).resize(((x1 - x0) * S, (y1 - y0) * S), Image.LANCZOS)
    a, b = (x0 - cx) * sx, (x1 - cx) * sx            # image-right extents in mm
    z0, z1 = (gy - y1) * sz, (gy - y0) * sz
    # world y that lands at the image-left / image-right edges
    ya, yb = (a, b) if sgn > 0 else (-a, -b)
    fit = [(0, ya, z0), (0, yb, z1), (0, ya, z1), (0, yb, z0)]
    tx = 0.0 if camx < 0 else L
    W = 1400; H = round(W * (z1 - z0) / (b - a))
    r = render(mesh, (camx, 0, 815), (tx, 0, 815), size=(W, H), margin=0.0, fit=fit)
    r = np.array(r.resize(c.size, Image.LANCZOS))
    base = np.array(c).astype(float)
    base = 255 - (255 - base) * 0.55                  # fade the concept
    lines = r < 120
    base[lines] = [220, 20, 20]
    outs.append(Image.fromarray(base.astype(np.uint8)))
Wt = sum(o.width for o in outs) + 20
sheet = Image.new("RGB", (Wt, max(o.height for o in outs)), "white")
x = 0
for o in outs:
    sheet.paste(o, (x, 0)); x += o.width + 20
sheet.save(sys.argv[3])
