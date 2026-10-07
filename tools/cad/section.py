import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/shell_a.brep",BRep_Builder())
fig,axs=plt.subplots(2,3,figsize=(18,10))
fb=ShapeAnalysis_FreeBounds(s,1e-3)
free=[]
for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
    ex=TopExp_Explorer(comp,TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.2)
        free+= [(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; ex.Next()
free=np.array(free)
for ax,z in zip(axs.flat,(-190,-120,-60,0,64,150)):
    sec=BRepAlgoAPI_Section(s,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1))); sec.Build()
    ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.1)
        P=np.array([(d.Value(k).X(),d.Value(k).Y()) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'k-',lw=0.8); ex.Next()
    m=np.abs(free[:,2]-z)<1.5; ax.plot(free[m,0],free[m,1],'r.',ms=4)
    ax.set_aspect('equal'); ax.set_title(f"z={z}"); ax.set_xlim(-32,32); ax.set_ylim(-282,-216)
plt.tight_layout(); plt.savefig("work/sections.png",dpi=60); print("ok")
