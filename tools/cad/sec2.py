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
s=TopoDS_Shape(); BRepTools.Read_s(s,"work/shell_a.brep",BRep_Builder())
fig,axs=plt.subplots(2,3,figsize=(18,9))
for ax,z in zip(axs.flat,(-152,-122,-91,-60,-29,-2)):
    sec=BRepAlgoAPI_Section(s,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1))); sec.Build(); ex=TopExp_Explorer(sec.Shape(),TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
        P=np.array([(d.Value(k).X(),d.Value(k).Y()) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],'k-',lw=1); ex.Next()
    ax.axvline(0,c='r',lw=0.4); ax.set_aspect('equal'); ax.set_xlim(-16,16); ax.set_ylim(-250,-220); ax.set_title(f"z={z}   (left = -x, right = +x)")
plt.tight_layout(); plt.savefig("work/sec2.png",dpi=60); print("ok")
