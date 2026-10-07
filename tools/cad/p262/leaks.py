exec(open('build.py').read().split("print('args',len(args))")[0])
from OCP.BOPAlgo import BOPAlgo_Builder
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.BRep import BRep_Tool
gf=BOPAlgo_Builder()
for a in args: gf.AddArgument(a)
gf.SetFuzzyValue(FZ); gf.SetRunParallel(True); gf.Perform()
R=gf.Shape()
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(R,TopAbs_EDGE,TopAbs_FACE,m)
out=[]
for i in range(1,m.Extent()+1):
    e=m.FindKey(i)
    if BRep_Tool.Degenerated_s(TopoDS.Edge_s(e)): continue
    if m.FindFromIndex(i).Extent()==1:
        b=bb(e)
        if b[0]>=XM-0.05 and b[3]<19.2 and b[1]>-278.0 and b[4]<-220.6 and b[2]>ZF-0.05 and b[5]<ZB+0.05:
            # ignore edges lying in the cavity interior (cavity tool faces' own outer rims are at z=ZF-1/ZR or y=-290)
            out.append(b)
print('free edges in region',len(out))
for b in sorted(out,key=lambda b:b[2]): print([round(v,2) for v in b])
