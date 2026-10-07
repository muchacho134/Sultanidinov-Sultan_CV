import sys, numpy as np, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
for n in sys.argv[1:]:
    s=TopoDS_Shape(); BRepTools.Read_s(s,f"work/x_{n}.brep",BRep_Builder()); print("==",n)
    rows=collections.Counter(); ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
        if a.GetType()==GeomAbs_Cylinder and p.Mass()>3:
            c=a.Cylinder(); d=c.Axis().Direction(); l=c.Location()
            print("   cyl R%.3f dir(%.2f,%.2f,%.2f) through(%.2f,%.2f) area %.1f z[%.2f,%.2f]"%(c.Radius(),d.X(),d.Y(),d.Z(),l.X(),l.Y(),p.Mass(),x[2],x[5]))
        if a.GetType()==GeomAbs_Plane and p.Mass()>20:
            nn=a.Plane().Axis().Direction(); print("   plane n(%.2f,%.2f,%.2f) area %.1f x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"%(nn.X(),nn.Y(),nn.Z(),p.Mass(),x[0],x[3],x[1],x[4],x[2],x[5]))
        ex.Next()
