"""Part 'base' (yaw housing: tray open toward -X, closed by plate 588, with the
yaw ring disc at the rear).

The source shell is missing several inner faces (top-wall inner face, front
wall inner face, the tray cavity walls next to the centre bar, and the 0.5 mm
pads on the inner side of the side panel).  The part is rebuilt as prisms:

* X -89.69..-87.69   ring disc            (clean section of the shell)
* X -87.69..-82.29   ring disc + frame + centre bar: clean section minus the
                     tray cavity (redrawn, see tray_walls)
* X -82.29..-58.79   tray walls only (redrawn)
* X -58.79..-57.29   side panel           (clean section, all its holes)

The tray-wall profile is taken from the intact bottom half and mirrored to
the top (the part is symmetric about Z=0); features cut into the top wall
(nut pockets, holes) are taken from horizontal sections of the top wall.
"""
import math
from geo270 import fuse, cut, cut_many, circle_face, rect_face
from geo012 import section_face, prism_x, yz, to_x, _wires
from geo270 import arc_edge, line_edge, path_face
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir, gp_Vec, gp_Trsf, gp_Ax1
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeFace
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

C = (-265.4, 0.0)            # ring disc centre (Y, Z)
XD0, XD1, XB, XP, XO = -89.69, -87.69, -82.29, -58.79, -57.29


def _half_paths():
    """bottom-half outer and inner (cavity side) profile of the tray walls, in (Y, Z)"""
    A = (-210.23, -6.03)
    outer = [('arc', C, 55.5, A, (-231.86, -44.22)),
             ('arc', (-228.23, -49.0), 6.0, (-231.86, -44.22), (-234.23, -49.0)),
             ('arc', (-228.23, -49.0), 6.0, (-234.23, -49.0), (-228.23, -55.0)),
             ('line', (-228.23, -55.0), (-85.4, -55.0)),
             ('line', (-85.4, -55.0), (-85.4, -44.9)),
             ('line', (-85.4, -44.9), (-77.0, -44.9)),
             ('line', (-77.0, -44.9), (-77.0, -40.0)),
             ('line', (-77.0, -40.0), (-82.9, -40.0)),
             ('line', (-82.9, -40.0), (-82.9, 0.0))]
    inner = [('line', (-85.4, 0.0), (-85.4, -37.08)),
             ('arc', (-88.4, -37.08), 3.0, (-85.4, -37.08), (-87.9, -40.04)),
             ('arc', (-87.4, -43.0), 3.0, (-87.9, -40.04), (-90.4, -43.0)),
             ('line', (-90.4, -43.0), (-90.4, -49.5)),
             ('arc', (-93.4, -49.5), 3.0, (-90.4, -49.5), (-93.4, -52.5)),
             ('line', (-93.4, -52.5), (-222.9, -52.5)),
             ('arc', (-222.9, -49.5), 3.0, (-222.9, -52.5), (-225.9, -49.5)),
             ('arc', (-228.9, -49.5), 3.0, (-225.9, -49.5), (-225.95, -49.0)),
             ('arc', (-228.9, -49.5), 3.0, (-225.95, -49.0), (-226.58, -47.6)),
             ('arc', (-224.25, -45.71), 3.0, (-226.58, -47.6), (-226.26, -43.48)),
             ('arc', C, 58.5, (-226.26, -43.48), (-207.67, -9.49)),
             ('arc', (-210.63, -9.0), 3.0, (-207.67, -9.49), (-207.63, -9.0)),
             ('arc', (-210.63, -9.0), 3.0, (-207.63, -9.0), A)]
    return outer, inner


def _edges(segs, mirror=False, reverse=False):
    m = (lambda p: (p[0], -p[1])) if mirror else (lambda p: p)
    out = []
    for s in segs:
        if s[0] == 'line':
            a, b = m(s[1]), m(s[2])
            out.append(line_edge(b, a) if reverse else line_edge(a, b))
        else:
            c, r, a, b = m(s[1]), s[2], m(s[3]), m(s[4])
            out.append(arc_edge(c, r, b, a) if reverse else arc_edge(c, r, a, b))
    return out[::-1] if reverse else out


def tray_walls():
    """C-shaped wall profile (material), sketch frame u=Y, v=Z:
    A -> bottom outer -> front -> top outer -> A' -> top inner -> front -> bottom inner -> A"""
    outer, inner = _half_paths()
    return path_face(_edges(outer) + _edges(outer, mirror=True, reverse=True)
                     + _edges(inner, mirror=True, reverse=True) + _edges(inner))


def cavity():
    """void inside the tray (sketch frame), closed across the wall gap at the bar"""
    _, inner = _half_paths()
    bot = _edges(inner)                                         # (-85.4,0) .. A
    top = _edges(inner, mirror=True, reverse=True)              # A' .. (-85.4,0)
    return path_face(bot + [line_edge((-210.23, -6.03), (-210.23, 6.03))] + top)


def _area(f):
    p = GProp_GProps(); BRepGProp.SurfaceProperties_s(f, p); return p.Mass()


def build_base(shell):
    bodies = []
    f, holes = section_face(shell, 'X', -88.9)                  # ring disc, back layer
    bodies.append(prism_x(cut_many(f, [h for h, _ in holes]) if holes else f, XD0, XD1, -88.9))
    f, holes = section_face(shell, 'X', -85.0)                  # ring disc + frame + bar
    f = cut_many(f, [h for h, _ in holes]) if holes else f
    cav = cut(cavity(), rect_face(-210.63, -6.0, -82.9, 6.0))   # minus centre bar
    f = cut(f, to_x(cav, -85.0))
    bodies.append(prism_x(f, XD1, XB, -85.0))
    w = cut_many(tray_walls(), [circle_face(-228.9, z, 1.35) for z in (49.5, -49.5)])
    bodies.append(yz(w, XB, XP))
    f, holes = section_face(shell, 'X', -58.2)                  # side panel with all holes
    bodies.append(prism_x(cut_many(f, [h for h, _ in holes]) if holes else f, XP, XO, -58.2))
    out = bodies[0]
    for b in bodies[1:]:
        out = fuse(out, b)
    # features cut into the top wall from above (nut pockets, holes): 0.5 mm Z-slabs
    tools = []
    for z in (52.75, 53.25, 53.75, 54.25, 54.75):
        pln = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
        ws = [w_ for w_, closed, bb in _wires(shell, pln) if closed]
        if len(ws) < 2: continue
        faces = sorted((BRepBuilderAPI_MakeFace(w_, True).Face() for w_ in ws), key=lambda f_: -_area(f_))
        for f_ in faces[1:]:
            t = gp_Trsf(); t.SetTranslation(gp_Vec(0, 0, -0.25))
            tools.append(BRepPrimAPI_MakePrism(BRepBuilderAPI_Transform(f_, t, True).Shape(), gp_Vec(0, 0, 0.5)).Shape())
    if tools:
        out = cut_many(out, tools)
    return out
