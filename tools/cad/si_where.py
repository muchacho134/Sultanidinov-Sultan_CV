import sys, collections
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopAbs import TopAbs_FACE
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
c=BRepAlgoAPI_Check(s,True,True); res=list(c.Result()); print(sys.argv[1].split('/')[-1],"self-intersections:",len(res))
zs=collections.Counter()
for r in res:
    for L in (r.GetFaultyShapes1(),r.GetFaultyShapes2()):
        for sh in L:
            if sh.ShapeType()==TopAbs_FACE:
                b=Bnd_Box(); BRepBndLib.Add_s(sh,b); x=b.Get(); zs[(str(BRepAdaptor_Surface(TopoDS.Face_s(sh)).GetType()).split('.')[-1][8:],round(x[2]),round(x[5]),round(x[1]),round(x[4]))]+=1
for k,v in zs.most_common(8): print("  face involved:",k,"x",v)
