exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
from OCP.BRepOffset import BRepOffset_Skin
from OCP.GeomAbs import GeomAbs_Intersection, GeomAbs_Arc
from OCP.gp import gp_Ax2, gp_Dir
P=rd("work/cur_P223.brep")
parts=[]
for x0,x1 in [(-25,-11.3),(11.3,25)]:
    side=BRepAlgoAPI_Common(P,BRepPrimAPI_MakeBox(gp_Pnt(x0,-283.1,250),gp_Pnt(x1,-245,300)).Shape()).Shape()
    ex=TopExp_Explorer(side,TopAbs_SOLID); n=0
    while ex.More():
        sol=ex.Current(); off=None
        for join in (GeomAbs_Arc,GeomAbs_Intersection):
            try:
                o=BRepOffsetAPI_MakeOffsetShape(); o.PerformByJoin(sol,0.1,1e-4,BRepOffset_Skin,False,False,join,False); o.Build()
                if o.IsDone() and V(o.Shape()) and vol(o.Shape())>vol(sol): off=o.Shape(); break
            except Exception as e: pass
        print("side",x0,"piece vol %.1f -> offset %s"%(vol(sol),"%.1f"%vol(off) if off is not None else "FAILED"))
        parts.append(off if off is not None else sol); ex.Next()
lug=BRepPrimAPI_MakeBox(gp_Pnt(-12.65,-283.1,250),gp_Pnt(12.65,-273.69,283.5)).Shape()
bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,250),gp_Dir(0,0,1)),12.7,296.63-250).Shape()
tool=lug
for t_ in parts+[bore]: tool=BRepAlgoAPI_Fuse(tool,t_).Shape()
print("tool solids",count(tool,TopAbs_SOLID),"vol %.1f"%vol(tool)); BRepTools.Write_s(tool,"work/clean_tool.brep")
so=rd("work/p244_pre223.brep")
for fz in [0.0,0.001,0.005,0.02]:
    t=cut(so,[tool],fz)
    if t is not None and not V(t): sf=ShapeFix_Shape(t); sf.Perform(); t=sf.Shape()
    ok=t is not None and V(t); print(fz,"valid",ok,"removed %.1f"%(vol(so)-vol(t) if t is not None else -1),flush=True)
    if ok: BRepTools.Write_s(t,"work/p244_e1.brep"); break
