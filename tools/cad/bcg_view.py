import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
exec(open("probe3.py").read().split("for n in sys.argv[2:]:")[0])
exec(open("render_p111.py").read().split("A=rd(")[0].split("rd=lambda")[0])
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
main={"P214":(0.55,0.75,0.95),"P200":(0.95,0.7,0.4),"P189":(0.6,0.9,0.6),"P185":(0.9,0.5,0.8),"P188":(0.95,0.9,0.4)}
def tri(s):
    BRepMesh_IncrementalMesh(s,0.15,False,0.3); out=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            T=loc.Transformation(); P=[t.Node(i).Transformed(T) for i in range(1,t.NbNodes()+1)]
            for i in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(i).Get(); out.append([(P[k-1].X(),P[k-1].Y(),P[k-1].Z()) for k in (a,b,c)])
        ex.Next()
    return np.array(out)
T=[];C=[];inside=[]
for n,s in P.items():
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    if n in main: tt=tri(s); T.append(tt); C+= [main[n]]*len(tt)
    elif x[2]>40 and x[5]<210 and x[0]>-14 and x[3]<42 and x[1]>-282 and x[4]<-234:
        tt=tri(s); T.append(tt); C+=[(0.55,0.55,0.55)]*len(tt); inside.append(n)
print("other parts in this region:",len(inside),sorted(inside))
T=np.concatenate(T); C=np.array(C)
n_=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n_/=np.linalg.norm(n_,axis=1,keepdims=True)+1e-12
fig,axs=plt.subplots(3,1,figsize=(18,16))
for ax,(tt,(i,j),dep,sg) in zip(axs,[("from +x (right side)",(2,1),0,-1),("from -x (left side)",(2,1),0,1),("from below (-y)",(2,0),1,1)]):
    o=np.argsort(-T[:,:,dep].mean(1)*sg); sh=(0.45+0.55*np.abs(n_[o,dep]))[:,None]
    ax.add_collection(PolyCollection([[(q[i],q[j]) for q in t] for t in T[o]],facecolors=np.clip(C[o]*sh,0,1),edgecolors='none'))
    p=T.reshape(-1,3); ax.set_xlim(p[:,i].min()-2,p[:,i].max()+2); ax.set_ylim(p[:,j].min()-2,p[:,j].max()+2); ax.set_aspect('equal'); ax.set_title(tt+"   (blue P214, orange P200, green P189, pink P185, yellow P188, grey = other parts)")
plt.tight_layout(); plt.savefig("work/bcg.png",dpi=55); print("ok")
