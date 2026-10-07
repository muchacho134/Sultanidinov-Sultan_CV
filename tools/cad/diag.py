import sys
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer, BRepCheck_ListOfStatus
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_IndexedDataMapOfShapeListOfShape
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
sh=TopoDS.Shell_s(TopExp_Explorer(s,TopAbs_SHELL).Current())
fb=ShapeAnalysis_FreeBounds(sh,1e-3)
for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
    ex=TopExp_Explorer(comp,TopAbs_WIRE)
    while ex.More():
        b=Bnd_Box(); BRepBndLib.Add_s(ex.Current(),b); print("free loop",[round(v,2) for v in b.Get()]); ex.Next()
# edge face counts
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(sh,TopAbs_EDGE,TopAbs_FACE,m)
from collections import Counter
print("edge face-count histogram:",Counter(m.FindFromIndex(i).Size() for i in range(1,m.Extent()+1)))
an=BRepCheck_Analyzer(s); print("valid:",an.IsValid())
# which subshapes are invalid
bad=Counter(); 
for t,nm in ((TopAbs_FACE,"face"),(TopAbs_EDGE,"edge"),(TopAbs_VERTEX,"vertex"),(TopAbs_WIRE,"wire"),(TopAbs_SHELL,"shell")):
    mm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,t,mm)
    for i in range(1,mm.Extent()+1):
        r=an.Result(mm.FindKey(i))
        if r is not None:
            st=r.Status()
            for x in st:
                if str(x)!="BRepCheck_Status.BRepCheck_NoError": bad[(nm,str(x).split('.')[-1])]+=1
print("invalid subshape statuses:",dict(bad))
