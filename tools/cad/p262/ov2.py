exec(open("finish.py").read().split("H=sol")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
def report(tag,M):
    a=BOPAlgo_ArgumentAnalyzer(); a.SetShape1(M); a.SelfInterMode=True; a.Perform()
    print(tag,'solids',len(sol(M)),'vol',round(vol(M),3),'valid',BRepCheck_Analyzer(M).IsValid(),'selfint',a.GetCheckResult().Size(),'bbox',bb(M),'faces',len(faces(M)))
M=rd('M1.brep'); P=rd('work/p027.brep')
ov=BRepAlgoAPI_Common(M,P).Shape()
for fz in [0.0,1e-4,1e-3]:
    c=BRepAlgoAPI_Cut(); from OCP.TopTools import TopTools_ListOfShape
    A=TopTools_ListOfShape(); A.Append(M); T=TopTools_ListOfShape(); T.Append(ov)
    c.SetArguments(A); c.SetTools(T); c.SetFuzzyValue(fz); c.Build(); R=c.Shape()
    u=ShapeUpgrade_UnifySameDomain(R,True,True,False); u.Build(); R=u.Shape()
    report('cut fz=%g'%fz,R)
    o=BRepAlgoAPI_Common(R,P).Shape(); print('   overlap P223 now',round(vol(o),5))
    BRepTools.Write_s(R,'M2_%g.brep'%fz)
