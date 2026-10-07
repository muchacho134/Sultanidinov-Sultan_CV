import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_IndexedDataMapOfShapeListOfShape
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_FindPlane, BRepBuilderAPI_MakeFace
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import *
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); s=r.OneShape()
e=TopExp_Explorer(s,TopAbs_SHELL); shell=e.Current()
fb=ShapeAnalysis_FreeBounds(shell,1e-3)
ws=[]
ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More(): ws.append(TopoDS.Wire_s(ex.Current())); ex.Next()
ex=TopExp_Explorer(fb.GetOpenWires(),TopAbs_WIRE)
while ex.More(): ws.append(TopoDS.Wire_s(ex.Current())); ex.Next()
ct={GeomAbs_Line:'L',GeomAbs_Circle:'C',GeomAbs_BSplineCurve:'B',GeomAbs_Ellipse:'E'}
print("loops:",len(ws))
for i,w in enumerate(ws):
    b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=[round(v,1) for v in b.Get()]
    ne=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(w,TopAbs_EDGE,ne)
    kinds={}
    for k in range(1,ne.Extent()+1):
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ne.FindKey(k))); kinds[ct.get(c.GetType(),'?')]=kinds.get(ct.get(c.GetType(),'?'),0)+1
    fp=BRepBuilderAPI_FindPlane(w,1e-3)
    pl="planar n=(%g,%g,%g) y/off=%.2f"%(round(fp.Plane().Axis().Direction().X(),2),round(fp.Plane().Axis().Direction().Y(),2),round(fp.Plane().Axis().Direction().Z(),2),fp.Plane().Location().Y()) if fp.Found() else "NON-planar"
    print(i,x,"edges",ne.Extent(),kinds,pl)
