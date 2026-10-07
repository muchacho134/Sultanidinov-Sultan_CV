exec(open("bcg_build.py").read().split("# A) P214")[0])
from OCP.GC import GC_MakeArcOfCircle
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffset
from OCP.GeomAbs import GeomAbs_Arc, GeomAbs_Intersection
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
import math
def P(x,zy): return gp_Pnt(x,zy[1],zy[0])
def wire(segs,x=0.0):
    """segs: list of points (z,y) and arcs ('A',(cz,cy)) between them; closed if first==last"""
    w=BRepBuilderAPI_MakeWire(); pts=[s for s in segs]; i=0; cur=pts[0]; i=1
    while i<len(pts):
        s=pts[i]
        if isinstance(s,tuple) and s[0]=='A':
            c=s[1]; nxt=pts[i+1]; r=math.dist(c,cur)
            m=((cur[0]+nxt[0])/2-c[0],(cur[1]+nxt[1])/2-c[1]); L=math.hypot(*m); mid=(c[0]+r*m[0]/L,c[1]+r*m[1]/L)
            e=BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(x,cur),P(x,mid),P(x,nxt)).Value()).Edge(); cur=nxt; i+=2
        else:
            if math.dist(cur,s)<1e-6: i+=1; continue
            e=BRepBuilderAPI_MakeEdge(P(x,cur),P(x,s)).Edge(); cur=s; i+=1
        w.Add(e)
    return w.Wire()
def face(segs,x=0.0): return BRepBuilderAPI_MakeFace(wire(segs,x),True).Face()
def prism(f,x0,x1):
    t=gp_Trsf(); t.SetTranslation(gp_Vec(x0,0,0)); from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    f2=BRepBuilderAPI_Transform(f,t,True).Shape(); return BRepPrimAPI_MakePrism(f2,gp_Vec(x1-x0,0,0)).Shape()
def off2d(f,d):
    m=BRepOffsetAPI_MakeOffset(f,GeomAbs_Arc); m.Perform(d); w=m.Shape()
    ex=TopExp_Explorer(w,TopAbs_WIRE); return BRepBuilderAPI_MakeFace(TopoDS.Wire_s(ex.Current()),True).Face()
def area(f):
    from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
    g=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,g); return g.Mass()
def unify(s): u=ShapeUpgrade_UnifySameDomain(s,True,True,True); u.Build(); return u.Shape()
A=lambda cz,cy:('A',(cz,cy))
# ---- box profile (common tail from the top-bump onwards)
TAIL=[(214.27,-286.90),A(214.27,-285.90),(215.27,-285.89),(215.22,-278.62),A(218.22,-278.60),(218.22,-275.60),(235.20,-275.60),
      A(246.31,-301.30),(264.81,-322.32),(264.81,-329.22),(264.38,-329.45),A(265.81,-332.09),(262.81,-332.09),(262.81,-336.30),
      A(259.81,-336.30),(259.81,-339.30),(232.43,-339.30),A(232.43,-342.30),(230.02,-340.52),A(217.38,-331.20),(217.38,-346.90)]
PM=[(188.93,-345.77),(188.93,-291.40),A(191.93,-291.40),(191.93,-288.40),(210.49,-288.40),A(210.49,-286.40),(212.43,-286.90)]+TAIL+[(194.78,-346.90),A(194.78,-331.20),(188.93,-345.77)]
PL=[(213.78,-346.90),(213.78,-286.90)]+TAIL+[(213.78,-346.90)]
fM=face(PM); fL=face(PL)
fMi=off2d(fM,-1.5); fLi=off2d(fL,-1.5)
print("areas",area(fM),area(fMi),area(fL),area(fLi))
outer=fuse([prism(fL,-68.2,-54.2),prism(fM,-54.2,-15.7)]); outer=unify(outer)
# fillets: R3 convex edge x=-68.2/z=213.78 ; R1.5 concave edge x=-54.2/z=213.78 (both along y)
def edges_along_y(s,x,z):
    out=[]; ex=TopExp_Explorer(s,TopAbs_EDGE)
    while ex.More():
        e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e); a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter())
        if abs(a.X()-x)<1e-3 and abs(b.X()-x)<1e-3 and abs(a.Z()-z)<1e-3 and abs(b.Z()-z)<1e-3 and abs(a.Y()-b.Y())>1: out.append(e)
        ex.Next()
    return out
fl=BRepFilletAPI_MakeFillet(outer)
for e in edges_along_y(outer,-68.2,213.78): fl.Add(3.0,e)
for e in edges_along_y(outer,-54.2,213.78): fl.Add(1.5,e)
fl.Build(); print("fillet",fl.IsDone()); outer=fl.Shape() if fl.IsDone() else outer
cav=fuse([prism(fLi,-66.7,-52.7),prism(fMi,-52.7,-17.2)])
boxs=chk("box",cut(outer,[cav]))
BRepTools.Write_s(boxs,"work/hous_box.brep")
