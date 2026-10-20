"""Feature outlines traced from the concept sheet (px of each view) -> mm.
Each outline is (points, corner indices); corners are sharp, the rest is splined."""
import numpy as np
import body as B

FS, F_CX, F_GND = 4.235, 1476.0, 361.0     # front view
RS, R_CX, R_GND = 4.11, 1476.0, 770.0      # rear view


def side(pts):
    return [(float(B.X(u)), float(B.Z(v))) for u, v in pts]


def front(pts):  # (px, py) of the front view -> (y, z), +y = viewer's left
    return [((F_CX - u) * FS, (F_GND - v) * FS) for u, v in pts]


def rear(pts):
    return [((u - R_CX) * RS, (R_GND - v) * RS) for u, v in pts]


def mirror_closed(half, corners=()):
    """half (mm): points from the top centre (y=0) out to one side and back to the bottom centre.
    Returns the symmetric closed loop and the mirrored corner indices."""
    n = len(half)
    loop = half + [(-y, z) for y, z in reversed(half[1:-1])]
    cs = list(corners) + [2 * n - 2 - c for c in corners if 0 < c < n - 1]
    return loop, cs


# side scoop (big lozenge between the wheels): outer recess edge
SCOOP = (side([(388, 272), (398, 264), (430, 257), (500, 244), (600, 226), (700, 212),
               (780, 201), (815, 196), (833, 196), (830, 205), (815, 228), (795, 252),
               (765, 274), (720, 293), (660, 302), (590, 308), (520, 316), (460, 318),
               (430, 313), (410, 300), (395, 286)]), [0, 8])
# inner duct opening (lighter ellipse inside the scoop)
SCOOP_IN = (side([(440, 280), (470, 268), (560, 252), (660, 236), (740, 224), (790, 218),
                  (798, 226), (780, 248), (740, 268), (680, 283), (600, 292), (520, 298),
                  (465, 298), (445, 291)]), [])
GLASS_SIDE = (side([(495, 181), (512, 168), (535, 150), (565, 128), (600, 108), (650, 97),
                    (700, 96), (750, 104), (790, 117), (818, 129), (833, 137), (822, 142),
                    (760, 150), (700, 158), (640, 165), (580, 171), (530, 177)]), [0, 10])
WINDSHIELD = mirror_closed(front([(1476, 108), (1440, 110), (1405, 115), (1380, 128), (1362, 145),
                                  (1352, 165), (1356, 176), (1400, 186), (1476, 192)]))
INTAKE_FRONT = mirror_closed(front([(1476, 302), (1400, 300), (1320, 294), (1260, 286), (1226, 279),
                                    (1236, 300), (1255, 322), (1290, 336), (1380, 341), (1476, 342)]), [4])
INTAKE_SIDE = (side([(20, 289), (60, 288), (100, 285), (136, 281), (124, 297),
                     (108, 312), (88, 324), (66, 331), (20, 333)]), [0, 3, 8])
SILL = (side([(372, 346), (400, 337), (450, 330), (550, 325), (650, 321), (740, 321),
              (790, 326), (840, 335), (895, 346), (895, 375), (372, 375)]), [0, 8, 9, 10])
REAR_RECESS = mirror_closed(rear([(1476, 677), (1350, 677), (1320, 683), (1300, 700), (1285, 725),
                                  (1268, 748), (1268, 790), (1476, 790)]), [6])
DIFFUSER = mirror_closed(rear([(1476, 712), (1420, 712), (1395, 718), (1365, 735), (1340, 750),
                               (1340, 790), (1476, 790)]), [5])
# headlamps: long swept lens on the front fender top
# side view: under the crest, down to the thin line running nose tip -> front arch
HEAD_SIDE = (side([(36, 287), (52, 284), (80, 276), (120, 262), (160, 247), (200, 231),
                   (232, 219), (258, 211), (232, 186), (195, 166), (150, 146), (100, 128),
                   (36, 120)]), [0, 7, 12])
# front view: teardrop from the fender top falling inboard (left lamp, y > 0)
HEAD_FRONT = (front([(1236, 168), (1290, 166), (1340, 178), (1372, 200), (1395, 236),
                     (1385, 250), (1340, 262), (1290, 252), (1256, 222), (1238, 190)]), [])

def _plan(pts):  # (x px, y mm) -> (x mm, y mm)
    return [(float(B.X(u)), float(v)) for u, v in pts]


# windshield in plan: base along the cowl, curved upper edge into the roof
_ws = _plan([(378, 0), (381, 200), (390, 380), (404, 520), (420, 640), (600, 640),
             (590, 470), (574, 300), (566, 150), (564, 0)])
WS_PLAN = (_ws + [(x, -y) for x, y in reversed(_ws[1:-1])], [4, 5, 13, 14])
