import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
O=np.array([4.74,-241.16,-237.85]); A=np.array([0.866,0.5,0.0]); A/=np.linalg.norm(A); N=np.array([0.5,-0.866,0.0]); N/=np.linalg.norm(N)
fig,axs=plt.subplots(1,2,figsize=(18,7))
# left: section through screw axis (plane contains screw axis and z); right: section plane z=-237.85 (perp to barrel axis, through screw axis)
for ax,(pln,proj,tt) in zip(axs,[(gp_Pln(gp_Pnt(*O),gp_Dir(*N)),lambda p:((p-O)@A,p[2]),"section through screw axis (horizontal = along screw, vertical = z)"),
                                  (gp_Pln(gp_Pnt(0,0,-237.85),gp_Dir(0,0,1)),lambda p:(p[0],p[1]),"section z=-237.85 (x,y)")]):
    for nm,c in (("P111",'k'),("solid_127",'tab:blue'),("solid_131",'tab:orange')):
        s=rd(f"work/x_{nm}.brep"); sec=BRepAlgoAPI_Section(s,pln); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE); first=True
        while ex.More():
            cc=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cc,0.01)
            P=np.array([proj(np.array([d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()])) for k in range(1,d.NbPoints()+1)])
            ax.plot(P[:,0],P[:,1],'-',c=c,lw=1.3,label=nm if first else None); first=False; ex.Next()
    ax.set_aspect('equal'); ax.legend(); ax.set_title(tt); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig("work/p111_sec.png",dpi=70); print("ok")
