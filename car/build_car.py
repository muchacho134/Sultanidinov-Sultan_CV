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


def grown_body(s, d):
    """The body loft rebuilt with every section offset d mm outwards."""
    return build_body.build(offset=d)


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


def soften(body, r_arch=12.0, r_open=6.0, min_r=3.0):
    """Fillet the edges where a cut meets the body skin, one edge at a time
    (batches fail on this surface); halve the radius on failure down to min_r.
    Face tags follow through the underlying surfaces."""
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_BSplineSurface, GeomAbs_Cylinder
    from OCP.BRep import BRep_Tool
    from OCP.GCPnts import GCPnts_AbscissaPoint
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    surf_tag = {BRep_Tool.Surface_s(g): t for g, t in body.tags}
    done, failed, tried = 0, 0, set()
    while True:
        s = body.shape
        m = TopTools_IndexedDataMapOfShapeListOfShape()
        TopExp.MapShapesAndAncestors_s(s, TopAbs_EDGE, TopAbs_FACE, m)
        cand = None
        for i in range(1, m.Extent() + 1):
            fl = [TopoDS.Face_s(f) for f in m.FindFromIndex(i)]
            if len(fl) != 2:
                continue
            types = [BRepAdaptor_Surface(f).GetType() for f in fl]
            if types.count(GeomAbs_BSplineSurface) != 1:
                continue
            e = TopoDS.Edge_s(m.FindKey(i))
            if BRep_Tool.Degenerated_s(e) or GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(e)) < 20:
                continue
            c = BRepAdaptor_Curve(e); p = c.Value((c.FirstParameter() + c.LastParameter()) / 2)
            key = (round(p.X()), round(p.Y()), round(p.Z()))
            if key in tried:
                continue
            cand = (e, key, r_arch if GeomAbs_Cylinder in types else r_open)
            break
        if cand is None:
            break
        e, key, r = cand
        tried.add(key)
        ok = False
        while r >= min_r and not ok:
            mf = BRepFilletAPI_MakeFillet(s); mf.Add(r, e)
            try:
                mf.Build(); ok = mf.IsDone() and valid(mf.Shape())
            except Exception:
                ok = False
            if not ok:
                r /= 2
        if ok:
            body.shape = mf.Shape(); done += 1
            # fillet faces sit at the edge midpoint: remember them as tried
            tried.add(key)
        else:
            failed += 1
    body.tags = [(f, surf_tag[BRep_Tool.Surface_s(f)]) for f in faces(body.shape)
                 if BRep_Tool.Surface_s(f) in surf_tag]
    print("softened edges", done, "unfilleted", failed)
    return body


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
    parts = {}
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
    # the intake is a black panel set back ~40 mm; fins and a V blade sit in front of it
    blades = None
    for pts, cs in (FT.FIN, (([(-y, z) for y, z in FT.FIN[0]]), FT.FIN[1]), FT.VBLADE):
        b_ = common(common(outline_prism(pts, cs, 'yz', -40, 500), itool), core)
        blades = b_ if blades is None else fuse(blades, b_)
    grille = keep_solids(cut(common(itool, inner_body(core)), blades), 1e5)
    parts["Front_grille"] = (grille, 'dark')
    parts["Intake_blades"] = (keep_solids(blades, 1e3), 'trim')
    print("intake", valid(body.shape))
    # rear recess + diffuser with fins
    L = B.LENGTH
    body.cut(outline_prism(*FT.REAR_RECESS, 'yz', L - 140, L + 50), 'dark')
    dtool = outline_prism(*FT.DIFFUSER, 'yz', L - 320, L + 50)
    body.cut(dtool, 'dark')
    fins = None
    for y in FT.DIFF_FINS_Y:
        plate = poly_prism([(L - 320, y - 6), (L + 10, y - 6), (L + 10, y + 6), (L - 320, y + 6)], 'xy', -10, 400)
        f_ = common(common(plate, dtool), core)
        fins = f_ if fins is None else fuse(fins, f_)
    parts["Diffuser_fins"] = (keep_solids(fins, 1e3), 'fin')
    if not valid(body.shape):
        body.fix()
    print("rear", valid(body.shape))
    soften(body)
    print("softened", valid(body.shape))
    # splitter lip under the nose, sitting flush against the floor
    sp = outline_prism(*FT.SPLITTER, 'xy', 58, 110)
    parts["Front_splitter"] = (keep_solids(cut(sp, core), 1e3), 'dark')

    # skins laid over the body (the body is not cut): (outset loft x region) - (body x region)
    grown = {}

    def skin(region_ops, d):
        if d not in grown:
            grown[d] = grown_body(core, d)
        outer, inner = grown[d], core
        for op in region_ops:
            outer, inner = common(outer, op), common(inner, op)
        return keep_solids(cut(outer, inner), 1e3)
    glass = skin([y_prism(*FT.CANOPY_GLASS, -1300, 1300),
                  outline_prism(*FT.GLASS_PLAN, 'xy', 500, 1500)], 5.0)
    parts["Glazing"] = (glass, 'glass')
    print("glass", valid(glass), "%.1f L" % (volume(glass) / 1e6))
    hf = outline_prism(*FT.HEAD_FRONT, 'yz', -100, 1400)
    lamps = skin([outline_prism(*FT.HEAD_SIDE, 'xz', -1300, 1300), fuse(hf, mirror_y(hf))], 3.0)
    parts["Headlamps"] = (lamps, 'lamp')
    duct = skin([y_prism(*FT.DUCT, -1300, 1300)], 4.0)
    parts["Side_ducts"] = (duct, 'dark')
    sill = None
    for y0, y1 in ((600, 1300), (-1300, -600)):
        s_ = skin([outline_prism(*FT.SILL_BLADE, 'xz', y0, y1)], 4.0)
        sill = s_ if sill is None else fuse(sill, s_)
    parts["Sill_blades"] = (sill, 'dark')
    bar = skin([outline_prism(*FT.LIGHT_BAR, 'yz', L - 250, L + 50)], 4.0)
    parts["Tail_light"] = (bar, 'red')
    for k, (s_, t) in parts.items():
        print("  %-15s valid %s  %.2f L" % (k, valid(s_), volume(s_) / 1e6))
    body.fix(divide_closed=True)
    print("body valid", valid(body.shape), "faces", len(faces(body.shape)), "vol L %.0f" % (volume(body.shape) / 1e6))
    return body, parts


def wheel(xa, sgn):
    """Plain cylinder wheel, outer face at |y| = 1035, 305 mm wide."""
    w = 305.0
    y0 = sgn * 1035.0
    y1 = y0 - sgn * w
    return cyl_y(xa, B.WHEEL_Z, B.TIRE_R, min(y0, y1), max(y0, y1))


if __name__ == "__main__":
    from OCP.BRepTools import BRepTools
    import pickle
    body, parts = build()
    BRepTools.Write_s(body.shape, "out/body.brep")
    manifest = []
    for name, (shape, tag) in parts.items():
        path = "out/part_%s.brep" % name
        BRepTools.Write_s(shape, path)
        manifest.append((name, path, tag))
    pickle.dump(manifest, open("out/parts.pkl", "wb"))
    allf = faces(body.shape)
    lab = [body.tag_of(f) for f in allf]
    pickle.dump(lab, open("out/body_tags.pkl", "wb"))
    print("faces", len(allf), {t: lab.count(t) for t in set(lab)})
