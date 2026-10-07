import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
def nloops(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-3); m=TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m); o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o)
    return m.Extent()+o.Extent()
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(TopoDS.Shell_s(it.Current())); it.Next()
for tol in (1e-3,1e-2,0.1):
    sew=BRepBuilderAPI_Sewing(tol)
    for s in shells: sew.Add(s)
    sew.Perform(); out=sew.SewedShape()
    ex=TopExp_Explorer(out,TopAbs_SHELL); n=0; closed=0; good=0; openl=0
    while ex.More():
        s=TopoDS.Shell_s(ex.Current()); n+=1
        if nloops(s)==0:
            closed+=1
            so=BRepBuilderAPI_MakeSolid(s).Solid(); f=ShapeFix_Solid(); f.Init(so); f.Perform(); so=f.Solid()
            p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p)
            if p.Mass()>1e-3 and BRepCheck_Analyzer(so).IsValid(): good+=1
        else: openl+=nloops(s)
        ex.Next()
    print(f"tol={tol}: shells_after={n} closed={closed} (valid positive solids={good}) remaining_free_loops={openl}")
