exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Ax2, gp_Dir
so=rd("work/p244_pre223.brep"); print("pre vol %.1f valid %s"%(vol(so),V(so)))
for zend in [296.63]:
  cyl=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,240.0),gp_Dir(0,0,1)),17.55,zend-240.0).Shape()
  for y0 in [-283.1]:
    box=BRepPrimAPI_MakeBox(gp_Pnt(-30,y0,239),gp_Pnt(30,-240,zend+1)).Shape()
    tool=BRepAlgoAPI_Common(cyl,box).Shape()
    for fz in [0.0,0.001,0.005]:
        t=cut(so,[tool],fz); ok=t is not None and V(t)
        print(zend,y0,fz,"valid",ok,"vol %.1f"%(vol(t) if t is not None else 0),"faces",count(t,TopAbs_FACE) if t is not None else 0)
        if ok: BRepTools.Write_s(t,"work/p244_cradle.brep"); BRepTools.Write_s(tool,"work/cradle_tool.brep"); raise SystemExit
