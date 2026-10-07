import sys
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'work/Gun_merged.step'"))
from OCP.BRepCheck import BRepCheck_Analyzer
print("parts:",len(parts)," has 114:",any(k.endswith('114') for k in parts))
s=parts["solid_131"][0]; p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p)
print("solid_131 type:",str(s.ShapeType()).split('.')[-1],"| valid:",BRepCheck_Analyzer(s).IsValid(),"| volume %.2f"%p.Mass())
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
fb=ShapeAnalysis_FreeBounds(s,1e-4); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m); print("open edges loops:",m.Extent())
