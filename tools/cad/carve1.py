exec(open("work/finish244.py").read().split("s=rd(\"work/p244_solid9")[0])
from OCP.ShapeFix import ShapeFix_Shape
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
s=rd("work/p244_solid9.brep"); s=cut(s,[rd("work/slot_tool.brep")])
for n in ["P259","P223","P596","P256"]:
    t=cut(s,[rd(f"work/cur_{n}.brep")]); v=BRepCheck_Analyzer(t).IsValid()
    if not v:
        sf=ShapeFix_Shape(t); sf.Perform(); t2=sf.Shape(); print(n,"invalid; shapefix ->",BRepCheck_Analyzer(t2).IsValid()); t=t2
    print(n,"valid",BRepCheck_Analyzer(t).IsValid(),"vol %.1f"%vol(t))
    if BRepCheck_Analyzer(t).IsValid(): s=t
BRepTools.Write_s(s,"work/p244_final.brep"); print("final %.1f"%vol(s))
