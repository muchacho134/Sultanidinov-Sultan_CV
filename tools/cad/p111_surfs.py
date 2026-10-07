import numpy as np
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
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/x_P111.brep",BRep_Builder())
v=lambda p:np.array([p.X(),p.Y(),p.Z()])
ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t=a.GetType(); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    if p.Mass()>2:
        if t==GeomAbs_Plane: pl=a.Plane(); d=f"PLANE pt{np.round(v(pl.Location()),3)} n{np.round(v(pl.Axis().Direction()),4)}"
        elif t==GeomAbs_Cylinder: c=a.Cylinder(); d=f"CYL R{c.Radius():.4f} loc{np.round(v(c.Location()),3)} dir{np.round(v(c.Axis().Direction()),4)}"
        elif t==GeomAbs_Cone: c=a.Cone(); d=f"CONE refR{c.RefRadius():.4f} semi{np.degrees(c.SemiAngle()):.3f} loc{np.round(v(c.Location()),3)} dir{np.round(v(c.Axis().Direction()),4)} apex{np.round(v(c.Apex()),3)}"
        else: d=str(t)
        print(f"{i:2d} area {p.Mass():7.2f} {str(f.Orientation()).split('.')[-1][7:]:8s} {d}  bbox z[{x[2]:.2f},{x[5]:.2f}]")
    i+=1; ex.Next()
