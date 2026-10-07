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
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
rd=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
A=rd("work/x_P110.brep"); B=rd("work/x_P213.brep")
fig,axs=plt.subplots(1,2,figsize=(20,8),gridspec_kw={'width_ratios':[2.2,1]})
def draw(ax,s,pln,proj,c,lab):
    sec=BRepAlgoAPI_Section(s,pln); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE); first=True
    while ex.More():
        cc=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cc,0.02)
        P=np.array([proj((d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z())) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'-',c=c,lw=1.2,label=lab if first else None); first=False; ex.Next()
def free(ax,s,proj):
    fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_EDGE); first=True
    while ex.More():
        cc=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cc,0.02)
        P=np.array([proj((d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z())) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'r-',lw=2.5,label="open edges" if first else None); first=False; ex.Next()
pz=lambda p:(p[2],p[1])
draw(axs[0],A,gp_Pln(gp_Pnt(0.005,0,0),gp_Dir(1,0,0)),pz,'k',"P110"); draw(axs[0],B,gp_Pln(gp_Pnt(0.005,0,0),gp_Dir(1,0,0)),pz,'tab:blue',"P213"); free(axs[0],A,pz)
axs[0].set_xlim(-350,-195); axs[0].set_aspect('equal'); axs[0].legend(); axs[0].set_title("section x=0 (side view: z horizontal, y vertical)"); axs[0].grid(alpha=.3)
px=lambda p:(p[0],p[1])
draw(axs[1],A,gp_Pln(gp_Pnt(0,0,-224.0),gp_Dir(0,0,1)),px,'k',"P110 @z=-224"); free(axs[1],A,px)
axs[1].set_aspect('equal'); axs[1].legend(); axs[1].set_title("section z=-224 (looking along barrel)"); axs[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig("work/p110_sec.png",dpi=65); print("ok")
