import numpy as np, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Check
from OCP.TopTools import TopTools_ListOfShape
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.gp import gp_Pnt
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
A=rd("work/mz_P221_solid.brep"); B=rd("work/mz_solid_220.brep"); C=rd("work/mz_solid_222.brep")
def vol(s): p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); return p.Mass()
def count(s,t):
    n=0; ex=TopExp_Explorer(s,t)
    while ex.More(): n+=1; ex.Next()
    return n
print("volumes: P221 %.1f  220 %.1f  222 %.1f"%(vol(A),vol(B),vol(C)))
args=TopTools_ListOfShape(); args.Append(A); tools=TopTools_ListOfShape(); tools.Append(B); tools.Append(C)
fu=BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools); fu.SetFuzzyValue(1e-5); fu.Build()
print("fuse done:",fu.IsDone())
r=fu.Shape()
u=ShapeUpgrade_UnifySameDomain(r,True,True,True); u.Build(); r=u.Shape()
solids=[]; ex=TopExp_Explorer(r,TopAbs_SOLID)
while ex.More(): solids.append(ex.Current()); ex.Next()
print("result: solids",len(solids),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE))
so=solids[0]
print("valid:",BRepCheck_Analyzer(so).IsValid(),"| self-intersections:",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()))
print("volume %.1f  (P221 + 220 = %.1f; 222 is inside P221 so adds nothing)"%(vol(so),vol(A)+vol(B)))
b=Bnd_Box(); BRepBndLib.Add_s(so,b); print("bbox",[round(v,3) for v in b.Get()])
# outside unchanged: every mesh point of the result must lie on an original surface (P221, its cap, 220, 222)
BRepMesh_IncrementalMesh(so,0.2,False,0.3)
orig=TopTools_ListOfShape()
from OCP.TopoDS import TopoDS_Compound
cmp=TopoDS_Compound(); bb_=BRep_Builder(); bb_.MakeCompound(cmp)
for s in (A,B,C): bb_.Add(cmp,s)
worst=0; n=0; ex=TopExp_Explorer(so,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    if t is not None:
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//25)):
            p=t.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),cmp); d.Perform(); worst=max(worst,d.Value()); n+=1
    ex.Next()
print("checked %d surface points: max distance from original surfaces %.5f mm"%(n,worst))
BRepTools.Write_s(so,"work/muzzle_solid.brep")
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write("work/muzzle_solid.step")
