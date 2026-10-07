import sys, numpy as np
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.BRepTools import BRepTools
from OCP.BRepBuilderAPI import *
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import *
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax3, gp_Ax2, gp_Cone, gp_Pln, gp_Circ
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound
k114=[k for k in parts if k.endswith("114")][0]; k131="solid_131"
s114=parts[k114][0]; s131=parts[k131][0]
def faces(s):
    L=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def tr_face(f):
    t,r=tr(fverts(f)); return t.min(),t.max(),r.max()
def free_wires(s,tol=1e-4):
    from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
    fb=ShapeAnalysis_FreeBounds(s,tol); L=[]
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More(): L.append(TopoDS.Wire_s(ex.Current())); ex.Next()
    return L
def describe(wr):
    out=[]
    for w in wr:
        P=[]; ex=TopExp_Explorer(w,TopAbs_EDGE); ne=0
        while ex.More():
            e=TopoDS.Edge_s(ex.Current()); ne+=1; c=BRepAdaptor_Curve(e)
            for u in np.linspace(c.FirstParameter(),c.LastParameter(),5): p=c.Value(u); P.append([p.X(),p.Y(),p.Z()])
            ex.Next()
        t,r=tr(np.array(P)); out.append((ne,round(t.min(),3),round(t.max(),3),round(r.min(),3),round(r.max(),3)))
    return out
# ---- 131: drop the cap that faces 114 (planar face at t=2.8)
F131=faces(s131); cap=[f for f in F131 if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(tr_face(f)[0]-2.8)<0.02 and abs(tr_face(f)[1]-2.8)<0.02]
print("131 cap candidates:",len(cap)); 
rest131=[f for f in F131 if not any(f.IsSame(c) for c in cap)]
sw=BRepBuilderAPI_Sewing(1e-4)
for f in rest131: sw.Add(f)
sw.Perform(); sh131=sw.SewedShape(); print("131 without cap: free loops",describe(free_wires(sh131)))
# ---- 114: keep shank/annulus, drop head facets + jagged cones
F114=faces(s114); keep=[]; dropped=0; cones=[]
for f in F114:
    t0,t1,r1=tr_face(f); typ=BRepAdaptor_Surface(f).GetType()
    if typ==GeomAbs_Plane and t0>=6.4: dropped+=1; continue
    if typ==GeomAbs_Cone: cones.append(f); continue
    keep.append(f)
print("114: kept",len(keep),"dropped head facets",dropped,"dropped jagged cones",len(cones))
cyls=[f for f in keep if BRepAdaptor_Surface(f).GetType()==GeomAbs_Cylinder]
T_CAP=6.49
c0=BRepAdaptor_Surface(cyls[0]).Cylinder(); L0=np.array([c0.Location().X(),c0.Location().Y(),c0.Location().Z()]); D0=np.array([c0.Axis().Direction().X(),c0.Axis().Direction().Y(),c0.Axis().Direction().Z()])
if D0@A<0: D0=-D0
print('exact axis dir',D0.round(6),'(approx',A.round(6),')')
def ax_pt(t):
    p=O+t*A; q=L0+D0*((p-L0)@D0); return gp_Pnt(*q)
new=[]
for cf in cyls:
    a=BRepAdaptor_Surface(cf); cyl=a.Cylinder(); u0,u1=a.FirstUParameter(),a.LastUParameter()
    ax3=cyl.Position(); loc=ax_pt(6.2)
    # move cylinder frame origin to t=6.2 (same axis, same x direction => same u angles)
    ax3b=gp_Ax3(loc,ax3.Direction(),ax3.XDirection())
    if not ax3.Direct(): ax3b=gp_Ax3(loc,ax3.Direction(),ax3.XDirection()); ax3b.YReverse()
    cone=gp_Cone(ax3b,-np.pi/4,2.9)
    v1=(T_CAP-6.2)/np.cos(np.pi/4)
    mf=BRepBuilderAPI_MakeFace(cone,float(u0),float(u1),0.0,float(v1))
    if mf.IsDone(): new.append(mf.Face())
print("new chamfer cone halves:",len(new))
R_cap=2.9-(T_CAP-6.2)
circ=gp_Circ(gp_Ax2(ax_pt(T_CAP),gp_Dir(*D0)),R_cap)
disc=BRepBuilderAPI_MakeFace(gp_Pln(ax_pt(T_CAP),gp_Dir(*D0)),BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circ).Edge()).Wire()).Face()
sw=BRepBuilderAPI_Sewing(1e-3)
for f in keep+new+[disc]: sw.Add(f)
sw.Perform(); sh114=sw.SewedShape()
print("114 fixed: free loops",describe(free_wires(sh114)))
BRepTools.Write_s(sh131,"work/s131_open.brep"); BRepTools.Write_s(sh114,"work/s114_fixed.brep")

from OCP.BRepFill import BRepFill_Generator
w131=free_wires(sh131)[0]
w114=[w for w in free_wires(sh114) if abs(describe([w])[0][1]-3.0)<0.05][0]
print("ring from",describe([w131]),"to",describe([w114]))
def circ_of(w):
    e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current()); return BRepAdaptor_Curve(e).Circle()
c1,c2=circ_of(w131),circ_of(w114)
P1=np.array([c1.Location().X(),c1.Location().Y(),c1.Location().Z()]); P2=np.array([c2.Location().X(),c2.Location().Y(),c2.Location().Z()])
Dn=np.array([c1.Axis().Direction().X(),c1.Axis().Direction().Y(),c1.Axis().Direction().Z()])
if Dn@A<0: Dn=-Dn
dt=(P2-P1)@Dn; dR=c2.Radius()-c1.Radius()
print("ring: R1=%.4f -> R2=%.4f over axial %.4f  (cone half-angle %.1f deg)"%(c1.Radius(),c2.Radius(),dt,np.degrees(np.arctan2(dR,dt))))
xd=c1.XAxis().Direction()
ring_cone=gp_Cone(gp_Ax3(c1.Location(),gp_Dir(*Dn),xd),float(np.arctan2(dR,dt)),float(c1.Radius()))
rf=[BRepBuilderAPI_MakeFace(ring_cone,0.0,2*np.pi,0.0,float(np.hypot(dR,dt))).Face()]
sw=BRepBuilderAPI_Sewing(1e-3)
for f in faces(sh131)+rf: sw.Add(f)
sw.Perform(); new131=sw.SewedShape()
print("131 + ring: free loops",describe(free_wires(new131)))
# total check: 131(new) + 114(new) together
sw=BRepBuilderAPI_Sewing(1e-3)
for f in faces(new131)+faces(sh114): sw.Add(f)
sw.Perform(); both=sw.SewedShape(); L=[]; ex=TopExp_Explorer(both,TopAbs_SHELL)
while ex.More(): L.append(ex.Current()); ex.Next()
print("131+114 combined: shells",len(L),"free loops",[describe(free_wires(s)) for s in L])
BRepTools.Write_s(new131,"work/s131_new.brep"); BRepTools.Write_s(sh114,"work/s114_fixed.brep")
