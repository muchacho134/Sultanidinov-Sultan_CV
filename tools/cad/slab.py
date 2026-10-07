import numpy as np, collections
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/shell_a.brep",BRep_Builder())
rows=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=np.array(b.Get()); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    rows.append((x,p.Mass(),str(BRepAdaptor_Surface(f).GetType()).split('.')[-1][8:])); ex.Next()
def inslab(x,sg): return (sg*x[0]>=6.3 and sg*x[3]<=12.2 and sg*x[3]>=6.3 and x[1]>=-245.5 and x[4]<=-230.4) if sg>0 else (x[3]<=-6.3 and x[0]>=-12.2 and x[1]>=-245.5 and x[4]<=-230.4)
for sg,nm in ((1,"+x"),(-1,"-x")):
    L=[r for r in rows if inslab(r[0],sg)]
    zc=sorted(set(round((r[0][2]+r[0][5])/2/31.1) for r in L))
    print(nm,"slab faces:",len(L),collections.Counter(r[2] for r in L),"area %.0f"%sum(r[1] for r in L))
    # window count: group by z centre of the slanted wall faces
    zs=sorted(round((r[0][2]+r[0][5])/2) for r in L if r[1]>30)
    print("   z of larger faces:",zs[:30])
