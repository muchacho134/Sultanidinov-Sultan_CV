import sys
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
s=rd(sys.argv[1]); B=[float(v) for v in sys.argv[2].split(",")]
ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(ex.Current(),b,False,False); x=b.Get()
    if x[0]>=B[0] and x[3]<=B[3] and x[1]>=B[1] and x[4]<=B[4] and x[2]>=B[2] and x[5]<=B[5]:
        a=BRepAdaptor_Surface(TopoDS.Face_s(ex.Current())); t=str(a.GetType()).split('.')[-1][8:]
        p=GProp_GProps(); BRepGProp.SurfaceProperties_s(ex.Current(),p)
        print(i,t,"area %.3f"%p.Mass(),"x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(x[0],x[3],x[1],x[4],x[2],x[5]))
    i+=1; ex.Next()
