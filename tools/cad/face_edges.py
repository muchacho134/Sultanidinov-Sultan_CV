import sys
exec(open("p110_sec.py").read().split("A=rd(")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepTools import BRepTools_WireExplorer
S=rd(sys.argv[1]); B=[float(v) for v in sys.argv[2].split(",")]
ex=TopExp_Explorer(S,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); x=b.Get()
    if not (x[3]<B[0] or x[0]>B[3] or x[4]<B[1] or x[1]>B[4] or x[5]<B[2] or x[2]>B[5]):
        a=BRepAdaptor_Surface(f); print("face",i,str(a.GetType()).split('.')[-1][8:],"x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(x[0],x[3],x[1],x[4],x[2],x[5]))
        w=TopExp_Explorer(f,TopAbs_WIRE)
        while w.More():
            we=BRepTools_WireExplorer(TopoDS.Wire_s(w.Current()),f)
            while we.More():
                c=BRepAdaptor_Curve(we.Current()); p=c.Value(c.FirstParameter()); q=c.Value(c.LastParameter())
                print("    (%.2f,%.2f,%.2f)-(%.2f,%.2f,%.2f)"%(p.X(),p.Y(),p.Z(),q.X(),q.Y(),q.Z())); we.Next()
            w.Next()
    i+=1; ex.Next()
