import sys,json,numpy as np
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
s=rd(sys.argv[1]); c=json.loads(sys.argv[2]); idx=json.loads(sys.argv[3]); P=np.array(json.loads(sys.argv[4]))
n=np.cross(P[1]-P[0],P[2]-P[0]); n/=np.linalg.norm(n)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); best=None
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get(); cc=[(x[i]+x[i+3])/2 for i in range(3)]
    d=sum((cc[i]-c[i])**2 for i in range(3))
    if best is None or d<best[0]: best=(d,w)
    ex.Next()
we=BRepTools_WireExplorer(best[1]); E=[]
while we.More(): E.append(we.Current()); we.Next()
for i in idx:
    cv=BRepAdaptor_Curve(E[i]); a,b=cv.FirstParameter(),cv.LastParameter()
    q=np.array([[cv.Value(a+(b-a)*k/20).X(),cv.Value(a+(b-a)*k/20).Y(),cv.Value(a+(b-a)*k/20).Z()] for k in range(21)])
    dd=(q-P[0])@n; print(i,"type",int(cv.GetType()),"dev %.3f..%.3f"%(dd.min(),dd.max()))
