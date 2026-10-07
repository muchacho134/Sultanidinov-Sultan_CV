import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
def tris(shape):
    BRepMesh_IncrementalMesh(shape,0.15,False,0.3); out=[]
    ex=TopExp_Explorer(shape,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            T=loc.Transformation(); P=[t.Node(i).Transformed(T) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
files=sys.argv[1:-3]; out=sys.argv[-3]; zlo,zhi=float(sys.argv[-2]),float(sys.argv[-1])
fig,axs=plt.subplots(len(files),2,figsize=(20,4.2*len(files)),squeeze=False)
for r,fn in enumerate(files):
    s=TopoDS_Shape(); BRepTools.Read_s(s,fn,BRep_Builder()); T=tris(s)
    n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=(np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
    for c,(sg,nm) in enumerate(((1,"+x side"),(-1,"-x side"))):
        vis=T[:,:,0].mean(1)*sg>-100
        order=np.argsort(T[:,:,0].mean(1)*sg)
        # simple light from viewer: shade by |n.x| plus facing
        face=(n[:,0]*sg)
        shade=np.clip(0.35+0.55*np.abs(face)+0.1*(face>0),0,1)
        poly=[[(t[k][2],t[k][1]) for k in range(3)] for t in T[order]]
        axs[r][c].add_collection(PolyCollection(poly,facecolors=[(v,v,v) for v in shade[order]*0.9],edgecolors=[(0.2,0.2,0.2,0.25)]*len(poly),linewidths=0.2))
        axs[r][c].set_xlim(zlo,zhi); axs[r][c].set_ylim(-285,-215); axs[r][c].set_aspect('equal'); axs[r][c].axis('off'); axs[r][c].set_title(f"{fn.split('/')[-1]}  -  {nm}")
plt.tight_layout(); plt.savefig(out,dpi=65); print("ok")
