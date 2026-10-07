import sys
exec(open("p110_sec.py").read().split("A=rd(")[0])
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepTools import BRepTools_WireExplorer
S=rd(sys.argv[1]); want=[int(a) for a in sys.argv[2].split(",")]
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(S,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(S,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); k=0
while ex.More():
    if k in want:
        print("=== loop",k)
        we=BRepTools_WireExplorer(TopoDS.Wire_s(ex.Current()))
        while we.More():
            e=we.Current(); c=BRepAdaptor_Curve(e); a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter()); t=c.GetType()
            ts="LINE" if t==GeomAbs_Line else (f"ARC R{c.Circle().Radius():.2f}" if t==GeomAbs_Circle else str(t).split('.')[-1][10:])
            f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); st=str(BRepAdaptor_Surface(f).GetType()).split('.')[-1][8:]
            print(f"  ({a.X():7.2f},{a.Y():8.2f},{a.Z():7.2f}) -> ({b.X():7.2f},{b.Y():8.2f},{b.Z():7.2f}) {ts:12s} on {st}")
            we.Next()
    k+=1; ex.Next()
