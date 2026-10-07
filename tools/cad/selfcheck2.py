import sys
from collections import Counter
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
c=BRepAlgoAPI_Check(s,True,True)
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
small=0; big=0; zs=[]; names=Counter()
for it in c.Result():
    for sh in (it.GetCheckedShape1(),it.GetCheckedShape2()):
        if sh.IsNull(): continue
        names[str(sh.ShapeType()).split('.')[-1]]+=1
        if sh.ShapeType()==TopAbs_FACE:
            b=Bnd_Box(); BRepBndLib.Add_s(sh,b); x=b.Get(); zs.append(round((x[2]+x[5])/2,0))
print("involved shape types:",dict(names))
import statistics
print("z of involved faces: min",min(zs),"max",max(zs),"distinct",len(set(zs)))
