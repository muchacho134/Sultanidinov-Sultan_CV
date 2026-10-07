import numpy as np
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
O=np.array([4.74,-241.16,-237.85]); A=np.array([0.866,0.5,0.0]); A/=np.linalg.norm(A)
for nm in ("work/s131_new.brep","work/s114_fixed.brep"):
    s=rd(nm); ex=TopExp_Explorer(s,TopAbs_FACE); print(nm)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); a=BRepAdaptor_Surface(f)
        c=p.CentreOfMass(); t=(np.array([c.X(),c.Y(),c.Z()])-O)@A
        print("  ",str(a.GetType()).split('.')[-1][8:],"area %.3f"%p.Mass(),"centroid t=%.2f"%t,"orient",str(f.Orientation()).split('.')[-1]); ex.Next()
