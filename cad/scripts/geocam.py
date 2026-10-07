"""Camera box (parts 272 + 273) as one hollow box, and simplified contents.

Outer surface follows the original: box X[-48.21,49.39] Y[-188.85,-96.85]
Z[-41.02,37.98], 2 mm side walls, 3 mm bottom and lid, the stepped R26/R27
opening and recesses in the bottom, the lens openings, the cable slot in the
-Y wall, the R5 notch in the lid edge and every screw hole (the previous pass
had capped most of them).
"""
from geo270 import fuse, cut, fuse_many, cut_many, box
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line

X0, X1, Y0, Y1, Z0, Z1 = -48.21, 49.39, -188.85, -96.85, -41.02, 37.98
T_WALL, T_BOT, T_TOP = 2.0, 3.0, 3.1


def zcyl(x, y, z0, z1, r):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(0, 0, 1)), r, z1 - z0).Shape()
def xcyl(y, z, x0, x1, r):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x0, y, z), gp_Dir(1, 0, 0)), r, x1 - x0).Shape()
def ycyl(x, z, y0, y1, r):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y0, z), gp_Dir(0, 1, 0)), r, y1 - y0).Shape()


def round_edges(shape, r, parallel_to=None):
    """fillet straight edges (optionally only those parallel to an axis)"""
    f = BRepFilletAPI_MakeFillet(shape)
    e = TopExp_Explorer(shape, TopAbs_EDGE); n = 0
    while e.More():
        ed = TopoDS.Edge_s(e.Current()); c = BRepAdaptor_Curve(ed)
        if c.GetType() == GeomAbs_Line:
            d = c.Line().Direction()
            if parallel_to is None or abs((d.X(), d.Y(), d.Z())[parallel_to]) > 0.99:
                f.Add(r, ed); n += 1
        e.Next()
    f.Build()
    return f.Shape() if (n and f.IsDone()) else shape


def build_box():
    outer = box(X0, Y0, Z0, X1, Y1, Z1)
    inner = box(X0 + T_WALL, Y0 + T_WALL, Z0 + T_BOT, X1 - T_WALL, Y1 - T_WALL, Z1 - T_TOP)
    s = cut(outer, inner)
    t = []
    # bottom: stepped opening for the round unit, lens openings, recesses, screw holes
    t += [zcyl(-15.66, -159.35, Z0 - 1, Z0 + T_BOT + 1, 26.0), zcyl(-15.66, -159.35, Z0 - 1, Z0 + 1.0, 27.0)]
    t += [zcyl(28.05, -116.97, Z0 - 1, Z0 + T_BOT + 1, 11.25)]          # camera lens (was capped)
    t += [zcyl(28.05, -159.35, Z0 - 1, Z0 + T_BOT + 1, 9.03)]           # second lens cup
    t += [zcyl(-15.66, -108.42, Z0 - 1, Z0 + 2.0, 4.0), zcyl(-15.66, -123.42, Z0 - 1, Z0 + 2.0, 8.0)]
    for x, y in ((18.42, -106.13), (17.21, -126.60), (-36.87, -180.56), (5.56, -180.56),
                 (5.56, -138.14), (37.69, -127.81), (-36.87, -138.14), (38.89, -107.34)):
        t.append(zcyl(x, y, Z0 - 1, Z0 + T_BOT + 1, 1.25))
    # +X wall screw holes, -X wall lid screws
    for y, z in ((-107.85, 29.88), (-177.85, 29.88), (-124.47, -33.15), (-109.47, -13.15),
                 (-124.47, -13.15), (-109.47, -33.15), (-104.85, 15.85), (-114.85, 15.85)):
        t.append(xcyl(y, z, X1 - T_WALL - 1, X1 + 1, 1.6))
    for y, z in ((-107.85, 29.88), (-177.85, 29.88)):
        t.append(xcyl(y, z, X0 - 1, X0 + T_WALL + 1, 1.6))
    # -Y wall: screw holes and cable slot;  +Y wall: screw holes
    for x, z in ((37.34, 11.27), (37.34, -27.93), (-36.16, -32.59), (-36.16, 2.41)):
        t.append(ycyl(x, z, Y0 - 1, Y0 + T_WALL + 1, 1.6))
    t.append(box(-5.36, Y0 - 1, Z0 + 2.0, 6.54, Y0 + T_WALL + 1, 30.98))
    for x, z in ((6.39, 15.85), (41.39, 15.85)):
        t.append(ycyl(x, z, Y1 - T_WALL - 1, Y1 + 1, 1.6))
    # lid edge notch
    t.append(zcyl(X1, -121.85, Z1 - T_TOP - 0.01, Z1 + 1, 5.0))
    return cut_many(s, t)


def build_contents():
    """simplified, smooth stand-ins for the parts inside the box"""
    # round unit (274-281): R25.5 base, R25 body, cone to R18
    ru = fuse_many([zcyl(-15.66, -159.35, -46.5, -41.02, 25.5),
                    zcyl(-15.66, -159.35, -41.02, -30.3, 25.0),
                    BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(-15.66, -159.35, -30.3), gp_Dir(0, 0, 1)), 25.0, 18.0, 19.2).Shape()])
    # lens below the camera board (560-574)
    lens = zcyl(28.05, -116.97, -47.9, -39.1, 10.31)
    ch = BRepFilletAPI_MakeChamfer(lens); e = TopExp_Explorer(lens, TopAbs_EDGE)
    while e.More():
        ed = TopoDS.Edge_s(e.Current()); c = BRepAdaptor_Curve(ed)
        if abs(c.Value(c.FirstParameter()).Z() + 47.9) < 1e-6: ch.Add(0.8, ed)
        e.Next()
    ch.Build(); lens = ch.Shape()
    # camera board stack (282-559): carrier plate + sensor block
    board = fuse(round_edges(box(13.2, -136.7, -26.0, 42.4, -102.6, -24.4), 1.5, 2),
                 round_edges(box(16.8, -128.2, -24.4, 39.3, -105.7, -8.7), 1.5, 2))
    # camera (575-587): two boards and its lens cup
    cam = [round_edges(box(11.3, -181.0, -31.3, 41.6, -179.4, 17.4), 2.0, 1),
           round_edges(box(15.1, -142.3, -34.4, 39.1, -140.6, 11.0), 2.0, 1),
           zcyl(28.05, -159.35, -41.0, -35.5, 9.02)]
    return {'ROUND_UNIT': ru, 'LENS': lens, 'CAMERA_BOARD': board, 'CAMERA': cam}
