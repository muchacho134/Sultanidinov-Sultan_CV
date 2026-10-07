from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
a=rd("work/x_P110.brep"); b=rd("work/x_P213.brep")
d=BRepExtrema_DistShapeShape(a,b); d.Perform(); print("min distance P110 <-> P213: %.4f mm"%d.Value(), "| contact points:",d.NbSolution())
