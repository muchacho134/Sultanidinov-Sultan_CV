import sys, json
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Shell, ShapeFix_Solid, ShapeFix_Shape
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Shell, TopoDS_Solid
from OCP.BRepLib import BRepLib

def free_loops(s, tol=1e-4):
    fb=ShapeAnalysis_FreeBounds(s,tol)
    m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o)
    return m.Extent(), o.Extent()

r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(TopoDS.Shell_s(it.Current())); it.Next()
res=[]
for i,s in enumerate(shells):
    nf=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,nf)
    row=dict(i=i,faces=nf.Extent(),before=free_loops(s))
    for tol in (1e-3,1e-2,1e-1,0.5):
        sew=BRepBuilderAPI_Sewing(tol); sew.Add(s); sew.Perform()
        out=sew.SewedShape()
        ex=TopExp_Explorer(out,TopAbs_SHELL); sh2=None
        shs=[]
        while ex.More(): shs.append(TopoDS.Shell_s(ex.Current())); ex.Next()
        row[f"sew{tol}"]=(len(shs),[free_loops(x)[0]+free_loops(x)[1] for x in shs][:3])
    res.append(row)
json.dump(res,open(sys.argv[2],'w'))
