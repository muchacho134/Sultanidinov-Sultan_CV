import sys
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_Sewing
from OCP.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
sh=TopoDS_Shape(); BRepTools.Read_s(sh,sys.argv[1],BRep_Builder())
e=TopExp_Explorer(sh,TopAbs_SHELL); shell=e.Current()
tr=gp_Trsf(); tr.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0)))
M=BRepBuilderAPI_Transform(shell,tr,True).Shape()
def faces(s):
    L=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def key(f):
    b=Bnd_Box(); BRepBndLib.Add_s(f,b); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    return [round(v,2) for v in b.Get()],round(p.Mass(),2)
F=faces(shell); Fm=faces(M)
orig=[key(f) for f in F]
def same(k1,k2): return all(abs(a-b)<0.05 for a,b in zip(k1[0],k2[0])) and abs(k1[1]-k2[1])<0.1
newf=[]
for f in Fm:
    k=key(f)
    if not any(same(k,o) for o in orig): newf.append((f,k))
print("faces:",len(F),"mirrored faces with no equivalent in original:",len(newf))
ws=sum(1 for _,k in newf if k[1]<1)
for f,k in sorted(newf,key=lambda q:q[1][0][0])[:60]: print(k)
import pickle
BRepTools.Write_s(shell,sys.argv[2])
b=BRep_Builder(); from OCP.TopoDS import TopoDS_Compound
c=TopoDS_Compound(); b.MakeCompound(c)
for f,_ in newf: b.Add(c,f)
BRepTools.Write_s(c,sys.argv[3])
