import sys
exec(open("p110_sec.py").read().split("A=rd(")[0])
from OCP.GeomAbs import GeomAbs_Line,GeomAbs_Circle
S=rd(sys.argv[1]); z=float(sys.argv[2]); ymin=float(sys.argv[3]) if len(sys.argv)>3 else -1e9
sec=BRepAlgoAPI_Section(S,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1))); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE); L=[]
while ex.More():
    c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter()); t=c.GetType()
    ts="LINE" if t==GeomAbs_Line else (f"ARC R{c.Circle().Radius():.2f} c({c.Circle().Location().X():.2f},{c.Circle().Location().Y():.2f})" if t==GeomAbs_Circle else "T"+str(t).split('.')[-1][10:])
    if min(a.Y(),b.Y())>ymin: L.append((round(a.X(),2),round(a.Y(),2),round(b.X(),2),round(b.Y(),2),ts))
    ex.Next()
for l in sorted(L): print(f"  ({l[0]:7.2f},{l[1]:8.2f}) -> ({l[2]:7.2f},{l[3]:8.2f}) {l[4]}")
