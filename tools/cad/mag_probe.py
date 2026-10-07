import sys, numpy as np, collections
exec(open("probe3.py").read().split("for n in sys.argv[2:]:")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
def info(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=np.array(b.Get())
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    ty=collections.Counter(str(BRepAdaptor_Surface(TopoDS.Face_s(fm.FindKey(i))).GetType()).split('.')[-1][8:] for i in range(1,fm.Extent()+1))
    fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,w)
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
    return x,fm.Extent(),dict(ty),w.Extent(),p.Mass()
mag=P["P256"]; mx,_,mt,ml,_=info(mag); print("MAGAZINE P256: bbox x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f] faces %s open loops %d"%(mx[0],mx[3],mx[1],mx[4],mx[2],mx[5],mt,ml))
BRepTools.Write_s(mag,"work/x_P256.brep")
rows=[]
for n,s in P.items():
    if n=="P256": continue
    x,nf,ty,nl,ar=info(s)
    # within the magazine footprint in x/z (+-3 mm) and between the mag top and the bore
    if x[0]>mx[0]-3 and x[3]<mx[3]+3 and x[2]>mx[2]-15 and x[5]<mx[5]+15 and x[1]>-300 and x[4]<-240:
        rows.append((n,nf,ty,nl,ar,x)); BRepTools.Write_s(s,f"work/x_{n}.brep")
rows.sort(key=lambda r:r[5][1])
print("parts above/inside the magazine footprint:")
for n,nf,ty,nl,ar,x in rows: print("  %-10s faces %3d %-45s loops %d area %7.1f  x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"%(n,nf,str(ty)[:45],nl,ar,x[0],x[3],x[1],x[4],x[2],x[5]))
