"""Review sheet: whole-car views + close-ups, and a surface-roughness heat map (deviation of the
surface from a smoothed copy of itself, seen from top / side / front / rear)."""
import sys, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
sys.path.insert(0, '.')
from render2 import render
from depthmap import depth_map

L = 5360.0
m = trimesh.load(sys.argv[1])
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, len(t) * 11 + 16, 30), fill=255); d.text((8, 4), t, font=FONT, fill=20); return im

shots = [
 ("1 front 3/4", dict(pos=(-6200, -9500, 3000), target=(2500, 0, 650), persp=True)),
 ("2 rear 3/4", dict(pos=(L + 7500, -6200, 2900), target=(3000, 0, 650), persp=True)),
 ("3 side", dict(pos=(2680, -12000, 800), target=(2680, 0, 800))),
 ("4 top", dict(pos=(2680, 0, 12000), target=(2680, 0, 0), up=(0, 1, 0))),
 ("5 nose corner / headlamp", dict(pos=(-1300, -2300, 1250), target=(250, -650, 750), persp=True,
     fit=[(0, -980, 450), (500, -980, 450), (0, -450, 1050), (500, -450, 1050)])),
 ("6 hood + windscreen base", dict(pos=(-1500, -1600, 2600), target=(900, 0, 1000), persp=True,
     fit=[(100, -800, 950), (100, 800, 950), (1900, -800, 1250), (1900, 800, 1250)])),
 ("7 A-pillar / mirror / roof", dict(pos=(1000, -4000, 2600), target=(2400, -500, 1200), persp=True,
     fit=[(1600, -1050, 950), (3300, -1050, 950), (1600, -400, 1560), (3300, -400, 1560)])),
 ("8 C-pillar / boot lid", dict(pos=(6500, -3200, 2800), target=(4500, -300, 1150), persp=True,
     fit=[(3800, -950, 950), (L, -950, 950), (3800, 300, 1560), (L, 300, 1200)])),
 ("9 rear panel / lamps", dict(pos=(L + 3000, -1200, 1000), target=(L, -100, 750), persp=True,
     fit=[(L, -950, 450), (L, 900, 450), (L, -950, 1100), (L, 900, 1100)])),
 ("10 rear corner / quarter", dict(pos=(L + 900, -2600, 900), target=(L - 300, -800, 650), persp=True,
     fit=[(L - 700, -990, 300), (L, -500, 300), (L - 700, -990, 1100), (L, -500, 1100)])),
 ("11 front wheel arch / sill", dict(pos=(900, -4200, 700), target=(1300, -900, 450), persp=True,
     fit=[(300, -980, 190), (2400, -980, 190), (300, -980, 1000), (2400, -980, 1000)])),
 ("12 front lower bumper", dict(pos=(-2500, -1200, 500), target=(50, -200, 350), persp=True,
     fit=[(0, -950, 190), (0, 950, 190), (0, -950, 700), (300, 950, 700)])),
]
cells = []
for t, cam in shots:
    print(t, flush=True)
    im = render(m, size=(1400, 860), margin=0.03, **cam).resize((700, 430), Image.LANCZOS).convert("RGB")
    cells.append(lab(im, t))
sheet = Image.new("RGB", (1420, 6 * 440 + 10), (250, 250, 250))
for k, im in enumerate(cells):
    sheet.paste(im, ((k % 2) * 715, (k // 2) * 440))
sheet.save(sys.argv[2])

# ---- roughness: |surface - smoothed surface| from four views ----------------------------------
def rough(order, sign, ra, rb, xref, sigma_mm=30.0):
    mv = trimesh.Trimesh(m.vertices[:, order], m.faces, process=False)
    A, B, D = depth_map(mv, sign, ra, rb, 4.0, xref)
    valid = np.isfinite(D)
    w = valid.astype(float)
    s = sigma_mm / 4.0
    sm = ndimage.gaussian_filter(np.where(valid, D, 0), s) / np.maximum(ndimage.gaussian_filter(w, s), 1e-6)
    gy, gx = np.gradient(np.where(valid, D, 0), 4.0)
    ok = valid & ndimage.binary_erosion(valid, iterations=3) & (np.hypot(gx, gy) < 1.0)
    r = np.where(ok, np.abs(D - sm), np.nan)
    return A, B, D, r
views = [("TOP", [2, 0, 1], -1, (0, L), (-1000, 1000), 1800.0, False),
         ("LEFT SIDE", [1, 0, 2], 1, (0, L), (0, 1600), -1200.0, True),
         ("FRONT", [0, 1, 2], 1, (-1000, 1000), (0, 1600), -100.0, True),
         ("REAR", [0, 1, 2], -1, (-1000, 1000), (0, 1600), L + 100.0, True)]
panels = []
stats = []
for name, order, sign, ra, rb, xref, flip in views:
    A, B, D, r = rough(order, sign, ra, rb, xref)
    base = np.where(np.isfinite(D), 200, 250).astype(float)
    rgb = np.dstack([base, base, base])
    rr = np.nan_to_num(r, nan=0)
    t = np.clip((rr - 1.0) / 5.0, 0, 1)                 # 1 mm .. 6 mm -> yellow .. red
    hot = rr > 1.0
    rgb[hot] = np.c_[np.full(hot.sum(), 240), 220 * (1 - t[hot]), 40 * (1 - t[hot])]
    if flip:
        rgb = rgb[::-1]
    im = Image.fromarray(rgb.astype(np.uint8))
    sc = 0.5 if name in ("TOP", "LEFT SIDE") else 0.9
    im = im.resize((int(im.width * sc), int(im.height * sc)))
    panels.append(lab(im, name + "  (yellow 1 mm ... red 6+ mm ripple)"))
    stats.append((name, np.nanpercentile(r, 95), np.nansum(r > 2) * 16 / 100))
H = panels[0].height + panels[1].height + max(panels[2].height, panels[3].height) + 30
W = max(panels[0].width, panels[2].width + panels[3].width + 20)
heat = Image.new("RGB", (W, H), (255, 255, 255))
heat.paste(panels[0], (0, 0)); heat.paste(panels[1], (0, panels[0].height + 10))
y = panels[0].height + panels[1].height + 20
heat.paste(panels[2], (0, y)); heat.paste(panels[3], (panels[2].width + 20, y))
heat.save(sys.argv[3])
for s in stats:
    print("roughness %-9s p95 %.1f mm, area over 2 mm %.0f cm2" % s)
