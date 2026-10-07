import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
fig,axs=plt.subplots(1,3,figsize=(27,8))
for ax,x0 in zip(axs,[0,8,11]):
    for fn,col in [("work/cur_P223.brep","r"),(sys.argv[1],"k")]:
        sec=BRepAlgoAPI_Section(rd(fn),gp_Pln(gp_Pnt(x0,0,0),gp_Dir(1,0,0))).Shape(); ex=TopExp_Explorer(sec,TopAbs_EDGE)
        while ex.More():
            c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.02)
            Q=np.array([[d.Value(k).Y(),d.Value(k).Z()] for k in range(1,d.NbPoints()+1)]); ax.plot(Q[:,1],Q[:,0],col+'-',lw=1.5); ex.Next()
    ax.set_xlim(245,300); ax.set_ylim(-288,-255); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title(f"x={x0} red=P223 black=P244")
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=55)
