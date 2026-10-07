exec(open("recess2.py").read().split("from OCP.TopTools import TopTools_IndexedMapOfShape")[0])
from OCP.BRepAdaptor import BRepAdaptor_Curve
for i in range(1,m.Extent()+1):
    e=TopoDS.Edge_s(m.FindKey(i)); c=BRepAdaptor_Curve(e)
    if c.GetType()!=GeomAbs_Circle: continue
    ci=c.Circle(); L=ci.Location()
    if abs(L.X())<0.05 and abs(L.Y()+243.9)<0.05 and -235.1<L.Z()<-226 and ci.Radius()>5:
        fl=m.FindFromIndex(i); print("circle R%.3f z=%.2f  arc %.0f deg | faces %d:"%(ci.Radius(),L.Z(),abs(c.LastParameter()-c.FirstParameter())*57.3,fl.Size()))
        for f in fl: print("       ",desc(TopoDS.Face_s(f)))
