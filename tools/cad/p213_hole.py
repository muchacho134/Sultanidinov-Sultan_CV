import numpy as np
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
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/x_P213.brep",BRep_Builder())
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE).Current()
ex=TopExp_Explorer(w,TopAbs_EDGE)
v=lambda p:np.round([p.X(),p.Y(),p.Z()],3)
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e); t=str(c.GetType()).split('.')[-1][8:]
    extra=""
    if c.GetType()==GeomAbs_Circle: ci=c.Circle(); extra=f"R{ci.Radius():.3f} centre{v(ci.Location())} axis{v(ci.Axis().Direction())}"
    f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); a=BRepAdaptor_Surface(f); st=str(a.GetType()).split('.')[-1][8:]
    if a.GetType()==GeomAbs_Cylinder: cy=a.Cylinder(); st+=f" R{cy.Radius():.3f} loc{v(cy.Location())} dir{v(cy.Axis().Direction())}"
    if a.GetType()==GeomAbs_Plane: st+=f" n{v(a.Plane().Axis().Direction())}"
    print(f"edge {t:8s} {v(c.Value(c.FirstParameter()))} -> {v(c.Value(c.LastParameter()))} {extra} | face: {st}")
    ex.Next()
print("--- cylinders of P213:")
ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if a.GetType()==GeomAbs_Cylinder:
        b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get(); cy=a.Cylinder(); nw=0; e2=TopExp_Explorer(f,TopAbs_WIRE)
        while e2.More(): nw+=1; e2.Next()
        print(f"  R{cy.Radius():.3f} loc{v(cy.Location())} z[{x[2]:.2f},{x[5]:.2f}] y[{x[1]:.2f},{x[4]:.2f}] wires {nw}")
    ex.Next()
