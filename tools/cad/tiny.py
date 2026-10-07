import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
s=rd(sys.argv[1]); th=float(sys.argv[2]); ex=TopExp_Explorer(s,TopAbs_FACE); i=0; n=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=abs(area(f))
    if a<th:
        b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); X=b.Get(); n+=1
        print(i,"t%d A %.4f"%(int(BRepAdaptor_Surface(f).GetType()),a),"x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(X[0],X[3],X[1],X[4],X[2],X[5]))
    i+=1; ex.Next()
print("tiny faces",n,"of",i)
