"""Target ("goal") illustration for the concept car: side, front and rear views drawn as
shaded vectors on the exact traced profile, showing the intended treatments:
soft sculpted side scoop, sculpted front fascia, finished rear.

Coordinates are pixels of the original concept sheet; each view is scaled into the canvas.
Writes goal.svg and rasterises goal.png with headless Chromium.
"""
import subprocess, sys
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "renders/goal"


def smooth(pts, closed=False, move=True):
    """Catmull-Rom through pts as cubic Beziers (SVG path data)."""
    P = np.array(pts, float)
    if closed:
        P = np.r_[P[-1:], P, P[:2]]
    else:
        P = np.r_[P[:1], P, P[-1:]]
    d = ("M %.1f %.1f " % tuple(P[1])) if move else ""
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        d += "C %.1f %.1f %.1f %.1f %.1f %.1f " % (*c1, *c2, *p2)
    return d + ("Z" if closed else "")


def mirror(half, cx):
    """half: from the top centre outwards and down to the bottom centre (x < cx side)."""
    return half + [(2 * cx - x, y) for x, y in reversed(half[1:-1])]


# ----------------------------------------------------------------------------- side view
SIL = [(45, 281), (50, 278), (60, 269), (80, 255), (100, 243), (150, 211), (200, 188),
       (250, 172), (300, 164), (340, 164), (370, 167), (385, 165), (400, 157), (420, 148),
       (450, 135), (500, 116), (550, 100), (600, 88), (650, 82), (680, 81), (710, 82),
       (750, 85), (800, 92), (850, 102), (900, 113), (950, 127), (1000, 140), (1050, 151),
       (1100, 166), (1120, 176), (1132, 186), (1142, 202)]
TAIL = [(1142, 202), (1147, 225), (1148, 260), (1144, 292), (1132, 318), (1110, 336), (1085, 344)]
WF, WR, WZ, TR, AR = 286.0, 996.0, 279.5, 82.0, 92.0
FOOT = 346.0


def arch(cx):
    dx = np.sqrt(AR ** 2 - (FOOT - WZ) ** 2)
    return cx + dx, cx - dx


def side_body():
    rf, lf = arch(WF)
    rr, lr = arch(WR)
    d = smooth(SIL + TAIL[1:])
    d += "L %.1f %.1f " % (rr, FOOT)
    d += "A %.1f %.1f 0 1 0 %.1f %.1f " % (AR, AR, lr, FOOT)
    d += "L %.1f %.1f " % (rf, FOOT)
    d += "A %.1f %.1f 0 1 0 %.1f %.1f " % (AR, AR, lf, FOOT)
    d += smooth([(lf, FOOT), (150, 345), (90, 343), (55, 340), (46, 335), (50, 312), (44, 290), (45, 281)],
                move=False) + "Z"
    return d


GLASS = ([(382, 171)] + [(x, y + 5) for x, y in SIL if 395 <= x <= 820] +
         [(826, 120), (833, 133), (822, 140), (760, 148), (700, 156), (640, 163), (580, 169),
          (520, 174), (450, 176), (395, 174)])
SHOULDER = [(120, 232), (200, 199), (300, 176), (380, 181), (480, 192), (600, 192),
            (720, 184), (820, 175), (900, 166), (980, 156), (1050, 158), (1110, 178), (1138, 200)]
DISH = [(372, 268), (400, 252), (470, 238), (560, 222), (660, 206), (760, 192), (830, 186),
        (858, 194), (850, 222), (820, 256), (775, 284), (710, 304), (620, 318), (520, 326),
        (440, 324), (395, 306), (375, 288)]
DUCT = [(640, 236), (720, 219), (790, 208), (822, 210), (812, 234), (780, 262), (730, 283),
        (670, 294), (636, 286), (628, 260)]
LIP = [(380, 262), (470, 240), (600, 218), (720, 200), (820, 188), (852, 194)]
INTAKE_S = [(47, 290), (100, 287), (138, 282), (126, 298), (110, 313), (90, 325), (68, 331),
            (48, 333), (56, 312)]
LAMP_S = [(50, 284), (90, 272), (130, 259), (165, 246)]
SILL = [(372, 342), (450, 334), (600, 330), (760, 330), (860, 334), (905, 342)]


def wheel(cx):
    spokes = ""
    for k in range(5):
        a = np.radians(90 + 72 * k)
        a2 = a + np.radians(30)
        x1, y1 = cx + 22 * np.cos(a), WZ - 22 * np.sin(a)
        x2, y2 = cx + 66 * np.cos(a2), WZ - 66 * np.sin(a2)
        mx, my = cx + 52 * np.cos(a + 0.25), WZ - 52 * np.sin(a + 0.25)
        spokes += ('<path d="M %.1f %.1f Q %.1f %.1f %.1f %.1f" stroke="url(#spoke)" stroke-width="9" '
                   'stroke-linecap="round" fill="none"/>' % (x1, y1, mx, my, x2, y2))
    return f'''
  <circle cx="{cx}" cy="{WZ}" r="{AR - 1}" fill="#0b0c0e"/>
  <circle cx="{cx}" cy="{WZ}" r="{TR}" fill="#16181b"/>
  <circle cx="{cx}" cy="{WZ}" r="{TR - 4}" fill="none" stroke="#2b2e33" stroke-width="2"/>
  <circle cx="{cx}" cy="{WZ}" r="70" fill="url(#rim)"/>
  {spokes}
  <circle cx="{cx}" cy="{WZ}" r="14" fill="#8d939b"/>
  <circle cx="{cx}" cy="{WZ}" r="70" fill="none" stroke="#9aa1a9" stroke-width="1.5" opacity=".6"/>'''


def side_view():
    body = side_body()
    return f'''
 <g id="side">
  <ellipse cx="596" cy="352" rx="600" ry="16" fill="#000" opacity=".28" filter="url(#b12)"/>
  {wheel(WF)}{wheel(WR)}
  <clipPath id="sideclip"><path d="{body}"/></clipPath>
  <path d="{body}" fill="url(#bodyV)"/>
  <g clip-path="url(#sideclip)">
    <!-- soft sculpted dish: the surface dives in, no hard edge -->
    <path d="{smooth(DISH, True)}" fill="url(#dish)" filter="url(#b6)"/>
    <path d="{smooth(LIP)}" stroke="#ffffff" stroke-width="7" fill="none" opacity=".85" filter="url(#b3)"/>
    <path d="{smooth([(x, y + 9) for x, y in LIP])}" stroke="#7d848d" stroke-width="10" fill="none" opacity=".55" filter="url(#b4)"/>
    <path d="{smooth(DUCT, True)}" fill="url(#duct)" filter="url(#b15)"/>
    <!-- shoulder highlight and lower body shade -->
    <path d="{smooth(SHOULDER)}" stroke="#ffffff" stroke-width="10" fill="none" opacity=".75" filter="url(#b4)"/>
    <path d="{smooth([(x, y + 14) for x, y in SHOULDER])}" stroke="#aab0b8" stroke-width="12" fill="none" opacity=".35" filter="url(#b6)"/>
    <path d="{smooth(SILL)}" stroke="#2a2d32" stroke-width="9" fill="none" stroke-linecap="round"/>
    <path d="{smooth([(x, y - 6) for x, y in SILL])}" stroke="#ffffff" stroke-width="2" fill="none" opacity=".5"/>
    <!-- arch lips catch the light -->
    <circle cx="{WF}" cy="{WZ}" r="{AR + 3}" fill="none" stroke="#ffffff" stroke-width="3" opacity=".55" filter="url(#b15)"/>
    <circle cx="{WR}" cy="{WZ}" r="{AR + 3}" fill="none" stroke="#ffffff" stroke-width="3" opacity=".55" filter="url(#b15)"/>
  </g>
  <path d="{smooth(GLASS, True)}" fill="url(#glass)"/>
  <path d="{smooth([(470, 160), (560, 121), (650, 101)])}" stroke="#ffffff" stroke-width="5" fill="none" opacity=".18" filter="url(#b3)"/>
  <path d="{smooth(INTAKE_S, True)}" fill="#111215"/>
  <path d="{smooth([(60, 291), (120, 288)])}" stroke="#3a3e44" stroke-width="2" fill="none"/>
  <path d="{smooth(LAMP_S)}" stroke="#e9f4ff" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="{smooth(LAMP_S)}" stroke="#bfe0ff" stroke-width="10" fill="none" opacity=".5" filter="url(#b4)"/>
  <path d="{smooth([(40, 342), (150, 346)])}" stroke="#1d1f23" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="{smooth([(1134, 205), (1145, 228)])}" stroke="#ff3b3b" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="{body}" fill="none" stroke="#5b6068" stroke-width="1.2" opacity=".6"/>
 </g>'''


# ----------------------------------------------------------------------------- front view
CX = 1476.0
FRONT = mirror([(CX, 91), (1420, 94), (1382, 104), (1352, 122), (1332, 140), (1318, 150),
                (1290, 153), (1262, 161), (1242, 176), (1232, 198), (1229, 228), (1231, 268),
                (1236, 304), (1243, 334), (1256, 346), (1320, 349), (CX, 350)], CX)
WIND = mirror([(CX, 100), (1404, 103), (1360, 120), (1336, 148), (1338, 172), (1398, 185), (CX, 189)], CX)
MOUTH = mirror([(CX, 300), (1400, 297), (1320, 290), (1262, 284), (1244, 292), (1252, 318),
                (1272, 336), (1320, 343), (CX, 344)], CX)
FIN_L = [(1300, 292), (1318, 318), (1330, 342)]
LAMP_F = [(1243, 236), (1268, 258), (1310, 276), (1352, 286)]
HOOD = [(1350, 182), (1400, 232), (1440, 268), (1476, 278)]


def front_view():
    body = smooth(FRONT, True)
    lamps = "".join(
        f'<path d="{smooth(p)}" stroke="#eef7ff" stroke-width="4" fill="none" stroke-linecap="round"/>'
        f'<path d="{smooth(p)}" stroke="#bfe0ff" stroke-width="11" fill="none" opacity=".45" filter="url(#b4)"/>'
        for p in (LAMP_F, [(2 * CX - x, y) for x, y in LAMP_F]))
    fins = "".join(f'<path d="{smooth(p)}" stroke="#d9dde2" stroke-width="5" fill="none" stroke-linecap="round"/>'
                   for p in (FIN_L, [(2 * CX - x, y) for x, y in FIN_L]))
    hood = "".join(f'<path d="{smooth(p)}" stroke="#ffffff" stroke-width="6" fill="none" opacity=".55" filter="url(#b4)"/>'
                   for p in (HOOD, [(2 * CX - x, y) for x, y in HOOD]))
    return f'''
 <g id="front">
  <ellipse cx="{CX}" cy="360" rx="260" ry="10" fill="#000" opacity=".3" filter="url(#b8)"/>
  <rect x="1226" y="300" width="76" height="61" rx="10" fill="#141518"/>
  <rect x="1650" y="300" width="76" height="61" rx="10" fill="#141518"/>
  <clipPath id="frontclip"><path d="{body}"/></clipPath>
  <path d="{body}" fill="url(#bodyF)"/>
  <g clip-path="url(#frontclip)">
    {hood}
    <path d="M 1229 205 Q 1236 290 1252 344" stroke="#ffffff" stroke-width="6" fill="none" opacity=".5" filter="url(#b4)"/>
    <path d="M 1723 205 Q 1716 290 1700 344" stroke="#ffffff" stroke-width="6" fill="none" opacity=".5" filter="url(#b4)"/>
  </g>
  <path d="{smooth(WIND, True)}" fill="url(#glassF)"/>
  <path d="{smooth(MOUTH, True)}" fill="url(#mouth)"/>
  {fins}
  <path d="M 1430 300 L 1476 314 L 1522 300" stroke="#cfd4da" stroke-width="5" fill="none" stroke-linejoin="round"/>
  <path d="M 1262 351 Q {CX} 358 1690 351" stroke="#1b1d21" stroke-width="5" fill="none" stroke-linecap="round"/>
  {lamps}
  <path d="{body}" fill="none" stroke="#5b6068" stroke-width="1.2" opacity=".6"/>
 </g>'''


# ----------------------------------------------------------------------------- rear view
RG = 770.0
REAR = mirror([(CX, 492), (1420, 494), (1386, 505), (1362, 528), (1348, 556), (1318, 560),
               (1284, 564), (1256, 576), (1236, 596), (1229, 626), (1231, 676), (1238, 720),
               (1248, 744), (1262, 752), (1330, 754), (CX, 755)], CX)
RWIN = mirror([(CX, 518), (1405, 522), (1384, 540), (1390, 560), (CX, 566)], CX)
RECESS = mirror([(CX, 684), (1350, 684), (1316, 692), (1296, 712), (1280, 738), (1274, 754), (CX, 754)], CX)


def rear_view():
    body = smooth(REAR, True)
    fins = "".join(f'<path d="M {x} 716 L {x + (x - CX) * 0.04:.1f} 754" stroke="#3a3e45" stroke-width="5"/>'
                   for x in (1372, 1410, 1442, 1510, 1542, 1580))
    return f'''
 <g id="rear">
  <ellipse cx="{CX}" cy="{RG - 1}" rx="260" ry="10" fill="#000" opacity=".3" filter="url(#b8)"/>
  <rect x="1226" y="708" width="76" height="62" rx="10" fill="#141518"/>
  <rect x="1650" y="708" width="76" height="62" rx="10" fill="#141518"/>
  <clipPath id="rearclip"><path d="{body}"/></clipPath>
  <path d="{body}" fill="url(#bodyR)"/>
  <g clip-path="url(#rearclip)">
    <path d="M 1250 574 Q 1300 556 1350 562" stroke="#ffffff" stroke-width="7" fill="none" opacity=".7" filter="url(#b4)"/>
    <path d="M 1702 574 Q 1652 556 1602 562" stroke="#ffffff" stroke-width="7" fill="none" opacity=".7" filter="url(#b4)"/>
    <path d="M 1250 650 Q {CX} 662 1702 650" stroke="#8d939b" stroke-width="16" fill="none" opacity=".35" filter="url(#b6)"/>
  </g>
  <path d="{smooth(RWIN, True)}" fill="url(#glassF)"/>
  <path d="M 1240 634 Q {CX} 646 1712 634" stroke="#ff2d2d" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M 1240 634 Q {CX} 646 1712 634" stroke="#ff5050" stroke-width="14" fill="none" opacity=".45" filter="url(#b4)"/>
  <path d="{smooth(RECESS, True)}" fill="url(#mouth)"/>
  {fins}
  <rect x="1446" y="694" width="60" height="12" rx="6" fill="#5c6168"/>
  <path d="{body}" fill="none" stroke="#5b6068" stroke-width="1.2" opacity=".6"/>
 </g>'''


DEFS = '''
 <defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="#f7f8fa"/><stop offset=".75" stop-color="#e9ebef"/><stop offset="1" stop-color="#dcdfe4"/></linearGradient>
  <linearGradient id="bodyV" x1="0" y1="80" x2="0" y2="350" gradientUnits="userSpaceOnUse">
   <stop offset="0" stop-color="#fbfcfd"/><stop offset=".35" stop-color="#eef0f3"/>
   <stop offset=".55" stop-color="#d9dde2"/><stop offset=".8" stop-color="#c3c8cf"/><stop offset="1" stop-color="#8e949c"/></linearGradient>
  <linearGradient id="bodyF" x1="0" y1="90" x2="0" y2="350" gradientUnits="userSpaceOnUse">
   <stop offset="0" stop-color="#f6f7f9"/><stop offset=".4" stop-color="#e7eaee"/><stop offset=".75" stop-color="#cfd3d9"/><stop offset="1" stop-color="#9aa0a8"/></linearGradient>
  <linearGradient id="bodyR" x1="0" y1="490" x2="0" y2="755" gradientUnits="userSpaceOnUse">
   <stop offset="0" stop-color="#f6f7f9"/><stop offset=".4" stop-color="#e5e8ec"/><stop offset=".75" stop-color="#cdd1d7"/><stop offset="1" stop-color="#979da5"/></linearGradient>
  <linearGradient id="glass" x1="0" y1="80" x2="0" y2="180" gradientUnits="userSpaceOnUse">
   <stop offset="0" stop-color="#3c4552"/><stop offset=".5" stop-color="#1c2129"/><stop offset="1" stop-color="#0d1015"/></linearGradient>
  <linearGradient id="glassF" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="#4a5462"/><stop offset=".6" stop-color="#1d222a"/><stop offset="1" stop-color="#0e1116"/></linearGradient>
  <linearGradient id="dish" x1="0" y1="190" x2="0" y2="330" gradientUnits="userSpaceOnUse">
   <stop offset="0" stop-color="#8a9099"/><stop offset=".3" stop-color="#b9bec5"/>
   <stop offset=".75" stop-color="#d7dbe0"/><stop offset="1" stop-color="#c9cdd3"/></linearGradient>
  <radialGradient id="duct" cx=".65" cy=".35" r=".8">
   <stop offset="0" stop-color="#050506"/><stop offset=".7" stop-color="#16181b"/><stop offset="1" stop-color="#4b5058"/></radialGradient>
  <linearGradient id="mouth" x1="0" y1="0" x2="0" y2="1">
   <stop offset="0" stop-color="#050506"/><stop offset=".6" stop-color="#14161a"/><stop offset="1" stop-color="#2a2d33"/></linearGradient>
  <radialGradient id="rim" cx=".4" cy=".35" r=".8">
   <stop offset="0" stop-color="#6b717a"/><stop offset=".7" stop-color="#2c2f34"/><stop offset="1" stop-color="#1b1d21"/></radialGradient>
  <linearGradient id="spoke" x1="0" y1="0" x2="1" y2="1">
   <stop offset="0" stop-color="#a3a9b1"/><stop offset="1" stop-color="#5d636b"/></linearGradient>
  <filter id="b15" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.5"/></filter>
  <filter id="b3" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
  <filter id="b4" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="4"/></filter>
  <filter id="b6" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="b8" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>
  <filter id="b12" x="-20%" y="-80%" width="140%" height="260%"><feGaussianBlur stdDeviation="12"/></filter>
 </defs>'''


def label(x, y, t):
    return (f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="20" '
            f'letter-spacing="3" fill="#4a4f57">{t}</text>')


def svg():
    W, H = 1800, 1130
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{DEFS}
 <rect width="{W}" height="{H}" fill="url(#bg)"/>
 <text x="40" y="52" font-family="Helvetica, Arial, sans-serif" font-size="28" letter-spacing="4" fill="#2a2e35">TARGET LOOK — CONCEPT CAR</text>
 <text x="40" y="82" font-family="Helvetica, Arial, sans-serif" font-size="16" fill="#6a7079">Same traced profile as the CAD. Soft sculpted side scoop, sculpted front fascia, finished rear. Wheels indicative only.</text>
 <g transform="translate(0,-10) scale(1.5)">{side_view()}</g>
 {label(60, 590, "SIDE")}
 <g transform="translate(-1718,508) scale(1.45)">{front_view()}</g>
 {label(60, 1090, "FRONT")}
 <g transform="translate(-788,-73) scale(1.45)">{rear_view()}</g>
 {label(990, 1090, "REAR")}
</svg>'''


if __name__ == "__main__":
    s = svg()
    open(OUT + ".svg", "w").write(s)
    subprocess.run(["/opt/pw-browsers/chromium-1194/chrome-linux/chrome", "--headless=new", "--no-sandbox",
                    "--disable-gpu", "--hide-scrollbars", "--window-size=1800,1300",
                    "--screenshot=" + OUT + ".png", "file://" + __import__("os").path.abspath(OUT + ".svg")],
                   check=True, capture_output=True)
    from PIL import Image
    Image.open(OUT + ".png").crop((0, 0, 1800, 1130)).save(OUT + ".png")
    print("wrote", OUT + ".svg", OUT + ".png")
