import sys, json
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE, TopAbs_COMPOUND
from OCP.TopExp import TopExp_Explorer
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds, ShapeAnalysis_Shell
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE
from OCP.ShapeAnalysis import ShapeAnalysis_Edge
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.Message import Message_ProgressRange

r = STEPControl_Reader()
st = r.ReadFile(sys.argv[1])
print("read status", st == IFSelect_RetDone)
r.TransferRoots()
print("nbShapes", r.NbShapes())
shape = r.OneShape()
rows = []
exp = TopExp_Explorer(shape, TopAbs_SOLID)
i = 0
while exp.More():
    s = TopoDS.Solid_s(exp.Current())
    a = BRepCheck_Analyzer(s)
    valid = a.IsValid()
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s, p)
    vol = p.Mass()
    b = Bnd_Box(); BRepBndLib.Add_s(s, b)
    nf = TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s, TopAbs_FACE, nf)
    ne = TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s, TopAbs_EDGE, ne)
    nsh = TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s, TopAbs_SHELL, nsh)
    # free edges
    free = 0
    try:
        sa = ShapeAnalysis_FreeBounds(s, 1e-4)
        from OCP.TopTools import TopTools_IndexedMapOfShape as M
        fm = M(); TopExp.MapShapes_s(sa.GetClosedWires(), TopAbs_EDGE, fm)
        fo = M(); TopExp.MapShapes_s(sa.GetOpenWires(), TopAbs_EDGE, fo)
        free = (fm.Extent(), fo.Extent())
    except Exception as e:
        free = str(e)
    rows.append(dict(i=i, valid=valid, vol=vol, faces=nf.Extent(), edges=ne.Extent(), shells=nsh.Extent(), free=free, bbox=b.Get() if not b.IsVoid() else None))
    i += 1
    exp.Next()
json.dump(rows, open(sys.argv[2], 'w'))
print("solids", len(rows), "valid", sum(r['valid'] for r in rows), "invalid", sum(not r['valid'] for r in rows))
