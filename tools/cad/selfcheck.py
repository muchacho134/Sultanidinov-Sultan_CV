import sys
from collections import Counter
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
c=BRepAlgoAPI_Check(s,True,True)
print("valid:",c.IsValid())
cnt=Counter(); n=0
for it in c.Result():
    n+=1; cnt[str(it.GetCheckStatus()).split('.')[-1]]+=1
print("issues:",n,dict(cnt))
