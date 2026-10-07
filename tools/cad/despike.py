exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCP.BRepTools import BRepTools_WireExplorer, BRepTools as BT
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.BRepAdaptor import BRepAdaptor_Surface
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
s=rd("work/p244_s15.brep"); F=[]; ex=TopExp_Explorer(s,TopAbs_FACE); tgt=None
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); X=b.Get()
    if abs(X[1]+283.1)<0.02 and abs(X[4]+283.1)<0.02 and X[3]-X[0]>25 and X[2]>160 and X[2]<170: tgt=f
    else: F.append(f)
    ex.Next()
E=[]; we=BRepTools_WireExplorer(BT.OuterWire_s(tgt),tgt)
while we.More(): E.append(TopoDS.Edge_s(we.Current())); we.Next()
P=lambda v:BRep_Tool.Pnt_s(v)
def ends(e): 
    a=P(TopExp.FirstVertex_s(e,True)); b=P(TopExp.LastVertex_s(e,True)); return a,b
for i,e in enumerate(E):
    a,b=ends(e)
    if a.Z()>255.5 or b.Z()>255.5: print(i,"(%.3f,%.3f)->(%.3f,%.3f)"%(a.X(),a.Z(),b.X(),b.Z()))
from OCP.gp import gp_Pnt
idx={}
for i,e in enumerate(E):
    a,b=ends(e)
    if abs(a.Z()-256.22)<0.01 and abs(b.Z()-256.22)<0.01: idx[i]=(a,b)
long=[i for i,(a,b) in idx.items() if abs(a.X()-b.X())>20][0]
short=[i for i in idx if i!=long]
print("long",long,"short",short)
xs=sorted([idx[long][0].X(),idx[long][1].X()]+[idx[i][k].X() for i in short for k in (0,1)])
# keep only pieces of the long edge not covered by a short edge
cov=[sorted([idx[i][0].X(),idx[i][1].X()]) for i in short]
pts={}
for i in list(short)+[long]:
    for q in idx[i]: pts[round(q.X(),3)]=q
keys=sorted(pts)
newE=[]
for x0,x1 in zip(keys[:-1],keys[1:]):
    mid=(x0+x1)/2
    if any(c[0]-1e-3<mid<c[1]+1e-3 for c in cov): continue
    newE.append(BRepBuilderAPI_MakeEdge(pts[x0],pts[x1]).Edge())
rest=[e for i,e in enumerate(E) if i not in idx]+newE
loops=[]; pool=rest[:]
while pool:
    cur=[pool.pop(0)]; a0,b=ends(cur[0])
    while b.Distance(a0)>1e-3:
        for k,e in enumerate(pool):
            a,bb=ends(e)
            if a.Distance(b)<2e-3: cur.append(pool.pop(k)); b=bb; break
            if bb.Distance(b)<2e-3: cur.append(TopoDS.Edge_s(pool.pop(k).Reversed())); b=a; break
        else: raise SystemExit("chain fail")
    loops.append(cur)
pl=BRepAdaptor_Surface(tgt).Plane(); NF=[]
for L in loops:
    mw=BRepBuilderAPI_MakeWire()
    for e in L: mw.Add(e)
    nf=BRepBuilderAPI_MakeFace(pl,mw.Wire(),True).Face()
    from OCP.ShapeFix import ShapeFix_Face
    sf=ShapeFix_Face(nf); sf.Perform(); nf=sf.Face()
    if area(nf)<0: nf=TopoDS.Face_s(nf.Reversed())
    print("loop edges",len(L),"area %.2f valid %s"%(area(nf),BRepCheck_Analyzer(nf).IsValid())); NF.append(nf)
sw=BRepBuilderAPI_Sewing(0.003)
for f in F: sw.Add(f)
for f in NF: sw.Add(f)
sw.Perform(); BRepTools.Write_s(sw.SewedShape(),"work/p244_s16.brep")
raise SystemExit
print("new face valid",BRepCheck_Analyzer(nf).IsValid(),"area %.2f"%area(nf))
sw=BRepBuilderAPI_Sewing(0.003)
for f in F: sw.Add(f)
sw.Add(nf); sw.Perform(); BRepTools.Write_s(sw.SewedShape(),"work/p244_s16.brep")
