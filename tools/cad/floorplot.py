exec(open("p110_sec.py").read().split("A=rd(")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepTools import BRepTools_WireExplorer
S=rd("work/p223_ckpt2.brep")
fig,ax=plt.subplots(figsize=(10,30))
# existing faces near the bottom (y<-282.5) as section-like outlines: draw all edges with y<-282.5
ex=TopExp_Explorer(S,TopAbs_EDGE)
while ex.More():
    c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.02)
    P=np.array([(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)])
    if P[:,1].max()<-282.5 and P[:,2].min()>95 and P[:,2].max()<255 and abs(P[:,0]).max()<16:
        ax.plot(P[:,0],P[:,2],'-',color='0.7',lw=1)
    ex.Next()
fb=ShapeAnalysis_FreeBounds(S,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More():
    b=Bnd_Box(); BRepBndLib.Add_s(ex.Current(),b); x=b.Get()
    if x[2]>100 and x[5]<255 and x[1]<-283:
        we=BRepTools_WireExplorer(TopoDS.Wire_s(ex.Current())); i=0
        while we.More():
            c=BRepAdaptor_Curve(we.Current()); d=GCPnts_QuasiUniformDeflection(c,0.02)
            P=np.array([(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)])
            y=P[:,1].mean(); col='red' if y<-283.0 else ('blue' if y<-282.5 else 'green')
            ax.plot(P[:,0],P[:,2],'-',color=col,lw=2.5); m=P.mean(0); ax.text(m[0],m[2],str(i),fontsize=9); i+=1; we.Next()
    ex.Next()
ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title("floor loop: red y=-283.1, blue y=-282.9, green higher; grey=existing bottom edges")
plt.tight_layout(); plt.savefig("work/floorplot.png",dpi=55); print("ok")
