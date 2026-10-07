exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
s=rd("work/x_P110.brep")
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
def desc(f):
    a=BRepAdaptor_Surface(f); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    t=str(a.GetType()).split('.')[-1][8:]
    if a.GetType()==GeomAbs_Cylinder: c=a.Cylinder(); t+=" R%.2f dir(%.2f,%.2f,%.2f)"%(c.Radius(),c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z())
    if a.GetType()==GeomAbs_Plane: n=a.Plane().Axis().Direction(); t+=" n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
    return "%s area %.2f x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(t,p.Mass(),x[0],x[3],x[1],x[4],x[2],x[5])

from OCP.TopTools import TopTools_IndexedMapOfShape
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    if x[0]>-9 and x[3]<9 and x[1]>-253 and x[4]<-234 and x[2]>-237 and x[5]<-226:
        w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_WIRE,w)
        free=sum(1 for e in [m.FindKey(i) for i in range(1,m.Extent()+1)] if False)
        print(" ",desc(f),"| wires",w.Extent(), "| orient",str(f.Orientation()).split('.')[-1][7:])
    ex.Next()
