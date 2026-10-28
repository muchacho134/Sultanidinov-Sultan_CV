import sys, trimesh
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '.')
from render2 import render

L = 5360.0
m = trimesh.load(sys.argv[1])
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
shots = [
    ("Grille into hood (front 3/4)", dict(pos=(-1900, -2300, 1700), target=(150, 0, 850), persp=True,
        fit=[(0, -700, 600), (0, 700, 600), (0, -700, 1050), (600, 700, 1050), (600, -700, 1050)])),
    ("Grille into hood (side)", dict(pos=(400, -6000, 950), target=(400, 0, 900), persp=True,
        fit=[(-50, -600, 650), (900, -600, 650), (-50, -600, 1150), (900, -600, 1150)])),
    ("Tail lamps (rear)", dict(pos=(L + 6000, 0, 800), target=(L, 0, 800), persp=True,
        fit=[(L, -950, 450), (L, 950, 450), (L, -950, 1100), (L, 950, 1100)])),
    ("Tail lamps (rear 3/4)", dict(pos=(L + 2200, -2600, 1500), target=(L - 150, -200, 750), persp=True,
        fit=[(L - 400, -980, 450), (L, 900, 450), (L - 400, -980, 1150), (L, 900, 1150)])),
    ("Underside", dict(pos=(2680, 0, -12000), target=(2680, 0, 0), up=(1, 0, 0))),
]
cells = []
for title, cam in shots:
    im = render(m, size=(1600, 1000), margin=0.04, **cam).resize((800, 500), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.text((10, 8), title, font=FONT, fill=20)
    cells.append(im)
sheet = Image.new("L", (1620, 1540), 250)
for k, im in enumerate(cells):
    sheet.paste(im, ((k % 2) * 820, (k // 2) * 515))
sheet.save(sys.argv[2])
print("saved", sys.argv[2])
