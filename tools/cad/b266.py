import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); s=r.OneShape()
e=TopExp_Explorer(s,TopAbs_SHELL); shell=e.Current()
t=TopoDS_Shape(); BRepTools.Read_s(t,sys.argv[2],BRep_Builder())
fb=ShapeAnalysis_FreeBounds(shell,1e-3)
loops=[]
for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
    ex=TopExp_Explorer(comp,TopAbs_WIRE)
    while ex.More(): loops.append(TopoDS.Wire_s(ex.Current())); ex.Next()
# 266 edges
ex=TopExp_Explorer(t,TopAbs_EDGE); k=0
while ex.More():
    ed=TopoDS.Edge_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(ed,b); x=[round(v,1) for v in b.Get()]
    best=min(((lambda d:(d.Perform(),d.Value())[1])(BRepExtrema_DistShapeShape(ed,w)),i) for i,w in enumerate(loops))
    print("266 edge",k,x,"nearest loop",best[1],"dist %.2f"%best[0]); k+=1; ex.Next()
