import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape, TopTools_IndexedDataMapOfShapeListOfShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRepCheck import BRepCheck_Analyzer
def rail(path):
    r=STEPControl_Reader(); r.ReadFile(path); r.TransferRoots(); root=r.OneShape()
    n_sol=0; ex=TopExp_Explorer(root,TopAbs_SOLID)
    while ex.More(): n_sol+=1; ex.Next()
    ex=TopExp_Explorer(root,TopAbs_SHELL,TopAbs_SOLID); shells=[]
    while ex.More(): shells.append(ex.Current()); ex.Next()
    for s in shells:
        b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
        if abs(x[2]+215)<0.1 and abs(x[5]-225)<0.1 and abs(x[0]+29)<0.1: return root,s,n_sol,len(shells)
root,s,ns,nsh=rail(sys.argv[1]); print(sys.argv[1].split('/')[-1],"solids",ns,"open shells",nsh)
ew=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,ew)
free_in_gap=0; free_total=0
for i in range(1,ew.Extent()+1):
    if ew.FindFromIndex(i).Size()==1:
        free_total+=1
        b=Bnd_Box(); BRepBndLib.Add_s(ew.FindKey(i),b); x=b.Get()
        if x[2]>-15 and x[5]<45 and x[4]>-224 and x[1]<-220.5 : free_in_gap+=1
print(" valid",BRepCheck_Analyzer(s).IsValid()," free edges total",free_total," free edges on tooth profile inside gap window",free_in_gap)
zs=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if a.GetType()==GeomAbs_Plane and abs(a.Plane().Axis().Direction().Z())>0.99:
        b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
        if abs((x[3]-x[0])-21.2)<0.3: zs.append(round(x[2],2))
    ex.Next()
zs.sort(); gaps=[round(b-a,2) for a,b in zip(zs,zs[1:])]
print(" rib wall faces:",len(zs)," largest spacing:",max(gaps)," spacings seen:",sorted(set(gaps)))
