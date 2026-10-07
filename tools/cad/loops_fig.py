import sys
exec(open("render_isof.py").read().split("files=sys.argv[1]")[0])
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
S=rd(sys.argv[1]); out=sys.argv[2]; T=tris(S)
fb=ShapeAnalysis_FreeBounds(S,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); L=[]
while ex.More():
    pts=[]; e2=TopExp_Explorer(ex.Current(),TopAbs_EDGE)
    while e2.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(e2.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
        pts+= [[d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()] for k in range(1,d.NbPoints()+1)]+[[np.nan]*3]; e2.Next()
    L.append(np.array(pts)); ex.Next()
views=[("side -x",2,1),("top",2,0),("front",0,1)]
fig,axs=plt.subplots(3,1,figsize=(26,24))
for ax,(t,i,j) in zip(axs,views):
    ax.add_collection(PolyCollection([[(q[i],q[j]) for q in tt] for tt in T],facecolors=(.85,.85,.87),edgecolors='none'))
    for k,P in enumerate(L):
        ax.plot(P[:,i],P[:,j],'-',lw=1.6,color=plt.cm.tab20(k%20)); m=np.nanmean(P,0); ax.text(m[i],m[j],str(k),fontsize=11,color='k',weight='bold')
    q=T.reshape(-1,3); ax.set_xlim(q[:,i].min()-2,q[:,i].max()+2); ax.set_ylim(q[:,j].min()-2,q[:,j].max()+2); ax.set_aspect('equal'); ax.set_title(t,fontsize=18)
plt.tight_layout(); plt.savefig(out,dpi=45); print(len(L))
