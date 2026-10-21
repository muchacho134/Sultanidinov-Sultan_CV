"""Concept car body: section loft driven by profiles traced from the 2D concept sheet.

Coordinates: X rearward from the nose (mm), Y lateral (+ = left), Z up from the ground.
Side-view keyframes are written in pixels of the reference sheet (side view) and
converted with S mm/px so the side elevation can be checked 1:1 against the drawing.

Half section (y >= 0), from the top centre outwards:
  upper height field  z = base(y) + canopy(y)      0 <= y <= yF
      base   : hood / deck centre zH rising to the shoulder crest zF at yF
      canopy : dome of height Hc and half width Wc sitting on the base
  shoulder arc        (yF, zF) -> (W, zW)          superellipse quadrant
  lower arc           (W, zW)  -> (W - tuck, zB)   superellipse quadrant
  flat floor          -> (0, zB)
"""
import numpy as np
from scipy.interpolate import PchipInterpolator

S = 4.083            # mm per px of the side view (overall length 4500 mm)
PX0, GROUND = 45.0, 361.5


def X(px):
    return (np.asarray(px, float) - PX0) * S


def Z(py):
    return (GROUND - np.asarray(py, float)) * S


def curve(pairs, zpx=False, xpx=True):
    a = np.array(pairs, float)
    xs = X(a[:, 0]) if xpx else a[:, 0]
    vs = Z(a[:, 1]) if zpx else a[:, 1]
    f = PchipInterpolator(xs, vs, extrapolate=False)
    lo, hi = xs[0], xs[-1]
    return lambda x: float(f(np.clip(x, lo, hi)))


LENGTH = float(X(1146))
AXLE_F, AXLE_R = float(X(286)), float(X(996))
WHEEL_Z = float(Z(279.5))
TIRE_R = WHEEL_Z
ARCH_R = TIRE_R + 40

# --- side elevation (px of the sheet) ----------------------------------------
# outer silhouette of the side view (traced): hood/fender crest, windshield, roof, fastback
SIL = curve([(45, 281), (50, 278), (60, 269), (80, 255), (100, 243), (150, 211), (200, 188),
             (250, 172), (300, 164), (340, 164), (370, 167), (385, 165), (400, 157), (420, 148),
             (450, 135), (500, 116), (550, 100), (600, 88), (650, 82), (680, 81), (710, 82),
             (750, 85), (800, 92), (850, 102), (900, 113), (950, 127), (1000, 140), (1050, 151),
             (1100, 166), (1120, 176), (1130, 183), (1140, 196), (1146, 212)], zpx=True)
# shoulder crest: front fender crest -> belt (glass bottom) -> rear haunch crest
zF = curve([(45, 281), (50, 278), (60, 269), (80, 255), (100, 243), (150, 211), (200, 188),
            (250, 172), (300, 164), (340, 164), (380, 168), (440, 177), (495, 181),
            (600, 178), (700, 174), (800, 170), (880, 165), (950, 156), (1000, 151),
            (1050, 153), (1100, 166), (1120, 176), (1130, 183), (1146, 212)], zpx=True)
yF = curve([(45, 240), (50, 360), (60, 460), (80, 560), (100, 625), (150, 705), (200, 765),
            (250, 805), (300, 820), (350, 815), (400, 790), (450, 770), (520, 760),
            (700, 760), (800, 770), (880, 795), (1000, 805), (1100, 780), (1146, 700)])
# hood / deck centreline under the canopy (front: hood well between the fenders)
zH = curve([(45, 285), (100, 252), (150, 224), (200, 204), (250, 190), (300, 182),
            (350, 177), (380, 175), (400, 176), (430, 179), (495, 181), (600, 178), (700, 174),
            (800, 170), (880, 165), (950, 156), (1000, 151), (1050, 153), (1100, 168),
            (1130, 186), (1146, 212)], zpx=True)
# canopy half width at its foot
Wc = curve([(370, 470), (400, 540), (450, 610), (520, 660), (650, 690), (780, 680),
            (850, 640), (920, 560), (980, 450), (1040, 330), (1100, 240), (1146, 200)])
# underside
zB = curve([(45, 338), (52, 340), (100, 342), (200, 345), (380, 344), (900, 344), (1080, 344),
            (1095, 342), (1115, 336), (1132, 322), (1146, 292)], zpx=True)
# --- plan ---------------------------------------------------------------------
W = curve([(45, 300), (48, 420), (55, 540), (65, 640), (80, 740), (100, 830), (150, 950),
           (200, 1015), (250, 1040), (286, 1046), (330, 1040), (380, 1012), (450, 978),
           (600, 972), (800, 990), (900, 1030), (996, 1046), (1060, 1040), (1100, 1012),
           (1125, 965), (1146, 880)])
zW = curve([(0, 220), (300, 420), (700, 600), (984, 650), (1400, 600), (2000, 540),
            (3000, 570), (3883, 690), (4300, 620), (4495, 450)], xpx=False)
TUCK = curve([(0, 60), (500, 140), (4000, 150), (4495, 110)], xpx=False)

N_TOP, N_CAN, N_SH, N_LO, N_FL = 16, 8, 16, 14, 5


def cosspace(a, b, n, end=True):
    t = (1 - np.cos(np.linspace(0, np.pi, n + (0 if end else 1)))) / 2
    v = a + (b - a) * t
    return v if end else v[:-1]


def g_dome(t, a=3.0, b=1.6):   # flat crown, tangent foot
    t = np.clip(np.abs(t), 0, 1)
    return (1 - t ** a) ** b


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def upper_z(x, y, hc):
    yf = yF(x)
    zf, zh = zF(x), min(zH(x), zF(x))
    base = zh + (zf - zh) * smoothstep(y / yf)
    return base + hc * g_dome(y / (1.12 * Wc(x)))


def canopy_height(x):
    """Dome height so that the centre reaches the traced silhouette (if it is above crest)."""
    zh = min(zH(x), zF(x))
    return max(0.0, SIL(x) - zh) if SIL(x) > zF(x) + 0.5 else 0.0


def half_profile(x, hc=None, dz=0.0):
    if hc is None:
        hc = canopy_height(x)
    yf, zf, w, zw, zb = yF(x), zF(x) + dz, W(x), zW(x), zB(x)
    zw = float(np.clip(zw, zb + 40, zf - 60))
    wc = min(1.12 * Wc(x), 0.97 * yf)
    ys = np.r_[cosspace(0, wc, N_CAN, end=False), cosspace(wc, yf, N_TOP - N_CAN)]
    pts = [(y, upper_z(x, y, hc) + dz * smoothstep(y / yf)) for y in ys]
    # shoulder: superellipse quadrant centred (yf, zw)
    n1 = 2.0   # elliptical shoulder
    th = np.linspace(0, np.pi / 2, N_SH + 1)[1:]
    for t in th:
        pts.append((yf + (w - yf) * np.sin(t) ** (2 / n1), zw + (zf - zw) * np.cos(t) ** (2 / n1)))
    tuck = TUCK(x)
    yb = w - tuck
    n2 = 1.7   # side leans in progressively toward the floor
    for t in np.linspace(0, np.pi / 2, N_LO + 1)[1:]:
        pts.append((yb + tuck * np.cos(t) ** (2 / n2), zw - (zw - zb) * np.sin(t) ** (2 / n2)))
    for y in np.linspace(yb, 0, N_FL + 1)[1:]:
        pts.append((y, zb))
    pts = np.array(pts)
    if X(340) < x < X(890):
        outer = pts[:, 0] > 0.9 * yf
        for i in np.where(outer)[0]:
            # never push a point inboard of the floor corner (would fold the section)
            pts[i, 0] -= min(cove(x, pts[i, 1]), 0.85 * max(pts[i, 0] - yb, 0.0))
    return pts


# --- side cove: the lower side between the wheels sits inboard of the shoulder crease
# and ends at the rear against the "sail" line, where the haunch steps out.
COVE_TOP = curve([(350, 222), (390, 232), (500, 224), (600, 214), (700, 204), (800, 193),
                  (870, 182), (900, 178)], zpx=True)
_sail = np.array([(833, 140), (872, 175), (868, 195), (855, 215), (830, 239), (795, 263),
                  (745, 288), (690, 312), (640, 332), (600, 350)], float)
_sail_z, _sail_x = Z(_sail[::-1, 1]), X(_sail[::-1, 0])
COVE_D = 62.0


def sail_x(z):
    return float(np.interp(z, _sail_z, _sail_x))


def cove(x, z):
    front = smoothstep((x - X(352)) / (X(440) - X(352)))
    rear = 1 - smoothstep((x - X(800)) / (X(885) - X(800)))
    top = smoothstep((COVE_TOP(x) - z) / 80)
    bot = smoothstep((z - 70) / 110)
    depth = COVE_D * (0.65 + 0.35 * smoothstep((x - X(450)) / (X(800) - X(450))))
    return depth * front * rear * top * bot


def full_loop(x, **kw):
    h = half_profile(x, **kw)
    loop = np.r_[h, h[-2:0:-1] * [-1, 1]]
    # start at the bottom centre so the loft seam runs along the underside
    loop = np.roll(loop, -(len(h) - 1), axis=0)
    return np.c_[np.full(len(loop), x), loop]
