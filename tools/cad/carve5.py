exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SOLID
from OCP.gp import gp_Pnt
s=rd("work/p244_final.brep"); P=rd("work/cur_P223.brep")
box=BRepPrimAPI_MakeBox(gp_Pnt(-25,-275,280),gp_Pnt(25,-250,300)).Shape()
tl=BRepAlgoAPI_Common(P,box).Shape()
ex=TopExp_Explorer(tl,TopAbs_SOLID); T=TopTools_ListOfShape()
while ex.More(): T.Append(ex.Current()); ex.Next()
for fz in [0.0,0.001,0.005,0.02]:
    op=BRepAlgoAPI_Cut(); A=TopTools_ListOfShape(); A.Append(s); op.SetArguments(A); op.SetTools(T); op.SetFuzzyValue(fz); op.SetNonDestructive(True); op.Build()
    r=op.Shape(); print(fz,"err",not op.IsDone(),"solids",count(r,TopAbs_SOLID),"vol %.1f"%vol(r),"valid",BRepCheck_Analyzer(r).IsValid())
    if count(r,TopAbs_SOLID)==1 and BRepCheck_Analyzer(r).IsValid(): BRepTools.Write_s(r,"work/p244_final2.brep"); break
