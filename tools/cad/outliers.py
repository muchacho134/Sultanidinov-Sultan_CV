import sys
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
for fn in sys.argv[1:]:
    s=rd(fn); ex=TopExp_Explorer(s,TopAbs_FACE); i=0; out=[]
    while ex.More():
        b=Bnd_Box(); BRepBndLib.AddOptimal_s(ex.Current(),b,False,False); x=b.Get()
        if x[0]<-20.5 or x[3]>20.5 or x[1]<-297 or x[4]>-201 or x[2]<69 or x[5]>297:
            out.append((i,str(BRepAdaptor_Surface(TopoDS.Face_s(ex.Current())).GetType()).split('.')[-1][8:],[round(v,1) for v in x]))
        ex.Next(); i+=1
    print(fn,len(out)); [print("  ",o) for o in out]
