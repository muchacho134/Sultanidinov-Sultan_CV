import sys; sys.path.insert(0,'.')
from load import *
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Shape
from OCP.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopAbs import TopAbs_EDGE
def rd(p):
    s=TopoDS_Shape(); BRepTools.Read_s(s,p,BRep_Builder()); return s
def sol(s):
    e=TopExp_Explorer(s,TopAbs_SOLID); o=[]
    while e.More(): o.append(e.Current()); e.Next()
    return o
H=sol(rd('keep_cells.brep'))[0]
T=gp_Trsf(); T.SetMirror(gp_Ax2(gp_Pnt(0.01,0,0),gp_Dir(1,0,0)))
Hm=BRepBuilderAPI_Transform(H,T,True).Shape()
f=BRepAlgoAPI_Fuse(H,Hm); f.SetFuzzyValue(1e-4); f.Build(); M=f.Shape()
u=ShapeUpgrade_UnifySameDomain(M,True,True,True); u.Build(); M=u.Shape()
ss=sol(M)
a=BOPAlgo_ArgumentAnalyzer(); a.SetShape1(M); a.SelfInterMode=True; a.Perform()
fb=ShapeAnalysis_FreeBounds(M,1e-4,False,False); nfree=0
for w in (fb.GetClosedWires(),fb.GetOpenWires()):
    e=TopExp_Explorer(w,TopAbs_EDGE)
    while e.More(): nfree+=1; e.Next()
print('solids',len(ss),'vol',round(vol(M),1),'valid',BRepCheck_Analyzer(M).IsValid(),'selfint',a.GetCheckResult().Size(),'free edges',nfree,'faces',len(faces(M)),'bbox',bb(M))
BRepTools.Write_s(M,'P262_fixed.brep')
for nm,p in [('Gas_Cylinder','work/p017.brep'),('P213','work/p008.brep'),('P223','work/p027.brep'),('P214','work/p055.brep')]:
    c=BRepAlgoAPI_Common(M,rd(p)).Shape(); print(f'  overlap {nm}: {vol(c):.4f} mm3')
