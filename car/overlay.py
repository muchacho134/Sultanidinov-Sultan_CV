"""Overlay a model on the reference sheet: silhouette (red) + B-rep edges (blue) per view,
plus a shaded 4-view render."""
import sys, numpy as np
from PIL import Image, ImageDraw
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.STEPControl import STEPControl_Reader
import body as B

REF = sys.argv[3] if len(sys.argv) > 3 else "/tmp/claude-0/-home-user-Sultanidinov-Sultan-CV/a2c31b01-d1a6-59f7-9950-593ea88b0041/images/1.webp"
FS, RS = 4.235, 4.11
TOP_SY = 1046 / 185.0
VIEWS = {  # name: (function mapping xyz -> px,py, depth direction)
    'side': (lambda P: np.c_[B.PX0 + P[:, 0] / B.S, B.GROUND - P[:, 2] / B.S], np.array([0, 1, 0])),
    'front': (lambda P: np.c_[1476 - P[:, 1] / FS, 361 - P[:, 2] / FS], np.array([1, 0, 0])),
    'rear': (lambda P: np.c_[1476 + P[:, 1] / RS, 770 - P[:, 2] / RS], np.array([-1, 0, 0])),
    'top': (lambda P: np.c_[B.PX0 + P[:, 0] / B.S, 617 - P[:, 1] / TOP_SY], np.array([0, 0, -1])),
}


def load(path):
    if path.endswith('.step') or path.endswith('.stp'):
        r = STEPControl_Reader(); r.ReadFile(path); r.TransferRoots(); return r.OneShape()
    s = TopoDS_Shape(); BRepTools.Read_s(s, path, BRep_Builder()); return s


def mesh(s, defl=1.5):
    BRepMesh_IncrementalMesh(s, defl, False, 0.25, True)
    V, F, off = [], [], 0
    e = TopExp_Explorer(s, TopAbs_FACE)
    while e.More():
        f = TopoDS.Face_s(e.Current()); loc = TopLoc_Location()
        t = BRep_Tool.Triangulation_s(f, loc)
        if t is not None:
            tr = loc.Transformation()
            for i in range(1, t.NbNodes() + 1):
                p = t.Node(i).Transformed(tr); V.append((p.X(), p.Y(), p.Z()))
            rev = f.Orientation() == TopAbs_REVERSED
            for i in range(1, t.NbTriangles() + 1):
                a, b, c = t.Triangle(i).Get()
                F.append((off + a - 1, off + c - 1, off + b - 1) if rev else (off + a - 1, off + b - 1, off + c - 1))
            off += t.NbNodes()
        e.Next()
    return np.array(V), np.array(F)


def edges(s):
    out = []
    e = TopExp_Explorer(s, TopAbs_EDGE)
    while e.More():
        ed = TopoDS.Edge_s(e.Current())
        if not BRep_Tool.Degenerated_s(ed):
            c = BRepAdaptor_Curve(ed)
            d = GCPnts_QuasiUniformDeflection(c, 0.5)
            if d.IsDone() and d.NbPoints() > 1:
                out.append(np.array([[d.Value(i).X(), d.Value(i).Y(), d.Value(i).Z()] for i in range(1, d.NbPoints() + 1)]))
        e.Next()
    return out


def overlay(s, out):
    V, F = mesh(s)
    E = edges(s)
    im = Image.open(REF).convert('L').convert('RGB')
    im = Image.blend(im, Image.new('RGB', im.size, 'white'), 0.35)
    d = ImageDraw.Draw(im)
    for name, (f, dirv) in VIEWS.items():
        P = f(V)
        mask = Image.new('L', im.size, 0); md = ImageDraw.Draw(mask)
        for tri in F:
            md.polygon([tuple(P[i]) for i in tri], fill=255)
        m = np.array(mask) > 0
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        a = np.array(im); a[edge] = (230, 0, 0); im = Image.fromarray(a); d = ImageDraw.Draw(im)
        for pts in E:
            # only draw edges on the visible half for side/top
            if name == 'side' and pts[:, 1].mean() < -1: continue
            if name == 'top' and pts[:, 2].mean() < 150: continue
            q = f(pts)
            d.line([tuple(p) for p in q], fill=(0, 90, 255), width=1)
    im.save(out)


if __name__ == "__main__":
    s = load(sys.argv[1]); overlay(s, sys.argv[2])
