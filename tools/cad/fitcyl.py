import sys,numpy as np
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.TopoDS import TopoDS_Shape,TopoDS
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepTools import BRepTools_WireExplorer
s=TopoDS_Shape();BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
fb=ShapeAnalysis_FreeBounds(s,0.003,False,False)
from OCP.TopExp import TopExp_Explorer
ex=TopExp_Explorer(fb.GetClosedWires(),__import__('OCP.TopAbs',fromlist=['x']).TopAbs_WIRE)
near=np.array([-0.09,-267.93,276.45]);best=None
while ex.More():
    w=TopoDS.Wire_s(ex.Current());pts=[]
    we=BRepTools_WireExplorer(w);es=[]
    while we.More(): es.append(we.Current());we.Next()
    P=[];
    for e in es:
        c=BRepAdaptor_Curve(e);a,b=c.FirstParameter(),c.LastParameter()
        P.append([[c.Value(a+(b-a)*k/10).X(),c.Value(a+(b-a)*k/10).Y(),c.Value(a+(b-a)*k/10).Z()] for k in range(11)])
    cen=np.mean([p for q in P for p in q],0)
    d=np.linalg.norm(cen-near)
    if best is None or d<best[0]: best=(d,P)
    ex.Next()
P=best[1]
idx=[int(i) for i in sys.argv[2].split(',')]
pts=np.array([p for i in idx for p in P[i]])
y,z=pts[:,1],pts[:,2]
A=np.c_[2*y,2*z,np.ones(len(y))];b=y**2+z**2
sol=np.linalg.lstsq(A,b,rcond=None)[0];yc,zc=sol[:2];R=np.sqrt(sol[2]+yc**2+zc**2)
r=np.sqrt((y-yc)**2+(z-zc)**2)-R
print("centre y %.3f z %.3f R %.3f  resid max %.3f"%(yc,zc,R,abs(r).max()))
for i in idx:
    q=np.array(P[i]);rr=np.sqrt((q[:,1]-yc)**2+(q[:,2]-zc)**2)-R
    print(i,"x %.2f..%.2f"%(q[:,0].min(),q[:,0].max()),"res %.3f"%abs(rr).max())
