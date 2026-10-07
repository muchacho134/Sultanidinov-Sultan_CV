import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRep import BRep_Tool
s=rd(sys.argv[1]); sw=BRepBuilderAPI_Sewing(float(sys.argv[3])); sw.Add(s); sw.Perform(); sh=sw.SewedShape()
mt=0; e=TopExp_Explorer(sh,TopAbs_EDGE)
while e.More(): mt=max(mt,BRep_Tool.Tolerance_s(TopoDS.Edge_s(e.Current()))); e.Next()
print(sh.ShapeType(),'loops',count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),'maxtol %.4f'%mt,'faces',count(sh,TopAbs_FACE)); BRepTools.Write_s(sh,sys.argv[2])
