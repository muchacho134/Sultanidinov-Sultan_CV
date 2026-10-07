exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SOLID
def cut(a_,tools,fz=0.005):
    op=BRepAlgoAPI_Cut(); A=TopTools_ListOfShape(); A.Append(a_); T=TopTools_ListOfShape()
    for t in tools: T.Append(t)
    op.SetArguments(A); op.SetTools(T); op.SetFuzzyValue(fz); op.Build(); r=op.Shape()
    sols=[]; ex=TopExp_Explorer(r,TopAbs_SOLID)
    while ex.More(): sols.append(ex.Current()); ex.Next()
    sols.sort(key=vol,reverse=True); print("  solids",[round(vol(x),2) for x in sols[:5]])
    return sols[0]
s=rd("work/p244_solid9.brep"); print("start %.1f"%vol(s))
s=cut(s,[rd("work/slot_tool.brep")]); print("slot: valid",BRepCheck_Analyzer(s).IsValid(),"%.1f"%vol(s))
s=cut(s,[rd(f"work/cur_{n}.brep") for n in ["P256","P596","P259","P223"]]); print("carve: valid",BRepCheck_Analyzer(s).IsValid(),"%.1f"%vol(s))
BRepTools.Write_s(s,"work/p244_final.brep")
