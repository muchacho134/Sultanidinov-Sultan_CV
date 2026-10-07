import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.BRepAdaptor import BRepAdaptor_Surface
s=rd(sys.argv[1]); Q=eval(sys.argv[2]); sw=BRepBuilderAPI_Sewing(0.003); ex=TopExp_Explorer(s,TopAbs_FACE); n=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); X=b.Get()
    if X[3]>Q[0] and X[0]<Q[3] and X[4]>Q[1] and X[1]<Q[4] and X[5]>Q[2] and X[2]<Q[5]:
        sw.Add(f); n+=1
        if len(sys.argv)>3: print("  t%d x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(int(BRepAdaptor_Surface(f).GetType()),X[0],X[3],X[1],X[4],X[2],X[5]))
    ex.Next()
sw.Perform(); r=[x for x in BRepAlgoAPI_Check(sw.SewedShape(),True,True).Result() if "TooSmall" not in str(x.GetCheckStatus())]
print(sys.argv[1],"faces",n,"SI",len(r))
for x in r:
    for L in (x.GetFaultyShapes1(),x.GetFaultyShapes2()):
        for sh in L:
            b=Bnd_Box(); BRepBndLib.Add_s(sh,b); v=b.Get(); print("   ",str(sh.ShapeType()).split('_')[-1],"x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(v[0],v[3],v[1],v[4],v[2],v[5]))
