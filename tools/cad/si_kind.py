import sys, collections
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.ShapeFix import ShapeFix_Shape
s=rd(sys.argv[1])
if len(sys.argv)>2: f=ShapeFix_Shape(s); f.Perform(); s=f.Shape(); BRepTools.Write_s(s,sys.argv[2])
c=BRepAlgoAPI_Check(s,True,True); r=list(c.Result())
k=collections.Counter((str(x.GetCheckStatus()).split('.')[-1], tuple(str(sh.ShapeType()).split('.')[-1] for sh in x.GetFaultyShapes1())) for x in r)
print(len(r)); [print(" ",a,b) for a,b in k.most_common(6)]
