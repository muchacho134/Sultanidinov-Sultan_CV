import numpy as np, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.BRepBuilderAPI import BRepBuilderAPI_FindPlane
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
import sys
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); i=0
st=lambda t:str(t).split('.')[-1].replace("GeomAbs_","")
while ex.More():
    w=ex.Current(); b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=b.Get(); ec=collections.Counter(); fc=collections.Counter(); e2=TopExp_Explorer(w,TopAbs_EDGE)
    while e2.More():
        e=TopoDS.Edge_s(e2.Current()); c=BRepAdaptor_Curve(e); d=st(c.GetType())
        if c.GetType()==GeomAbs_Circle: d+="R%.2f"%c.Circle().Radius()
        ec[d]+=1
        for f in m.FindFromIndex(m.FindIndex(e)):
            a=BRepAdaptor_Surface(TopoDS.Face_s(f)); t=st(a.GetType())
            if a.GetType()==GeomAbs_Cylinder: t+="R%.2f"%a.Cylinder().Radius()
            fc[t]+=1
        e2.Next()
    fp=BRepBuilderAPI_FindPlane(w,1e-3)
    print(f"loop {i}: x[{x[0]:.2f},{x[3]:.2f}] y[{x[1]:.2f},{x[4]:.2f}] z[{x[2]:.2f},{x[5]:.2f}] planar={fp.Found()} edges {dict(ec)} | neighbours {dict(fc)}"); i+=1; ex.Next()
