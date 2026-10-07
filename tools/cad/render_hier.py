import sys, pickle, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
M=pickle.load(open("work/hier_map.pkl","rb")); groups=sorted(set(M.values())); cmap=plt.cm.tab20.colors
col={g:cmap[i*2%20] if i<10 else cmap[(i*2+1)%20] for i,g in enumerate(groups)}
T=[];C=[]
for k,(s,comp,ref) in parts.items():
    s=st.GetShape_s(comp); BRepMesh_IncrementalMesh(s,0.5,False,0.5)
    ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            tf=loc.Transformation(); P=[t.Node(i).Transformed(tf) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); T.append([(P[q-1].X(),P[q-1].Y(),P[q-1].Z()) for q in (a,b,c)]); C.append(col[M[k]])
        ex.Next()
T=np.array(T); C=np.array(C)
n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=(np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
fig,axs=plt.subplots(2,1,figsize=(22,10))
for ax,sg,tt in ((axs[0],1,"from +x (right side)"),(axs[1],-1,"from -x (left side)")):
    o=np.argsort(T[:,:,0].mean(1)*sg); sh=(0.55+0.45*np.abs(n[o,0]))[:,None]
    ax.add_collection(PolyCollection([[(q[2],q[1]) for q in t] for t in T[o]],facecolors=np.clip(C[o]*sh,0,1),edgecolors='none'))
    ax.set_xlim(-410,330); ax.set_ylim(-360,-195); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(tt)
axs[0].legend(handles=[Patch(color=col[g],label=g) for g in groups],loc='lower left',ncol=4,fontsize=9)
plt.tight_layout(); plt.savefig("work/hier.png",dpi=60); print("ok")
