import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch
src=open("p110_sec.py").read()
exec(src.split("A=rd(")[0])
exec("def draw"+src.split("def draw")[1].split("pz=lambda")[0])
M=rd("work/x_P256.brep"); B=rd("work/bcg_solid.brep")
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
def edges_of(shape,proj,ax,c,lw=1.3,ls='-'):
    ex=TopExp_Explorer(shape,TopAbs_EDGE)
    while ex.More():
        cc=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(cc,0.05)
        P=np.array([proj((d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z())) for k in range(1,d.NbPoints()+1)]); ax.plot(P[:,0],P[:,1],ls,c=c,lw=lw); ex.Next()
fb=ShapeAnalysis_FreeBounds(M,1e-4); FREE=fb.GetClosedWires()
fig=plt.figure(figsize=(22,13))
# ---------- side view (from +x): z horizontal, y vertical
ax=fig.add_subplot(1,2,1)
pz=lambda p:(p[2],p[1])
draw(ax,B,gp_Pln(gp_Pnt(0,-267.9,0),gp_Dir(1,0,0)),pz,'0.55',"bolt carrier (P214, section x=0)")
edges_of(M,pz,ax,'0.25',1.0)
edges_of(FREE,pz,ax,'red',2.5)
# proposed top cap: follows the existing top edge, 1.5 mm thick feed-lip band
ax.add_patch(Rectangle((104.33,-282.84),61.0,1.94,fc=(0.2,0.45,0.95,0.45),ec='tab:blue',lw=1.5))
ax.add_patch(Rectangle((165.33,-285.84),4.0,1.5,fc=(0.2,0.45,0.95,0.45),ec='tab:blue',lw=1.5))
# mag-catch window -> pocket (left side), spine U-slot kept
ax.add_patch(Rectangle((143.83,-318.74),10.0,16.6,fc=(0.2,0.45,0.95,0.15),ec='tab:blue',lw=1.5,ls='--'))
ax.annotate("1  TOP CAP (new)\nclose the open top along the\nexisting top edge (y -280.9 … -282.3);\nfeed-lip band 1.5 mm",xy=(130,-281.8),xytext=(108,-300),fontsize=11,color='tab:blue',arrowprops=dict(arrowstyle='->',color='tab:blue'))
ax.annotate("2  MAG-CATCH WINDOW\n(left side, U-shape R4.75)\n→ keep as 2 mm pocket",xy=(149,-312),xytext=(112,-335),fontsize=11,color='tab:blue',arrowprops=dict(arrowstyle='->',color='tab:blue'))
ax.annotate("3  SPINE U-SLOT (R4)\n→ keep, add slot floor\nand walls",xy=(167.3,-290),xytext=(150,-262),fontsize=11,color='tab:blue',arrowprops=dict(arrowstyle='->',color='tab:blue'))
ax.annotate("body walls, corners R1.5,\nfloor plate: already OK",xy=(135,-355),xytext=(108,-352),fontsize=11,color='0.3')
ax.annotate("carrier underside y -280.4\n(0.5 mm above mag top)",xy=(190,-280.4),xytext=(172,-300),fontsize=10,color='0.4',arrowprops=dict(arrowstyle='->',color='0.5'))
ax.set_xlim(100,205); ax.set_ylim(-363,-250); ax.set_aspect('equal'); ax.grid(alpha=.25)
ax.set_title("Magazine P256 – side view (from +x).  grey = existing, RED = open edges, BLUE = proposed",fontsize=12)
# ---------- top view (from +y) and front view
ax2=fig.add_subplot(2,2,2)
px=lambda p:(p[2],p[0])
edges_of(M,px,ax2,'0.25',1.0); edges_of(FREE,px,ax2,'red',2.5)
ax2.add_patch(Rectangle((104.33,-11.25),61.0,22.5,fc=(0.2,0.45,0.95,0.30),ec='tab:blue',lw=1.5))
ax2.add_patch(Rectangle((165.33,-5.65),4.0,11.3,fc=(0.2,0.45,0.95,0.30),ec='tab:blue',lw=1.5))
ax2.text(120,0,"1  top cap (flat, follows outline,\n    keeps R1.5 corners)",fontsize=11,color='tab:blue',va='center')
ax2.set_aspect('equal'); ax2.grid(alpha=.25); ax2.set_title("Top view (looking down into the open top)",fontsize=12); ax2.set_xlim(100,175); ax2.set_ylim(-16,16)
ax3=fig.add_subplot(2,2,4)
pxy=lambda p:(p[0],p[1])
edges_of(M,pxy,ax3,'0.25',1.0); edges_of(FREE,pxy,ax3,'red',2.5)
ax3.text(14,-300,"2  mag-catch pocket\n    on this side (x = -11.25)",fontsize=11,color='tab:blue')
ax3.annotate("",xy=(-11.25,-310),xytext=(13,-303),arrowprops=dict(arrowstyle='->',color='tab:blue'))
ax3.set_aspect('equal'); ax3.grid(alpha=.25); ax3.set_title("Front view (from -z)",fontsize=12); ax3.set_xlim(-16,40); ax3.set_ylim(-363,-275)
plt.tight_layout(); plt.savefig("work/mag_plan.png",dpi=70); print("ok")
