import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SHELL
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
s=rd(sys.argv[1])
fb=ShapeAnalysis_FreeBounds(s,1e-4)
print("closed wires",count(fb.GetClosedWires(),TopAbs_EDGE),"open wires edges",count(fb.GetOpenWires(),TopAbs_EDGE))
print("shells",count(s,TopAbs_SHELL))
ex=TopExp_Explorer(s,TopAbs_SHELL); sh=TopoDS.Shell_s(ex.Current())
fs=ShapeFix_Shell(sh); fs.Perform(); sh=fs.Shell()
so=BRepBuilderAPI_MakeSolid(sh).Solid(); f=ShapeFix_Solid(so); f.Perform(); so=f.Solid()
print("valid",BRepCheck_Analyzer(so).IsValid(),"vol %.1f"%vol(so),"faces",count(so,TopAbs_FACE))
BRepTools.Write_s(so,sys.argv[2])
