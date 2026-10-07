exec(open("finish.py").read().split("H=sol")[0])
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_SHELL
M=rd(sys.argv[1])
a=BOPAlgo_ArgumentAnalyzer(); a.SetShape1(M); a.SelfInterMode=True; a.Perform()
fb=ShapeAnalysis_FreeBounds(M,1e-4,False,False); nfree=0
for w in (fb.GetClosedWires(),fb.GetOpenWires()):
    e=TopExp_Explorer(w,TopAbs_EDGE)
    while e.More(): nfree+=1; e.Next()
nsh=0; e=TopExp_Explorer(M,TopAbs_SHELL)
while e.More(): nsh+=1; e.Next()
print('solids',len(sol(M)),'shells',nsh,'free edges',nfree,'valid',BRepCheck_Analyzer(M).IsValid(),'self-intersections',a.GetCheckResult().Size())
print('volume',round(vol(M),1),'faces',len(faces(M)),'bbox',bb(M))
for nm,p in [('Gas_Cylinder','work/p017.brep'),('P213','work/p008.brep'),('P223','work/p027.brep'),('P214','work/p055.brep')]:
    T=rd(p); c=BRepAlgoAPI_Common(M,T).Shape(); d=BRepExtrema_DistShapeShape(M,T); d.Perform()
    print(f'  {nm:12s} overlap {vol(c):.4f} mm3   min distance {d.Value():.3f} mm')
# handguard-region clearances only (z<=66.93)
hb=BRepPrimAPI_MakeBox(gp_Pnt(-40,-300,-216),gp_Pnt(40,-200,66.93)).Shape()
Mh=BRepAlgoAPI_Common(M,hb).Shape()
for nm,p in [('Gas_Cylinder','work/p017.brep'),('P213','work/p008.brep')]:
    d=BRepExtrema_DistShapeShape(Mh,rd(p)); d.Perform(); print(f'  handguard clearance to {nm}: {d.Value():.3f} mm')
rb=BRepPrimAPI_MakeBox(gp_Pnt(-40,-300,66.94),gp_Pnt(40,-200,226)).Shape()
Mr=BRepAlgoAPI_Common(M,rb).Shape(); print('  over receiver (z>66.93): lowest y =',round(bb(Mr)[1],3),' width x',bb(Mr)[0],bb(Mr)[3])
