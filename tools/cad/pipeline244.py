import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell, ShapeFix_Shape, ShapeFix_Wireframe
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pnt
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
V=lambda x:BRepCheck_Analyzer(x).IsValid()
def cut(a_,tools,fz):
    op=BRepAlgoAPI_Cut(); A=TopTools_ListOfShape(); A.Append(a_); T=TopTools_ListOfShape()
    for t in tools:
        ex=TopExp_Explorer(t,TopAbs_SOLID)
        while ex.More(): T.Append(ex.Current()); ex.Next()
    op.SetArguments(A); op.SetTools(T); op.SetFuzzyValue(fz); op.Build(); r=op.Shape()
    sols=[]; ex=TopExp_Explorer(r,TopAbs_SOLID)
    while ex.More(): sols.append(ex.Current()); ex.Next()
    sols.sort(key=vol,reverse=True); return sols[0] if sols else None
def tryfix(x):
    if V(x): return x
    sf=ShapeFix_Shape(x); sf.Perform(); return sf.Shape()
s=rd(sys.argv[1]); ex=TopExp_Explorer(s,TopAbs_SHELL); sh=TopoDS.Shell_s(ex.Current())
fs=ShapeFix_Shell(sh); fs.Perform(); sh=fs.Shell()
so=BRepBuilderAPI_MakeSolid(sh).Solid(); f=ShapeFix_Solid(so); f.Perform(); so=tryfix(f.Solid()); print("solid valid",V(so))
so=tryfix(cut(so,[rd("work/slot_tool.brep")],0.005)); print("slot valid",V(so))
for n in ["P259","P596","P256"]:
    t=cut(so,[rd(f"work/cur_{n}.brep")],0.005); t=tryfix(t) if t is not None else None
    print(n,"valid",t is not None and V(t)); 
    if t is not None and V(t): so=t
box=BRepPrimAPI_MakeBox(gp_Pnt(-25,-275,280),gp_Pnt(25,-250,300)).Shape()
tl=BRepAlgoAPI_Common(rd("work/cur_P223.brep"),box).Shape()
full=rd("work/cur_P223.brep"); done=False
for tool_,fz in [(full,0.001),(full,0.005),(full,0.0),(full,0.01),(tl,0.001),(tl,0.005)]:
    t=cut(so,[tool_],fz)
    if t is not None and not V(t):
        sf=ShapeFix_Shape(t); sf.Perform(); t=sf.Shape()
    print("  try",("full" if tool_ is full else "box"),fz,t is not None and V(t))
    if t is not None and V(t): so=t; print("P223 carved fz",fz); break
else: print("P223 carve FAILED")
for prec in [0.005,0.01]:
    wf=ShapeFix_Wireframe(so); wf.SetPrecision(prec); wf.FixSmallEdges(); wf.FixWireGaps(); u=wf.Shape()
    sf=ShapeFix_Shape(u); sf.SetPrecision(prec); sf.SetMaxTolerance(prec*2); sf.Perform(); u=sf.Shape()
    w=STEPControl_Writer(); w.Transfer(u,STEPControl_AsIs); w.Write("work/rt_c.step")
    r=STEPControl_Reader(); r.ReadFile("work/rt_c.step"); r.TransferRoots(); t=r.OneShape()
    print("prec",prec,"valid",V(u),"roundtrip",V(t),"solids",count(u,TopAbs_SOLID))
    if V(u) and V(t) and count(u,TopAbs_SOLID)==1: so=u; break
BRepTools.Write_s(so,sys.argv[2]); print("faces",count(so,TopAbs_FACE),"vol %.1f"%vol(so))
