import sys, collections
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
s=rd(sys.argv[1]); r=list(BRepAlgoAPI_Check(s,True,True).Result())
k=collections.Counter((str(x.GetCheckStatus()).split('.')[-1], tuple(str(sh.ShapeType()).split('.')[-1][7:] for sh in x.GetFaultyShapes1())) for x in r)
print(len(r)); [print(" ",a,b) for a,b in k.most_common(8)]
for x in r:
    st=str(x.GetCheckStatus()).split('.')[-1]
    if st=="BOPAlgo_TooSmallEdge": continue
    for L in (x.GetFaultyShapes1(),x.GetFaultyShapes2()):
        for sh in L:
            b=Bnd_Box(); BRepBndLib.Add_s(sh,b); v=b.Get(); print("  ",st[7:],str(sh.ShapeType()).split('.')[-1][7:],"x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"%(v[0],v[3],v[1],v[4],v[2],v[5]))
