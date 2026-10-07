exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
s=rd("work/x_P110.brep")
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); li=0
def desc(f):
    a=BRepAdaptor_Surface(f); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    t=str(a.GetType()).split('.')[-1][8:]
    if a.GetType()==GeomAbs_Cylinder: c=a.Cylinder(); t+=" R%.2f dir(%.2f,%.2f,%.2f)"%(c.Radius(),c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z())
    if a.GetType()==GeomAbs_Plane: n=a.Plane().Axis().Direction(); t+=" n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
    return "%s area %.2f x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(t,p.Mass(),x[0],x[3],x[1],x[4],x[2],x[5])
while ex.More():
    w=ex.Current(); print("loop",li); e2=TopExp_Explorer(w,TopAbs_EDGE); seen=set()
    while e2.More():
        e=TopoDS.Edge_s(e2.Current())
        for f in m.FindFromIndex(m.FindIndex(e)):
            h=f.HashCode(10**9) if hasattr(f,'HashCode') else id(f)
            print("   adjacent:",desc(TopoDS.Face_s(f)))
        e2.Next()
    li+=1; ex.Next()
# faces lying in the plane z=-231.4 and z=-215
print("--- faces in plane z=-231.4 or z=-215:")
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    if (abs(x[2]+231.4)<0.02 and abs(x[5]+231.4)<0.02) or (abs(x[2]+215)<0.02 and abs(x[5]+215)<0.02): print("  ",desc(f))
    ex.Next()
