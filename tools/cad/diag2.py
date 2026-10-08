exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.gp import gp_Ax2, gp_Dir, gp_Pln, gp_Vec
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
so=rd("work/p244_pre223.brep"); P=rd("work/cur_P223.brep")
upper=BRepAlgoAPI_Common(P,BRepPrimAPI_MakeBox(gp_Pnt(-25,-283.0,250),gp_Pnt(25,-240,300)).Shape()).Shape()
# lug footprint at y=-283.0 (z>=250)
pl=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,-283.0,0),gp_Dir(0,1,0)),-1000,1000,-1000,1000).Face()
foot=BRepAlgoAPI_Common(BRepAlgoAPI_Common(P,BRepPrimAPI_MakeBox(gp_Pnt(-25,-290,250),gp_Pnt(25,-240,300)).Shape()).Shape(),pl).Shape()
ex=TopExp_Explorer(foot,TopAbs_FACE); prisms=[]
while ex.More():
    g=GProp_GProps(); BRepGProp.SurfaceProperties_s(ex.Current(),g); print("foot face area %.1f"%g.Mass())
    prisms.append(BRepPrimAPI_MakePrism(ex.Current(),gp_Vec(0,-0.1,0)).Shape()); ex.Next()
bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,245),gp_Dir(0,0,1)),12.7,296.63-245).Shape()
tool=upper
for t_ in prisms+[bore]: tool=BRepAlgoAPI_Fuse(tool,t_).Shape()
BRepTools.Write_s(tool,"work/diag_tool.brep"); print("tool vol %.1f solids %d"%(vol(tool),count(tool,TopAbs_SOLID)))
for fz in [0.0,0.001,0.005]:
    t=cut(so,[tool],fz); ok=t is not None and V(t)
    print(fz,"valid",ok,"vol %.1f"%(vol(t) if t is not None else 0),"faces",count(t,TopAbs_FACE) if t is not None else 0,flush=True)
    if ok: BRepTools.Write_s(t,"work/p244_diag.brep"); break
