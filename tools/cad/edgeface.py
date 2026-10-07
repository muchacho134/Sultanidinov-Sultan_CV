import sys,json
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
s=rd(sys.argv[1]); c=json.loads(sys.argv[2])
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); best=None
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=b.Get(); cc=[(x[i]+x[i+3])/2 for i in range(3)]
    d=sum((cc[i]-c[i])**2 for i in range(3))
    if best is None or d<best[0]: best=(d,w)
    ex.Next()
we=BRepTools_WireExplorer(best[1]); i=0
names={0:"PLN",1:"CYL",2:"CON",3:"SPH",4:"TOR",5:"BEZ",6:"BSP",7:"REV",8:"EXT",9:"OFF",10:"OTH"}
while we.More():
    e=we.Current(); 
    # find same edge in shell
    fs=[]
    for k in range(1,m.Extent()+1):
        if m.FindKey(k).IsSame(e): fs=list(m.FindFromIndex(k)); break
    out=[]
    for f in fs:
        a=BRepAdaptor_Surface(TopoDS.Face_s(f)); t=int(a.GetType()); bb=Bnd_Box(); BRepBndLib.Add_s(f,bb); X=bb.Get()
        info=names.get(t,str(t))
        if t==0: n=a.Plane().Axis().Direction(); p=a.Plane().Location(); info+=" n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
        if t==1: ax=a.Cylinder().Axis(); info+=" R%.2f ax(%.2f,%.2f,%.2f)"%(a.Cylinder().Radius(),ax.Direction().X(),ax.Direction().Y(),ax.Direction().Z())
        info+=" bb x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"%(X[0],X[3],X[1],X[4],X[2],X[5])
        out.append(info)
    print(i,out); i+=1; we.Next()
