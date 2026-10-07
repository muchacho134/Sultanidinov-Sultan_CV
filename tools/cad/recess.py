exec(open("p110_diag.py").read().split("fb=ShapeAnalysis_FreeBounds")[0])
from OCP.TopTools import TopTools_IndexedMapOfShape
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    if x[0]>-9 and x[3]<9 and x[1]>-253 and x[4]<-234 and x[2]>-237 and x[5]<-226:
        w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_WIRE,w)
        free=sum(1 for e in [m.FindKey(i) for i in range(1,m.Extent()+1)] if False)
        print(" ",desc(f),"| wires",w.Extent(), "| orient",str(f.Orientation()).split('.')[-1][7:])
    ex.Next()
