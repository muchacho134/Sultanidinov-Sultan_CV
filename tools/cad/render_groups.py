import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
exec(open("puzzle.py").read().split("print(\"parts\",len(parts))")[0])
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
def tris(shape):
    BRepMesh_IncrementalMesh(shape,0.3,False,0.4); out=[]
    ex=TopExp_Explorer(shape,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            T=loc.Transformation(); P=[t.Node(i).Transformed(T) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
groups=[g.split(",") for g in sys.argv[2].split(";")]; titles=sys.argv[3].split(";")
cols=plt.cm.tab20.colors
fig=plt.figure(figsize=(16,7*((len(groups)+1)//2)))
for gi,(G,tt) in enumerate(zip(groups,titles)):
    ax=fig.add_subplot((len(groups)+1)//2,2,gi+1,projection='3d')
    lo=np.array([1e9]*3); hi=-lo
    for ci,k in enumerate(G):
        T=tris(parts[k])
        if not len(T): continue
        M=T[...,[2,0,1]]
        ax.add_collection3d(Poly3DCollection(M,facecolor=cols[ci%20],edgecolor=(0,0,0,0.05),linewidths=0.1,alpha=0.9,label=k))
        lo=np.minimum(lo,M.reshape(-1,3).min(0)); hi=np.maximum(hi,M.reshape(-1,3).max(0))
        ax.text(*M.reshape(-1,3).mean(0),k,fontsize=8)
    c=(lo+hi)/2; r=(hi-lo).max()/2
    ax.set_xlim(c[0]-r,c[0]+r); ax.set_ylim(c[1]-r,c[1]+r); ax.set_zlim(c[2]-r,c[2]+r)
    ax.view_init(elev=25,azim=-60); ax.set_title(tt); ax.set_axis_off()
plt.tight_layout(); plt.savefig(sys.argv[4],dpi=70); print("ok")
