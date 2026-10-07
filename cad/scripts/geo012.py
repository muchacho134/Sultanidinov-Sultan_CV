"""Part 012 (main side plate).

The source is an open shell whose hole pattern was filled wrongly.  The part
is rebuilt as prisms from cross sections of that shell (the plate along X,
the two side flange plates along Y): closed section loops are kept as they
are, open loops (the broken features) are dropped and redrawn from the
pattern found on the rest of the part:

* 8 slots on R25..30 around (Y,Z)=(-265.4,0), every 45 deg: through slot R2.05
  (front 3 mm) + counterbore (back 3 mm).  0/45/180 deg were capped or open.
* left centre opening = mirror of the right one.
* tops of the two stem slots (run up to the R35 disc edge with R3 corners).
* top flange (end face / corner were missing) and its screw holes R1.3 and
  slots R1.5, symmetric about Y=-265.4.
"""
import math
from geo270 import (circle_face, poly_face, rect_face, stadium_face, one_face, fillet_at, plane_face,
                    fuse, cut, common, fuse_many, cut_many, unify, box)
from OCP.gp import gp_Trsf, gp_Ax2, gp_Ax1, gp_Pnt, gp_Dir, gp_Vec, gp_Pln
from OCP.BRepBuilderAPI import (BRepBuilderAPI_Transform, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid,
                                BRepBuilderAPI_MakeFace)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.ShapeFix import ShapeFix_Solid
from OCP.GeomAbs import GeomAbs_C0
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_SHELL
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

XA, XM, XB, XF = -56.39, -53.39, -50.39, -36.49     # front face, counterbore floor, back face, flange end
YC, ZC = -265.4, 0.0                                   # centre of the 8-slot pattern

# ---- frames: 2D sketches live in the helpers' plane (u,0,v); map u->Y, v->Z ----
def _tr(shape, t): return BRepBuilderAPI_Transform(shape, t, True).Shape()
def yz(face2d, x0, x1):
    """sketch (u=Y, v=Z) -> prism along X from x0 to x1"""
    t = gp_Trsf(); t.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.pi / 2)
    m = gp_Trsf(); m.SetTranslation(gp_Vec(x0, 0, 0))
    return BRepPrimAPI_MakePrism(_tr(_tr(face2d, t), m), gp_Vec(x1 - x0, 0, 0)).Shape()
def xz(face2d, y0, y1):
    """sketch (u=X, v=Z) -> prism along Y from y0 to y1"""
    m = gp_Trsf(); m.SetTranslation(gp_Vec(0, y0, 0))
    return BRepPrimAPI_MakePrism(_tr(face2d, m), gp_Vec(0, y1 - y0, 0)).Shape()

def _wires(s, pln, tol=1e-4):
    sec = BRepAlgoAPI_Section(s, pln); sec.Build()
    seq = TopTools_HSequenceOfShape(); e = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    while e.More(): seq.Append(e.Current()); e.Next()
    out = TopTools_HSequenceOfShape()
    ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(seq, tol, False, out)
    res = []
    for i in range(1, out.Length() + 1):
        w = out.Value(i); b = Bnd_Box(); BRepBndLib.Add_s(w, b)
        res.append((TopoDS.Wire_s(w), BRep_Tool.IsClosed_s(w), b.Get()))
    return res

def to_x(face2d, c):
    """sketch face (u=Y, v=Z) -> plane X=c"""
    t = gp_Trsf(); t.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.pi / 2)
    m = gp_Trsf(); m.SetTranslation(gp_Vec(c, 0, 0))
    return _tr(_tr(face2d, t), m)

def section_face(s, axis, c, keep=lambda bb: True):
    """Cross-section of shell s at plane axis=c, built in place: outer loop minus closed inner
    loops.  Open loops (broken features) are dropped and redrawn from the pattern."""
    pln = gp_Pln(gp_Pnt(c, 0, 0), gp_Dir(1, 0, 0)) if axis == 'X' else gp_Pln(gp_Pnt(0, c, 0), gp_Dir(0, 1, 0))
    ws = [(w, bb) for w, closed, bb in _wires(s, pln) if closed and keep(bb)]
    span = lambda bb: (bb[3] - bb[0]) + (bb[4] - bb[1]) + (bb[5] - bb[2])
    ws.sort(key=lambda x: -span(x[1]))
    faces = [BRepBuilderAPI_MakeFace(w, True).Face() for w, _ in ws]
    return faces[0], list(zip(faces[1:], [bb for _, bb in ws[1:]]))

def prism_x(face, x0, x1, c):
    m = gp_Trsf(); m.SetTranslation(gp_Vec(x0 - c, 0, 0))
    return BRepPrimAPI_MakePrism(_tr(face, m), gp_Vec(x1 - x0, 0, 0)).Shape()
def prism_y(face, y0, y1, c):
    m = gp_Trsf(); m.SetTranslation(gp_Vec(0, y0 - c, 0))
    return BRepPrimAPI_MakePrism(_tr(face, m), gp_Vec(0, y1 - y0, 0)).Shape()

def pol(r, a):
    a = math.radians(a); return (YC + r * math.cos(a), ZC + r * math.sin(a))
def mirror3d(shape):
    t = gp_Trsf(); t.SetMirror(gp_Ax2(gp_Pnt(0, YC, 0), gp_Dir(0, 1, 0)))
    return _tr(shape, t)

def stem_slots():
    """two stem slots: R3.5 bottom at Z=-54.5, running up to the R35 disc edge with R3 corners"""
    out = []
    for y0, y1 in ((-261.9, -254.9), (-275.9, -268.9)):
        yc = (y0 + y1) / 2
        f = one_face(unify(fuse(rect_face(y0, -54.5, y1, -25), circle_face(yc, -54.5, 3.5))))
        f = one_face(cut(f, circle_face(YC, ZC, 35)))
        zt = lambda y: -math.sqrt(35 ** 2 - (y - YC) ** 2)
        out.append(fillet_at(f, [(y0, zt(y0)), (y1, zt(y1))], 3.0))
    return out

def top_holes(r_hole=1.3, r_slot=1.5):
    hs = [circle_face(y, 35, r_hole) for y in (-252.4, -260.4, -270.4, -278.4)]
    hs += [stadium_face((y, 32.5), (y, 37.5), r_slot) for y in (-256.4, -274.4)]
    return hs

def slab(shell, c, front):
    """one 3 mm plate slab: section of the shell + redrawn pattern features (sketch frame)"""
    outer, inner = section_face(shell, 'X', c)
    holes = [f for f, bb in inner]
    pat = []
    for a, rcb in ((0, 4.0), (45, 4.05), (180, 4.05)):            # broken pattern slots
        pat.append(stadium_face(pol(25, a), pol(30, a), 2.05 if front else rcb))
    pat += stem_slots() + top_holes()
    holes += [to_x(f, c) for f in pat]
    if front:   # left centre opening = mirror of the right one (incl. its R1.3 hole)
        for f, bb in inner:
            if bb[1] > YC and bb[4] < -250 and abs(bb[2] + 19.4) < 1 or (abs(bb[1] + 258.7) < 0.2 and abs(bb[2] + 2.3) < 0.2):
                holes.append(mirror3d(f))
    face = cut_many(outer, holes)
    return face

def flange_face():
    fl = one_face(unify(fuse(fuse(rect_face(-281.4, 33, -249.4, 37), rect_face(-278.4, 30, -252.4, 40)),
                              fuse_many([circle_face(y, z, 3) for y in (-278.4, -252.4) for z in (33, 37)]))))
    fl = one_face(cut(fl, circle_face(YC, 30, 4)))                 # notch = 90-deg counterbore R4
    d = math.sqrt(7 ** 2 - 3 ** 2)
    for sg in (1, -1):                                             # R3 roundings at the notch
        cy = YC + sg * d
        tn = (YC + sg * 4 * d / 7, 30 + 4 * 3 / 7)
        q = poly_face([tn, (tn[0], 30), (cy, 30), (cy, 33)])
        fl = one_face(cut(fl, cut(cut(q, circle_face(cy, 33, 3)), circle_face(YC, 30, 4))))
    return one_face(unify(cut_many(fl, top_holes())))

def build_012(shell):
    A = slab(shell, -54.5, True)
    B = slab(shell, -52.0, False)
    fo, fi = section_face(shell, 'X', -45.0, keep=lambda bb: bb[5] < -100)
    foot = cut_many(fo, [f for f, _ in fi]) if fi else fo
    ya, yai = section_face(shell, 'Y', -217.7)
    yb, ybi = section_face(shell, 'Y', -209.6)
    flA = cut_many(ya, [f for f, _ in yai]) if yai else ya
    flB = cut_many(yb, [f for f, _ in ybi]) if ybi else yb
    # 45-deg gusset between plate and inner flange plate (prism along Z)
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
    pg = BRepBuilderAPI_MakePolygon()
    for x, y in ((XB, -223.2), (XB, -219.2), (XB + 4, -219.2)): pg.Add(gp_Pnt(x, y, -22.5))
    pg.Close()
    g = BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(pg.Wire(), True).Face(), gp_Vec(0, 0, 62.5)).Shape()
    bodies = [prism_x(A, XA, XM, -54.5), prism_x(B, XM, XB, -52.0),
              yz(flange_face(), XB, XF), prism_x(foot, XB, XF, -45.0),
              prism_y(flA, -219.2, -216.2, -217.7), prism_y(flB, -211.1, -208.1, -209.6), g]
    out = bodies[0]
    for b in bodies[1:]:
        out = fuse(out, b)          # sequential fuse; UnifySameDomain stalls on this part, so it is skipped
    return out
