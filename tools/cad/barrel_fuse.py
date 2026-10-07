import numpy as np
from OCP.TopoDS import TopoDS_Shape, TopoDS, TopoDS_Compound
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeVertex
from OCP.ShapeFix import ShapeFix_Solid
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
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
def vol(s): p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); return p.Mass()
def count(s,t):
    n=0; ex=TopExp_Explorer(s,t)
    while ex.More(): n+=1; ex.Next()
    return n
def close(shell):
    fb=ShapeAnalysis_FreeBounds(shell,1e-4); sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(shell); caps=[]
    ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
    while ex.More(): f=BRepBuilderAPI_MakeFace(TopoDS.Wire_s(ex.Current()),True).Face(); sw.Add(f); caps.append(f); ex.Next()
    sw.Perform(); sh=TopoDS.Shell_s(TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current())
    so=BRepBuilderAPI_MakeSolid(sh).Solid(); fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); return fx.Solid(),caps
pieces={}; caps=[]
for n in ("P159","P156"):
    so,c=close(rd(f"work/br_{n}.brep")); pieces[n]=so; caps+=c
    print(f"{n} capped -> valid {BRepCheck_Analyzer(so).IsValid()} volume {vol(so):.1f}")
for n in ("solid_158","solid_199","solid_153"): pieces[n]=rd(f"work/br_{n}.brep")
order=["solid_158","P159","solid_199","P156","solid_153"]
args=TopTools_ListOfShape(); args.Append(pieces[order[0]]); tools=TopTools_ListOfShape()
for n in order[1:]: tools.Append(pieces[n])
fu=BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools); fu.SetFuzzyValue(1e-5); fu.Build(); print("fuse done:",fu.IsDone())
u=ShapeUpgrade_UnifySameDomain(fu.Shape(),True,True,True); u.Build(); r=u.Shape()
print("result: solids",count(r,TopAbs_SOLID),"| shells",count(r,TopAbs_SHELL),"| faces",count(r,TopAbs_FACE))
so=TopExp_Explorer(r,TopAbs_SOLID).Current()
print("valid:",BRepCheck_Analyzer(so).IsValid(),"| self-intersections:",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()))
b=Bnd_Box(); BRepBndLib.Add_s(so,b); print("volume %.1f | bbox"%vol(so),[round(v,3) for v in b.Get()])
cmp=TopoDS_Compound(); bb_=BRep_Builder(); bb_.MakeCompound(cmp)
for s in pieces.values(): bb_.Add(cmp,s)
BRepMesh_IncrementalMesh(so,0.2,False,0.3); worst=0; n=0; ex=TopExp_Explorer(so,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    if t is not None:
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//40)):
            p=t.Node(i).Transformed(loc.Transformation()); d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),cmp); d.Perform(); worst=max(worst,d.Value()); n+=1
    ex.Next()
print("checked %d surface points: max distance from original surfaces %.5f mm"%(n,worst))
# show the barrel profile: radius along z from the result (outer envelope)
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write("work/barrel_solid.step"); BRepTools.Write_s(so,"work/barrel_solid.brep")
