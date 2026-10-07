import sys
exec(open("cmp.py").read().split("k=[x for x in B")[0].replace("A=load(sys.argv[1]); B=load(sys.argv[2])","A=load(sys.argv[1]); B=load(sys.argv[2])"))
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_AbscissaPoint
def flen(s):
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); L=0
    for i in range(1,m.Extent()+1):
        if m.FindFromIndex(i).Size()==1:
            try: L+=GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(TopoDS.Edge_s(m.FindKey(i))))
            except Exception: pass
    return L
for n in ("262","596","110","258"):
    k=[x for x in B if x.endswith(n)][0]; s=B[k]
    print(n,"| solid:",TopExp_Explorer(s,TopAbs_SOLID).More(),"| valid:",BRepCheck_Analyzer(s).IsValid(),"| open boundary %.0f mm"%flen(s))
