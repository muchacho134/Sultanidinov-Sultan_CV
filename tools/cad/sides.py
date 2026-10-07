import numpy as np, collections
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/shell_a.brep",BRep_Builder())
rows=[]
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t=a.GetType()
    b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get(); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    nw=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_WIRE,nw)
    nx=None
    if t==GeomAbs_Plane: nx=a.Plane().Axis().Direction().X()
    rows.append(dict(t=str(t).split('.')[-1][8:],bbox=x,area=p.Mass(),nw=nw.Extent(),nx=nx,cx=(x[0]+x[3])/2)); ex.Next()
print("faces:",len(rows))
big=[r for r in rows if r['t']=='Plane' and abs(r['nx'])>0.99 and r['area']>20]
for side,sg in (("+x",1),("-x",-1)):
    L=[r for r in big if np.sign(r['cx'])==sg]
    print(side,"big x-normal planes:",len(L))
    for r in sorted(L,key=lambda r:-r['area'])[:8]: print("  x=%.2f area=%.1f wires=%d z[%.0f..%.0f] y[%.0f..%.0f]"%(r['cx'],r['area'],r['nw'],r['bbox'][2],r['bbox'][5],r['bbox'][1],r['bbox'][4]))
# slot-like faces (planes/cyls with small area) by x-side beyond |x|>13
for side,sg in (("+x",1),("-x",-1)):
    L=[r for r in rows if np.sign(r['cx'])==sg and abs(r['cx'])>13]
    print(side,"faces with |x|>13:",len(L),collections.Counter(r['t'] for r in L), "total area %.0f"%sum(r['area'] for r in L))
