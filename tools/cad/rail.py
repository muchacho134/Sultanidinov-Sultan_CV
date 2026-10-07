import sys, collections
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
objs=[]
for t in (TopAbs_SOLID,TopAbs_SHELL):
    it=TopExp_Explorer(sh,t,TopAbs_SOLID if t==TopAbs_SHELL else TopAbs_SHAPE)
    while it.More(): objs.append((t,it.Current())); it.Next()
for idx in (95,108,123,128,130,135,136,137,120):
    shells=[o for t,o in objs if t==TopAbs_SHELL]
    s=shells[idx]
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    print(idx,"bbox",[round(v,1) for v in x])
# rib analysis on shell 123 and 95, 108: planar faces normal ~Z
shells=[o for t,o in objs if t==TopAbs_SHELL]
for idx in (95,108,123):
    s=shells[idx]; zs=[]
    ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
        if a.GetType()==GeomAbs_Plane:
            n=a.Plane().Axis().Direction()
            if abs(n.Z())>0.99:
                b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
                zs.append((round(x[2],2),round((x[3]-x[0]),1),round(x[1],0)))
        ex.Next()
    zs.sort()
    print(idx,"Z-normal planar faces:",len(zs))
    print(zs[:60])
