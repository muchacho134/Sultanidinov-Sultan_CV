import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
s=rd(sys.argv[1]); m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); n=0
for k in range(1,m.Extent()+1):
    ed=TopoDS.Edge_s(m.FindKey(k)); L=m.FindFromIndex(k)
    fs=list(L)
    if len(fs)==1 or (len(fs)==2 and fs[0].IsSame(fs[1]) and not BRep_Tool.IsClosed_s(ed,TopoDS.Face_s(fs[0]))):
        if BRep_Tool.Degenerated_s(ed): continue
        c=BRepAdaptor_Curve(ed); g=GProp_GProps(); BRepGProp.LinearProperties_s(ed,g); a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter())
        if len(fs)==1 and BRep_Tool.IsClosed_s(ed,TopoDS.Face_s(fs[0])): continue
        n+=1; print(" len %.3f tol %.4f (%.2f,%.2f,%.2f)->(%.2f,%.2f,%.2f)"%(g.Mass(),BRep_Tool.Tolerance_s(ed),a.X(),a.Y(),a.Z(),b.X(),b.Y(),b.Z()))
print(sys.argv[1],"edges on one face only:",n)
