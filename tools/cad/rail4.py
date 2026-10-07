import sys, collections
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
nm={GeomAbs_Plane:'pl',GeomAbs_Cylinder:'cy',GeomAbs_Cone:'co',GeomAbs_Torus:'to',GeomAbs_BSplineSurface:'bs'}
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(it.Current()); it.Next()
s=shells[123]
def window(z0,z1,ytop):
    out=[]
    ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
        if x[2]>=z0-0.01 and x[5]<=z1+0.01 and x[4]>=ytop:
            a=BRepAdaptor_Surface(f); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
            n=a.Plane().Axis().Direction() if a.GetType()==GeomAbs_Plane else None
            out.append((nm.get(a.GetType(),'?'),round(p.Mass(),1),tuple(round(v,1) for v in x),None if n is None else (round(n.X()),round(n.Y()),round(n.Z()))))
        ex.Next()
    return out
for name,(z0,z1) in {"gap":(-15,45),"ref(-75..-15)":(-75,-15),"ref(45..105)":(45,105)}.items():
    w=window(z0,z1,-226)
    print("==",name,"faces in window (top-of-rail region y>-226):",len(w))
    print("  types:",collections.Counter(t for t,*_ in w))
    if name!="ref(45..105)": 
        for t in sorted(w,key=lambda q:q[2][2])[:40]: print("  ",t)
