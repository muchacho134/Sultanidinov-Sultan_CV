import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import *
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
v=lambda p:np.array([p.X(),p.Y(),p.Z()])
B=rd("work/x_P185.brep"); K=rd("work/x_P188.brep")
ex=TopExp_Explorer(B,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if a.GetType()==GeomAbs_Plane: pl=a.Plane(); print("P185 plane n",np.round(v(pl.Axis().Direction()),4),"pt",np.round(v(pl.Location()),3))
    if a.GetType()==GeomAbs_Cylinder: c=a.Cylinder(); print("P185 cyl R",c.Radius(),"loc",np.round(v(c.Location()),3),"dir",np.round(v(c.Axis().Direction()),3))
    ex.Next()
# knob axis
ex=TopExp_Explorer(K,TopAbs_FACE); axes=[]
while ex.More():
    a=BRepAdaptor_Surface(TopoDS.Face_s(ex.Current()))
    if a.GetType() in (GeomAbs_Cylinder,) and a.Cylinder().Radius()>5: c=a.Cylinder(); axes.append((v(c.Location()),v(c.Axis().Direction())))
    if a.GetType()==GeomAbs_Torus: t=a.Torus(); print("P188 torus R %.3f r %.3f centre"%(t.MajorRadius(),t.MinorRadius()),np.round(v(t.Location()),3))
    if a.GetType()==GeomAbs_Cone: c=a.Cone(); print("P188 cone semi %.2f refR %.3f loc"%(np.degrees(c.SemiAngle()),c.RefRadius()),np.round(v(c.Location()),3))
    ex.Next()
P0,D=axes[0]; D=D/np.linalg.norm(D); print("knob axis point",np.round(P0,3),"dir",np.round(D,4))
# section of knob by plane containing axis and the z direction -> profile (s along axis, r)
n=np.cross(D,[0,0,1.0]); n/=np.linalg.norm(n)
sec=BRepAlgoAPI_Section(K,gp_Pln(gp_Pnt(*P0),gp_Dir(*n))); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE)
fig,ax=plt.subplots(figsize=(10,8))
while ex.More():
    c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.01)
    Q=np.array([v(d.Value(k)) for k in range(1,d.NbPoints()+1)]); s=(Q-P0)@D; r=(Q-P0)@np.array([0,0,1.0])
    ax.plot(s,r,'k-',lw=1.2); ex.Next()
ax.axhline(0,c='r',lw=.5); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title("P188 knob: section through its axis (s along axis, r up)")
plt.tight_layout(); plt.savefig("work/knob_profile.png",dpi=70); print("ok")
