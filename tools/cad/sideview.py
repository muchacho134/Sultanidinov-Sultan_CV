import sys, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
def tris(shape):
    BRepMesh_IncrementalMesh(shape,0.4,False,0.4); out=[]
    ex=TopExp_Explorer(shape,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            T=loc.Transformation(); P=[t.Node(i).Transformed(T) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
zlo,zhi=float(sys.argv[2]),float(sys.argv[3])
allT=[]
for k,(s,comp,ref) in parts.items():
    s=st.GetShape_s(comp); b=bb(s)
    if b[5]<zlo or b[2]>zhi or b[1]>-190 or b[4]<-350: continue
    if (b[3]-b[0])>200: continue
    try: T=tris(s)
    except Exception: continue
    if len(T): allT.append(T)
T=np.concatenate(allT); print("triangles",len(T))
fig,axs=plt.subplots(2,1,figsize=(20,9))
for ax,(side,sgn) in zip(axs,(("viewed from +x side",1),("viewed from -x side",-1))):
    n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/= (np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
    depth=T[:,:,0].mean(1)*sgn; order=np.argsort(depth)       # far first
    shade=np.clip(0.55+0.45*np.abs(n[:,0]),0,1)
    poly=[[(t[k][2],t[k][1]) for k in range(3)] for t in T[order]]
    pc=PolyCollection(poly,facecolors=[(s_,s_,s_*1.02 if s_*1.02<1 else 1) for s_ in shade[order]*0.85],edgecolors='none')
    ax.add_collection(pc); ax.set_xlim(zlo,zhi); ax.set_ylim(-300,-195); ax.set_aspect('equal'); ax.set_title(side); ax.axis('off')
plt.tight_layout(); plt.savefig("work/sideview.png",dpi=75); print("ok")
