import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepCheck import BRepCheck_Analyzer, BRepCheck_ListOfStatus
from OCP.TopAbs import TopAbs_VERTEX, TopAbs_SHELL, TopAbs_SOLID
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
s=rd(sys.argv[1]); a=BRepCheck_Analyzer(s)
for typ,nm in [(TopAbs_VERTEX,"V"),(TopAbs_EDGE,"E"),(TopAbs_FACE,"F"),(TopAbs_WIRE,"W"),(TopAbs_SHELL,"SH"),(TopAbs_SOLID,"SO")]:
    ex=TopExp_Explorer(s,typ); seen=0
    while ex.More():
        sub=ex.Current(); r=a.Result(sub)
        if r is not None:
            st=[int(x) for x in r.Status()]
            if any(x!=0 for x in st):
                b=Bnd_Box(); BRepBndLib.Add_s(sub,b); X=b.Get(); seen+=1
                if seen<15: print(nm,st,"x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]"%(X[0],X[3],X[1],X[4],X[2],X[5]))
        ex.Next()
    print(nm,"bad",seen)
