import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Shape, ShapeFix_Wireframe
from OCP.TopAbs import TopAbs_SOLID
def rt(s,fn):
    w=STEPControl_Writer(); w.Transfer(s,STEPControl_AsIs); w.Write(fn)
    r=STEPControl_Reader(); r.ReadFile(fn); r.TransferRoots(); return r.OneShape()
s=rd(sys.argv[1]); print("in valid",BRepCheck_Analyzer(s).IsValid())
t=rt(s,"work/rt_a.step"); print("raw roundtrip valid",BRepCheck_Analyzer(t).IsValid())
for prec in [0.005,0.01]:
    wf=ShapeFix_Wireframe(s); wf.SetPrecision(prec); wf.FixSmallEdges(); wf.FixWireGaps(); u=wf.Shape()
    sf=ShapeFix_Shape(u); sf.SetPrecision(prec); sf.SetMaxTolerance(prec*2); sf.Perform(); u=sf.Shape()
    print(prec,"fixed valid",BRepCheck_Analyzer(u).IsValid(),"solids",count(u,TopAbs_SOLID),"faces",count(u,TopAbs_FACE))
    t=rt(u,"work/rt_b.step"); ok=BRepCheck_Analyzer(t).IsValid(); print("  roundtrip valid",ok)
    if ok and BRepCheck_Analyzer(u).IsValid(): BRepTools.Write_s(u,sys.argv[2]); break
