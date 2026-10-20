"""Build the full concept car and export an assembly STEP with colours."""
import sys, numpy as np
import body as B, features as FT
from occ_util import *
import build_body
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Ax1, gp_Vec
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeRevol
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet


def faces(s):
    out = []; e = TopExp_Explorer(s, TopAbs_FACE)
    while e.More():
        out.append(TopoDS.Face_s(e.Current())); e.Next()
    return out


class Tagged:
    """Solid + face tags that survive boolean ops through the op history."""

    def __init__(self, shape):
        self.shape, self.tags = shape, []

    def _remap(self, op):
        new = []
        for f, t in self.tags:
            if op.IsDeleted(f):
                continue
            mod = op.Modified(f)
            if mod.Size() == 0:
                new.append((f, t))
            else:
                for g in mod:
                    new.append((TopoDS.Face_s(g), t))
        self.tags = new

    def cut(self, tool, tag=None):
        op = BRepAlgoAPI_Cut(self.shape, tool); op.SetFuzzyValue(1e-4); op.Build()
        assert op.IsDone()
        self._remap(op)
        if tag:
            res = TopTools_IndexedMapOfShape()
            from OCP.TopExp import TopExp
            TopExp.MapShapes_s(op.Shape(), TopAbs_FACE, res)
            for tf in faces(tool):
                mod = op.Modified(tf)
                cands = [TopoDS.Face_s(g) for g in mod] if mod.Size() else [tf]
                for g in cands:
                    if res.Contains(g):
                        self.tags.append((g, tag))
        self.shape = op.Shape()
        return self

    def fix(self, divide_closed=False):
        """ShapeFix the solid (optionally splitting closed/periodic faces, which do not
        survive a STEP round trip); tags follow through the underlying surfaces."""
        from OCP.ShapeFix import ShapeFix_Shape
        from OCP.ShapeUpgrade import ShapeUpgrade_ShapeDivideClosed
        from OCP.BRep import BRep_Tool
        surf = {}
        for g, t in self.tags:
            surf[BRep_Tool.Surface_s(g)] = t
        s = self.shape
        if divide_closed:
            d = ShapeUpgrade_ShapeDivideClosed(s); d.SetNbSplitPoints(1); d.Perform(); s = d.Result()
        fx = ShapeFix_Shape(s); fx.Perform()
        self.shape = fx.Shape()
        self.tags = [(f, surf[BRep_Tool.Surface_s(f)]) for f in faces(self.shape)
                     if BRep_Tool.Surface_s(f) in surf]
        return self

    def tag_of(self, f):
        for g, t in self.tags:
            if g.IsSame(f):
                return t
        return None


def inner_body(s, dx=45.0, dy=40.0, dz=35.0):
    """The body shrunk about its centre: used to give recessed panels a floor."""
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    cx, cz = B.LENGTH / 2, 450.0
    sx, sy, sz = 1 - dx / cx, 1 - dy / 1046.0, 1 - dz / cz
    g = gp_GTrsf()
    g.SetVectorialPart(gp_Mat(sx, 0, 0, 0, sy, 0, 0, 0, sz))
    g.SetTranslationPart(gp_XYZ(cx * (1 - sx), 0, cz * (1 - sz)))
    return BRepBuilderAPI_GTransform(s, g, True).Shape()


def keep_solids(s, min_vol):
    """Compound of the solids of s larger than min_vol (drops boolean slivers)."""
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    from OCP.TopAbs import TopAbs_SOLID
    comp = TopoDS_Compound(); bb = BRep_Builder(); bb.MakeCompound(comp)
    e = TopExp_Explorer(s, TopAbs_SOLID)
    while e.More():
        if volume(e.Current()) > min_vol:
            bb.Add(comp, e.Current())
        e.Next()
    return comp


def y_prism(pts2d, corners, y0, y1):
    return outline_prism(pts2d, corners, 'xz', y0, y1)


def poly_prism(pts2d, plane, a, b):
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
    poly = BRepBuilderAPI_MakePolygon()
    for u, v in pts2d:
        p = {'xz': (u, a, v), 'yz': (a, u, v), 'xy': (u, v, a)}[plane]
        poly.Add(gp_Pnt(*p))
    poly.Close()
    f = face_from_wire(poly.Wire())
    d = {'xz': (0, b - a, 0), 'yz': (b - a, 0, 0), 'xy': (0, 0, b - a)}[plane]
    return prism(f, d)


def cyl_y(xc, zc, r, y0, y1):
    ax = gp_Ax2(gp_Pnt(xc, y0, zc), gp_Dir(0, 1, 0))
    return BRepPrimAPI_MakeCylinder(ax, r, y1 - y0).Shape()


def both_sides(make):
    return [make(+1), make(-1)]


def build():
    core = build_body.build()
    body = Tagged(core)
    # wheel arches / wheel houses
    for xa in (B.AXLE_F, B.AXLE_R):
        for sgn in (1, -1):
            y0, y1 = (690, 1400) if sgn > 0 else (-1400, -690)
            body.cut(cyl_y(xa, B.WHEEL_Z, B.ARCH_R, y0, y1), 'well')
    print("arches", valid(body.shape))
    # front intake: front-view mouth  x  side-view wedge
    mouth = outline_prism(*FT.INTAKE_FRONT, 'yz', -50, 600)
    wedge = outline_prism(*FT.INTAKE_SIDE, 'xz', -1300, 1300)
    itool = common(mouth, wedge)
    body.cut(itool, 'dark')
    # the intake is a black panel set back ~40 mm, not an empty hole
    grille = keep_solids(common(itool, inner_body(core)), 1e5)
    print("intake", valid(body.shape))
    # side scoops: shallow recess + deeper duct, sill recess
    for sgn in (1, -1):
        body.cut(y_prism(*FT.SCOOP, sgn * 845, sgn * 1400), 'recess')
        body.cut(y_prism(*FT.SCOOP_IN, sgn * 660, sgn * 1400), 'dark')
        body.cut(outline_prism(*FT.SILL, 'xz', sgn * 850, sgn * 1400), 'dark')
    print("scoops", valid(body.shape))
    # rear recess + diffuser
    L = B.LENGTH
    body.cut(outline_prism(*FT.REAR_RECESS, 'yz', L - 140, L + 50), 'dark')
    body.cut(outline_prism(*FT.DIFFUSER, 'yz', L - 320, L + 50), 'dark')
    print("rear", valid(body.shape))
    # glazing: split off as its own solid
    # canopy glass: side outline, kept inboard of the fender / haunch crests
    # (intersecting the two prisms first leaves a tool the kernel cannot cut with;
    #  applying them one after the other is reliable)
    glass = common(common(body.shape, y_prism(*FT.CANOPY_GLASS, -1300, 1300)),
                   outline_prism(*FT.GLASS_PLAN, 'xy', 500, 1500))
    body.cut(glass, None)
    if not valid(body.shape):
        body.fix()
    print("after glass faces", len(faces(body.shape)), "vol L %.0f" % (volume(body.shape) / 1e6))
    print("glass", valid(body.shape), valid(glass), "%.1f L" % (volume(glass) / 1e6))
    # headlamps: lens solids split off the fender tops
    hs = outline_prism(*FT.HEAD_SIDE, 'xz', -1300, 1300)
    hf = outline_prism(*FT.HEAD_FRONT, 'yz', -100, 1400)
    hf = fuse(hf, mirror_y(hf))
    htool = common(hs, hf)
    lamps = keep_solids(common(body.shape, htool), 1e6)
    body.cut(htool, None)
    if not valid(body.shape):
        body.fix()
    body.fix(divide_closed=True)
    print("body valid", valid(body.shape), "faces", len(faces(body.shape)), "vol L %.0f" % (volume(body.shape) / 1e6))
    print("lamps", valid(lamps), "%.1f L" % (volume(lamps) / 1e6))
    return body, glass, lamps, grille


def wheel(xa, sgn):
    """Plain cylinder wheel, outer face at |y| = 1035, 305 mm wide."""
    w = 305.0
    y0 = sgn * 1035.0
    y1 = y0 - sgn * w
    return cyl_y(xa, B.WHEEL_Z, B.TIRE_R, min(y0, y1), max(y0, y1))


if __name__ == "__main__":
    from OCP.BRepTools import BRepTools
    body, glass, lamps, grille = build()
    BRepTools.Write_s(grille, "out/grille.brep")
    BRepTools.Write_s(body.shape, "out/body.brep")
    BRepTools.Write_s(glass, "out/glass.brep")
    BRepTools.Write_s(lamps, "out/lamps.brep")
    import pickle
    tags = {}
    allf = faces(body.shape)
    lab = [body.tag_of(f) for f in allf]
    pickle.dump(lab, open("out/body_tags.pkl", "wb"))
    print("faces", len(allf), {t: lab.count(t) for t in set(lab)})
