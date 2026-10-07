exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Ax1, gp_Vec, gp_Pln, gp_Trsf
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol, BRepPrimAPI_MakeHalfSpace
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Common, BRepAlgoAPI_Section
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopTools import TopTools_HSequenceOfShape
from OCP.GeomAbs import GeomAbs_Circle
import numpy as np
AX=(0.0,-267.9)
def cyl(cx,cy,r,z0,z1): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(cx,cy,z0),gp_Dir(0,0,1)),r,z1-z0).Shape()
def box(x0,y0,z0,x1,y1,z1): return BRepPrimAPI_MakeBox(gp_Pnt(x0,y0,z0),gp_Pnt(x1,y1,z1)).Shape()
def fuse(L):
    a=TopTools_ListOfShape(); a.Append(L[0]); t=TopTools_ListOfShape()
    for s in L[1:]: t.Append(s)
    f=BRepAlgoAPI_Fuse(); f.SetArguments(a); f.SetTools(t); f.SetFuzzyValue(1e-6); f.Build(); return f.Shape()
def cut(A,L):
    a=TopTools_ListOfShape(); a.Append(A); t=TopTools_ListOfShape()
    for s in L: t.Append(s)
    c=BRepAlgoAPI_Cut(); c.SetArguments(a); c.SetTools(t); c.SetFuzzyValue(1e-6); c.Build(); return c.Shape()
def common(A,B): c=BRepAlgoAPI_Common(A,B); c.Build(); return c.Shape()
def chk(nm,s):
    so=TopExp_Explorer(s,TopAbs_SOLID).Current() if count(s,TopAbs_SOLID) else s
    print("%-10s solids %d valid %s vol %.1f"%(nm,count(s,TopAbs_SOLID),BRepCheck_Analyzer(s).IsValid(),vol(s))); return s
# A) P214: R10 body + R12.5 collar
P214=fuse([cyl(*AX,10.0,43.42,76.13),cyl(*AX,12.5,76.13,82.38)]); chk("P214",P214)
# B) gap cylinder
GAP=cyl(*AX,12.5,82.38,106.97); chk("gap",GAP)
# C) carrier: R12.5 body with 1.5 rear edge fillet, right flat x<=11.5
Z0,Z1=106.97,203.06
body=cyl(*AX,12.5,Z0,Z1)
fl=BRepFilletAPI_MakeFillet(body); ex=TopExp_Explorer(body,TopAbs_EDGE)
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e)
    if c.GetType()==GeomAbs_Circle and abs(c.Circle().Location().Z()-Z1)<1e-6: fl.Add(1.5,e)
    ex.Next()
fl.Build(); body=fl.Shape()
body=common(body,box(-20,-290,Z0-1,11.5,-240,Z1+1))
feat=[]
feat.append(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(10.0,-267.9,196.06),gp_Dir(1,0,0)),1.05,5).Shape())          # pin hole in right flat (R1.05, from x=10)
feat.append(cut(box(-14,-271.0,119.07,0,-264.8,135.47),[cyl(*AX,9.5,100,210)]))                              # left window pocket (floor = bore radius)
feat.append(box(-6.3,-290,Z0-1,8.26,-276.6,176.97))                                                         # bottom channel (ceiling y=-276.6)
feat.append(box(5.64,-290,Z0-1,8.26,-275.55,176.97))                                                        # right step up to y=-275.55
feat.append(box(-8.97,-290,Z0-1,-6.3,-276.6,145.40))                                                        # left ledge region (front part)
feat.append(box(8.26,-290,Z0-1,9.19,-276.38,143.88))                                                        # right ledge region (front part)
# rear bottom ramp: x in [-5.3,5.3], from z=193.56 (y=-278.4) rising to y=-275.78 at z=195.26, flat to the rear
poly=BRepBuilderAPI_MakePolygon(); 
for (z,y) in ((193.56,-290),(193.56,-278.4),(195.26,-275.78),(Z1+2,-275.78),(Z1+2,-290)): poly.Add(gp_Pnt(-5.3,y,z))
poly.Close(); feat.append(BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire(),True).Face(),gp_Vec(10.6,0,0)).Shape())
feat.append(box(-5.3,-257.6,151.77,5.3,-240,Z1+2))                                                          # top slot (floor y=-257.6)
carrier=cut(body,feat); chk("carrier",carrier)
# D) gas key (P189): R7.25 tube on the upper axis + tail block (left flat at x=-5.05 mirrored)
GK=fuse([cyl(0.0,-243.9,7.25,121.87,160.11),box(-5.05,-257.11,139.74,5.05,-249.10,181.37)]); chk("gas key",GK)
# E) bar (P185): stadium slab, round end R5 at C, width 10, to t=22.74 along d=(0.866,0.5), z 108.019..118.019
C=np.array([7.681,-254.5]); d=np.array([0.866,0.5]); d/=np.linalg.norm(d); nrm=np.array([d[1],-d[0]])
t1=22.74; zb,zt=108.019,118.019
p1=C+nrm*5; p2=C+nrm*5+d*t1; p3=C-nrm*5+d*t1; p4=C-nrm*5
pl=BRepBuilderAPI_MakePolygon(gp_Pnt(p1[0],p1[1],zb),gp_Pnt(p2[0],p2[1],zb),gp_Pnt(p3[0],p3[1],zb),gp_Pnt(p4[0],p4[1],zb),True)
slab=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(pl.Wire(),True).Face(),gp_Vec(0,0,zt-zb)).Shape()
BAR=fuse([slab,cyl(C[0],C[1],5.0,zb,zt)]); chk("bar",BAR)
# F) knob (P188): revolve the exact upper half of its axial section
K=rd("work/x_P188.brep")
P0=np.array([18.305,-252.812,113.024]); D=np.array([-0.866,-0.5,0.0016]); D/=np.linalg.norm(D)
Up=np.cross(np.cross(D,[0,0,1.0]),D); Up/=np.linalg.norm(Up)        # in-plane direction perpendicular to axis (~ +z)
N=np.cross(D,Up)
sec=BRepAlgoAPI_Section(K,gp_Pln(gp_Pnt(*P0),gp_Dir(*N))); sec.Build()
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCP.BRep import BRep_Tool
edges=TopTools_HSequenceOfShape(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE); kept=0
def sr(p): q=np.array([p.X(),p.Y(),p.Z()])-P0; return q@D, q@Up
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e); u0,u1=c.FirstParameter(),c.LastParameter()
    us=np.linspace(u0,u1,41); rr=[sr(c.Value(u))[1] for u in us]
    if min(rr)>=-1e-6: edges.Append(e); kept+=1
    elif max(rr)>1e-6:     # crosses the axis: keep the part with r>=0
        g=BRep_Tool.Curve_s(e,0.0,0.0) if False else None
        from OCP.BRep import BRep_Tool as BT
        crv,a,b=BT.Curve_s(e,0.0,0.0) if False else (None,None,None)
        # find parameter where r=0 by bisection
        lo,hi=(u0,u1) if rr[0]<0 else (u1,u0)
        for _ in range(60):
            mid=(lo+hi)/2
            if sr(c.Value(mid))[1]<0: lo=mid
            else: hi=mid
        pa=c.Value(hi); pb=c.Value(u1 if rr[-1]>0 else u0)
        edges.Append(BRepBuilderAPI_MakeEdge(pa,pb).Edge()); kept+=1
    ex.Next()
# closing edges: along the axis between the profile's two axis points, and the missing inner end (s=0) from r=6.5 to the axis
pts=[]
ex=TopExp_Explorer(sec.Shape(),TopAbs_VERTEX)
s_vals=[]
ws=TopTools_HSequenceOfShape()
ShapeAnalysis_FreeBounds.ConnectEdgesToWires_s(edges,1e-4,False,ws)
w0=TopoDS.Wire_s(ws.Value(1)); print("knob profile wires:",ws.Length())
# endpoints of the open profile wire
from OCP.ShapeAnalysis import ShapeAnalysis_Wire
from OCP.TopExp import TopExp
v1=TopoDS.Vertex_s(TopExp.FirstVertex_s(TopoDS.Edge_s(TopExp_Explorer(w0,TopAbs_EDGE).Current())))
ends=[]
vm={}
ex=TopExp_Explorer(w0,TopAbs_VERTEX)
cnt={}
while ex.More():
    p=BRep_Tool.Pnt_s(TopoDS.Vertex_s(ex.Current())); k=(round(p.X(),5),round(p.Y(),5),round(p.Z(),5)); cnt[k]=cnt.get(k,0)+1; vm[k]=p; ex.Next()
ends=[vm[k] for k,c in cnt.items() if c==1]
print("profile open ends (s,r):",[tuple(np.round(sr(p),3)) for p in ends])
a,b=sorted(ends,key=lambda p:sr(p)[1])    # a: on axis (r~0), b: inner end at r~6.5
axis_end=gp_Pnt(*(P0+D*0.0)); 
pa_s=sr(a)[0]; pb_s=sr(b)[0]
q_axis_inner=gp_Pnt(*(P0+D*pb_s))          # axis point at the inner end's s
mw=BRepBuilderAPI_MakeWire(w0)
mw.Add(BRepBuilderAPI_MakeEdge(b,q_axis_inner).Edge()); mw.Add(BRepBuilderAPI_MakeEdge(q_axis_inner,a).Edge())
prof=BRepBuilderAPI_MakeFace(mw.Wire(),True).Face()
KNOB=BRepPrimAPI_MakeRevol(prof,gp_Ax1(gp_Pnt(*P0),gp_Dir(*D)),2*np.pi).Shape(); chk("knob",KNOB)
for nm,s in (("P214",P214),("GAP",GAP),("carrier",carrier),("GK",GK),("BAR",BAR),("KNOB",KNOB)): BRepTools.Write_s(s,f"work/bcg_{nm}.brep")
ALL=fuse([carrier,P214,GAP,GK,BAR,KNOB])
u=ShapeUpgrade_UnifySameDomain(ALL,True,True,True); u.Build(); ALL=u.Shape()
print("FINAL: solids",count(ALL,TopAbs_SOLID),"| shells",count(ALL,TopAbs_SHELL),"| faces",count(ALL,TopAbs_FACE))
so=TopExp_Explorer(ALL,TopAbs_SOLID).Current()
print("valid",BRepCheck_Analyzer(so).IsValid(),"| self-intersections",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
BRepTools.Write_s(so,"work/bcg_solid.brep")
