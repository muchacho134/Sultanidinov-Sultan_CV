import sys, numpy as np, trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from render2 import render

L = 5360.0
concept = Image.open(sys.argv[1]).convert("L")
mesh = trimesh.load(sys.argv[2], force='mesh')
out = sys.argv[3]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f_big = ImageFont.truetype(FONT, 34); f_mid = ImageFont.truetype(FONT, 24); f_small = ImageFont.truetype(FONT, 18)

def roi(x0, x1, y0, y1, z0, z1):
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]

# (title, concept crop box, camera kwargs)
VIEWS = [
    ("Side view", (892, 30, 1712, 268), dict(pos=(2680, -12000, 815), target=(2680, 0, 815))),
    ("Front view", (62, 25, 462, 270), dict(pos=(-12000, 0, 815), target=(0, 0, 815))),
    ("Rear view", (508, 25, 888, 270), dict(pos=(L + 12000, 0, 815), target=(L, 0, 815))),
    ("Top view", (45, 358, 615, 612), dict(pos=(2680, 0, 12000), target=(2680, 0, 0), up=(0, 1, 0))),
    ("Front 3/4", (632, 378, 1262, 628), dict(pos=(-6200, -9500, 3000), target=(2500, 0, 650), persp=True)),
    ("Rear 3/4", (1272, 385, 1745, 628), dict(pos=(L + 7500, -6200, 2900), target=(3000, 0, 650), persp=True)),
]
DETAILS = [
    ("Front grille", (1052, 693, 1220, 803), dict(pos=(-1700, -1500, 1150), target=(60, -560, 760), persp=True,
                                                    fit=roi(0, 250, -330, -960, 600, 990))),
    ("Headlight", (1235, 693, 1402, 803), dict(pos=(-1500, -1500, 1050), target=(100, -720, 800), persp=True,
                                                 fit=roi(0, 330, -520, -960, 700, 900))),
    ("Rear light", (1418, 693, 1584, 803), dict(pos=(L + 1500, -1900, 1150), target=(L - 60, -720, 800), persp=True,
                                                  fit=roi(L - 260, L, -560, -1000, 520, 1060))),
]

def pair(crop, cam, width, ss=2):
    c = concept.crop(crop)
    h = round(width * c.height / c.width)
    c = c.resize((width, h), Image.LANCZOS)
    r = render(mesh, size=(width * ss, h * ss), margin=0.05, **cam).resize((width, h), Image.LANCZOS)
    return c, r

PAD, GAP, LABEL = 30, 24, 44
cells = []
for title, crop, cam in VIEWS:
    print(title, flush=True)
    cells.append((title, *pair(crop, cam, 900)))
dcells = []
for title, crop, cam in DETAILS:
    print(title, flush=True)
    dcells.append((title, *pair(crop, cam, 290)))

W = PAD * 2 + 900 * 2 + GAP
H = PAD + 60 + sum(LABEL + c[1].height + GAP for c in cells) + LABEL + 40 + max(d[1].height for d in dcells) + PAD + 40
sheet = Image.new("L", (W, H), 250)
d = ImageDraw.Draw(sheet)
d.text((PAD, PAD), "Concept", font=f_big, fill=30)
d.text((PAD + 900 + GAP, PAD), "CAD model (luxury_saloon_mm.step)", font=f_big, fill=30)
y = PAD + 60
for title, c, r in cells:
    d.text((PAD, y + 8), title, font=f_mid, fill=60)
    y += LABEL
    sheet.paste(c, (PAD, y)); sheet.paste(r, (PAD + 900 + GAP, y))
    d.rectangle((PAD, y, PAD + 899, y + c.height - 1), outline=200)
    d.rectangle((PAD + 900 + GAP, y, PAD + 1799 + GAP, y + r.height - 1), outline=200)
    y += c.height + GAP
d.text((PAD, y + 8), "Details  (concept | CAD)", font=f_mid, fill=60)
y += LABEL
x = PAD
for title, c, r in dcells:
    sheet.paste(c, (x, y)); sheet.paste(r, (x + 290 + 6, y))
    d.text((x, y + c.height + 6), title, font=f_small, fill=70)
    x += 2 * 290 + 6 + 30
sheet.save(out)
print("saved", out, sheet.size)
