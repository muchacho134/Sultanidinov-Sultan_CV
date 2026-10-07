import numpy as np, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/x_P111.brep",BRep_Builder())
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); li=0
st=lambda t:str(t).split('.')[-1].replace("GeomAbs_","")
while ex.More():
    w=ex.Current(); b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=b.Get(); desc=[]; adj=collections.Counter()
    e2=TopExp_Explorer(w,TopAbs_EDGE)
    while e2.More():
        e=TopoDS.Edge_s(e2.Current()); c=BRepAdaptor_Curve(e); d=st(c.GetType())
        if c.GetType()==GeomAbs_Circle: d+="(R%.2f)"%c.Circle().Radius()
        desc.append(d)
        i=m.FindIndex(e)
        if i: 
            for f in m.FindFromIndex(i): a=BRepAdaptor_Surface(TopoDS.Face_s(f)); adj[st(a.GetType())+("(R%.2f)"%a.Cylinder().Radius() if a.GetType()==GeomAbs_Cylinder else "")]+=1
        e2.Next()
    print(f"loop {li}: z[{x[2]:.2f},{x[5]:.2f}] x[{x[0]:.2f},{x[3]:.2f}] y[{x[1]:.2f},{x[4]:.2f}] edges: {collections.Counter(desc)} | adjacent faces: {dict(adj)}"); li+=1; ex.Next()
print("--- faces")
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get(); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    w=0; e3=TopExp_Explorer(f,TopAbs_WIRE)
    while e3.More(): w+=1; e3.Next()
    extra=""
    if a.GetType()==GeomAbs_Cylinder: c=a.Cylinder(); extra="R%.2f ax(%.2f,%.2f,%.2f) loc(%.2f,%.2f,%.2f)"%(c.Radius(),c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z(),c.Location().X(),c.Location().Y(),c.Location().Z())
    if a.GetType()==GeomAbs_Plane: n=a.Plane().Axis().Direction(); extra="n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
    if p.Mass()>2: print(f"  {st(a.GetType()):8s} area {p.Mass():7.2f} wires {w} z[{x[2]:.2f},{x[5]:.2f}] {extra}")
    ex.Next()
