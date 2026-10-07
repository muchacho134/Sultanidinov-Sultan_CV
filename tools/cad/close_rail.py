import sys
from OCP.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import *
from OCP.BRepFill import BRepFill_Filling
from OCP.GeomAbs import GeomAbs_C0
from OCP.gp import gp_Trsf, gp_Vec
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
rail_path,p266,out=sys.argv[1:4]
r=STEPControl_Reader(); r.ReadFile(rail_path); r.TransferRoots(); s=r.OneShape()
e=TopExp_Explorer(s,TopAbs_SHELL); shell=e.Current()
t=TopoDS_Shape(); BRepTools.Read_s(t,p266,BRep_Builder())
tr=gp_Trsf(); tr.SetTranslation(gp_Vec(0,-0.4,0)); t=BRepBuilderAPI_Transform(t,tr,True).Shape()
def free_wires(sh,tol=1e-3):
    fb=ShapeAnalysis_FreeBounds(sh,tol); ws=[]
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More(): ws.append(TopoDS.Wire_s(ex.Current())); ex.Next()
    return ws
def one_shell(res):
    ex=TopExp_Explorer(res,TopAbs_SHELL); L=[]
    while ex.More(): L.append(ex.Current()); ex.Next()
    return L
# step 1: sew rail + moved 266
sw=BRepBuilderAPI_Sewing(0.05); sw.Add(shell); sw.Add(t); sw.Perform(); base=one_shell(sw.SewedShape())
print("after adding 266: shells",len(base),"free loops",[len(free_wires(x)) for x in base])
cur=base[0]
for i,w in enumerate(free_wires(cur)): pass
# step 2: patch every remaining loop
patches=[]; fails=[]
for i,w in enumerate(free_wires(cur)):
    face=None
    fp=BRepBuilderAPI_FindPlane(w,1e-2)
    if fp.Found():
        mf=BRepBuilderAPI_MakeFace(fp.Plane(),w)
        if mf.IsDone(): face=mf.Face(); kind="plane"
    if face is None:
        try:
            fl=BRepFill_Filling(3,15,2,False,1e-4,1e-3,0.1,0.01,8,9)
            ex=TopExp_Explorer(w,TopAbs_EDGE)
            while ex.More(): fl.Add(TopoDS.Edge_s(ex.Current()),GeomAbs_C0,True); ex.Next()
            fl.Build()
            if fl.IsDone(): face=fl.Face(); kind="fill"
        except Exception as ex_: fails.append((i,str(ex_)[:60]))
    if face is None: fails.append((i,"no face")); continue
    patches.append((i,kind,face))
print("patched",len(patches),"failed",fails)
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(cur)
for _,_,f in patches: sw.Add(f)
sw.Perform(); res=one_shell(sw.SewedShape())
print("after patching: shells",len(res),"free loops",[len(free_wires(x)) for x in res])
big=max(res,key=lambda x:len(list(range(1))) )
sh=res[0]
ms=BRepBuilderAPI_MakeSolid(); ms.Add(TopoDS.Shell_s(sh)); so=ms.Solid()
fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p)
print("solid valid:",BRepCheck_Analyzer(so).IsValid(),"volume: %.1f"%p.Mass())
b=Bnd_Box(); BRepBndLib.Add_s(so,b); print("bbox",[round(v,1) for v in b.Get()])
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write(out)
BRepTools.Write_s(so,out.replace(".step",".brep"))
