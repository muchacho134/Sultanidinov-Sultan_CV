import sys
exec(open("p110_sec.py").read().split("A=rd(")[0])
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle
S=rd(sys.argv[1])
for xs in sys.argv[2:]:
    x=float(xs); sec=BRepAlgoAPI_Section(S,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0))); sec.Build()
    ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE); L=[]
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter())
        t=c.GetType(); s=""
        if t==GeomAbs_Circle: ci=c.Circle(); s=f"ARC R{ci.Radius():.3f} c({ci.Location().Z():.2f},{ci.Location().Y():.2f})"
        elif t==GeomAbs_Line: s="LINE"
        else: s=f"T{t}"
        L.append((round(a.Z(),2),round(a.Y(),2),round(b.Z(),2),round(b.Y(),2),s)); ex.Next()
    print("=== x",x,len(L))
    for l in sorted(L): print(f"  ({l[0]:7.2f},{l[1]:8.2f}) -> ({l[2]:7.2f},{l[3]:8.2f}) {l[4]}")
