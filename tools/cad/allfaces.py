import sys, numpy as np
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
v=lambda p:"(%.2f,%.2f,%.2f)"%(p.X(),p.Y(),p.Z())
ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t=a.GetType(); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_WIRE,w)
    if t==GeomAbs_Plane: d="PLANE n"+v(a.Plane().Axis().Direction())
    elif t==GeomAbs_Cylinder: c=a.Cylinder(); d="CYL R%.3f dir%s loc%s"%(c.Radius(),v(c.Axis().Direction()),v(c.Location()))
    elif t==GeomAbs_Cone: c=a.Cone(); d="CONE semi%.1f refR%.3f dir%s apex%s"%(np.degrees(c.SemiAngle()),c.RefRadius(),v(c.Axis().Direction()),v(c.Apex()))
    elif t==GeomAbs_Torus: c=a.Torus(); d="TORUS R%.3f r%.3f dir%s loc%s"%(c.MajorRadius(),c.MinorRadius(),v(c.Axis().Direction()),v(c.Location()))
    else: d=str(t).split('.')[-1]
    print("%2d %-62s area %7.1f w%d x[%6.2f,%6.2f] y[%7.2f,%7.2f] z[%6.2f,%6.2f]"%(i,d,p.Mass(),w.Extent(),x[0],x[3],x[1],x[4],x[2],x[5])); i+=1; ex.Next()
