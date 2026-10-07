import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(it.Current()); it.Next()
s=shells[123]
rib=[]
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if a.GetType()==GeomAbs_Plane:
        n=a.Plane().Axis().Direction()
        if abs(n.Z())>0.99:
            b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
            if abs((x[3]-x[0])-21.2)<0.3: rib.append((round(x[2],2),round(n.Z()),round(x[1],1),round(x[4],1)))
    ex.Next()
rib.sort(); print(len(rib))
prev=None
for z,nz,y0,y1 in rib:
    gap=None if prev is None else round(z-prev,2)
    print(z,nz,y0,y1,"gap",gap, "<<<" if gap and gap>5.5 else "")
    prev=z
