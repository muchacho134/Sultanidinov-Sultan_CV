import sys, random, math; sys.path.insert(0,'.')
from load import *
from OCP.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax2, gp_Trsf, gp_Ax1, gp_Pln
from OCP.GC import GC_MakeArcOfCircle, GC_MakeSegment
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform, BRepBuilderAPI_Sewing)
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from OCP.BOPAlgo import BOPAlgo_MakerVolume, BOPAlgo_ArgumentAnalyzer
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN, TopAbs_WIRE
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Shape, TopoDS_Compound
XM=0.01; ZF=-215.0; ZR=66.93; ZB=225.0; YCUT=-230.7; FZ=float(sys.argv[1]) if len(sys.argv)>1 else 0.005
O=load('in/rail_completed.step')
def P(x,y,z=0): return gp_Pnt(x,y,z)
def mx(x): return 2*XM-x
# ---- cavity half profile (right), then mirrored
cx,cy,R=XM,-243.9,10.195
gy=-236.05; gx=cx+math.sqrt(R*R-(gy-cy)**2)
fx=cx+R
pts_r=[('L',(15.01,-290.0),(15.01,-253.449)),
       ('A',(15.01,-253.449),(14.706,-251.919),(13.838,-250.621)),
       ('L',(13.838,-250.621),(11.376,-248.159)),
       ('A',(11.376,-248.159),(10.504,-246.861),(fx,-245.33)),
       ('L',(fx,-245.33),(fx,cy)),
       ('A',(fx,cy),(cx+R*math.cos(math.radians(24)),cy+R*math.sin(math.radians(24))),(gx,gy)),
       ('L',(gx,gy),(gx,-231.11))]
def edge(seg,mir=False,z=ZF-1):
    f=(lambda p:(mx(p[0]),p[1])) if mir else (lambda p:p)
    if seg[0]=='L': a,b=f(seg[1]),f(seg[2]); return BRepBuilderAPI_MakeEdge(P(*a,z),P(*b,z)).Edge()
    a,m,b=f(seg[1]),f(seg[2]),f(seg[3]); return BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(*a,z),P(*m,z),P(*b,z)).Value()).Edge()
w=BRepBuilderAPI_MakeWire()
for s in pts_r: w.Add(edge(s))
w.Add(BRepBuilderAPI_MakeEdge(P(gx,-231.11,ZF-1),P(mx(gx),-231.11,ZF-1)).Edge())
for s in reversed(pts_r):
    s2=(s[0],)+tuple(reversed(s[1:])); w.Add(edge(s2,True))
w.Add(BRepBuilderAPI_MakeEdge(P(mx(15.01),-290,ZF-1),P(15.01,-290,ZF-1)).Edge())
assert w.IsDone()
cav=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(w.Wire(),True).Face(),gp_Vec(0,0,ZR-(ZF-1))).Shape()
print('cavity vol',round(vol(cav),1),'valid',BRepCheck_Analyzer(cav).IsValid())
BRepTools.Write_s(cav,'cav.brep')
# ---- planar patches for holes (right side): find free wires and planar-fill those named
sw=BRepBuilderAPI_Sewing(1e-3)
for f in faces(O): sw.Add(f)
sw.Perform(); Osew=sw.SewedShape()
fb=ShapeAnalysis_FreeBounds(Osew,1e-3,False,False)
patches=[]; e=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while e.More():
    wi=TopoDS.Wire_s(e.Current()); b=bb(wi)
    if b[0]>XM and (abs(b[1]+277.9)<0.01 and abs(b[4]+272.9)<0.01 and b[2]<-160)  or (b[0]>10 and abs(b[0]-b[3])<0.02 and b[1]>-224):
        mf=BRepBuilderAPI_MakeFace(wi,True)
        print('patch',b,'ok',mf.IsDone())
        if mf.IsDone(): patches.append(mf.Face())
    e.Next()
# hole 21 (right lower wall bottom, z -163..55.23): rebuild faces from its own edges
def poly(ps):
    ww=BRepBuilderAPI_MakeWire()
    for i in range(len(ps)): ww.Add(BRepBuilderAPI_MakeEdge(P(*ps[i]),P(*ps[(i+1)%len(ps)])).Edge())
    return BRepBuilderAPI_MakeFace(ww.Wire(),True).Face()
wb=BRepBuilderAPI_MakeWire()
wb.Add(BRepBuilderAPI_MakeEdge(P(15.01,-277.9,-163),P(18.01,-277.9,-163)).Edge())
wb.Add(BRepBuilderAPI_MakeEdge(P(18.01,-277.9,-163),P(18.01,-277.9,50.23)).Edge())
wb.Add(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P(18.01,-277.9,50.23),P(18.288,-277.9,52.57),P(19.108,-277.9,54.78)).Value()).Edge())
wb.Add(BRepBuilderAPI_MakeEdge(P(19.108,-277.9,54.78),P(18.835,-277.9,55.23)).Edge())
wb.Add(BRepBuilderAPI_MakeEdge(P(18.835,-277.9,55.23),P(15.01,-277.9,55.23)).Edge())
wb.Add(BRepBuilderAPI_MakeEdge(P(15.01,-277.9,55.23),P(15.01,-277.9,-163)).Edge())
patches.append(BRepBuilderAPI_MakeFace(wb.Wire(),True).Face())
patches.append(poly([(15.01,-277.9,55.23),(18.835,-277.9,55.23),(18.835,-272.9,55.23),(15.01,-272.9,55.23)]))
patches.append(poly([(18.835,-277.9,55.23),(19.108,-277.9,54.78),(19.108,-272.9,54.78),(18.835,-272.9,55.23)]))
patches.append(poly([(15.01,-277.9,50.23),(15.01,-277.9,55.23),(15.01,-272.9,55.23),(15.01,-272.9,50.23)]))
# window end fillets missing on windows 12-17: copy from window 19 / window 13 (pitch 31.11)
def tr(f,dz):
    T=gp_Trsf(); T.SetTranslation(gp_Vec(0,0,dz)); return BRepBuilderAPI_Transform(f,T,True).Shape()
src5=[f for f in faces(O) if all(abs(u-v)<0.06 for u,v in zip(bb(f),(10.0,-243.0,29.9,12.0,-242.0,32.5)))]
src9=[f for f in faces(O) if all(abs(u-v)<0.06 for u,v in zip(bb(f),(9.18,-242.97,-109.83,12.03,-239.44,-107.83)))]
print('src faces',len(src5),len(src9))
for st in [-166.31,-135.19,-104.08,-72.97,-41.85,-10.74]: patches.append(tr(src5[0],st-20.38))
patches.append(tr(src9[0],-166.31-(-135.19)))
srcb=[f for f in faces(O) if all(abs(u-v)<0.06 for u,v in zip(bb(f),(10.16,-242.97,32.47,12.03,-242.97,45.74)))]
print('src bottom',len(srcb))
for st in [-166.31,-135.19,-104.08,-72.97,-41.85,-10.74]: patches.append(tr(srcb[0],st-20.38))
# ---- cutting planes
def rect(pl, u0,u1,v0,v1):
    return BRepBuilderAPI_MakeFace(pl,u0,u1,v0,v1).Face()
def face_pts(p0,p1,p2,p3):
    ww=BRepBuilderAPI_MakeWire()
    for a,b in [(p0,p1),(p1,p2),(p2,p3),(p3,p0)]: ww.Add(BRepBuilderAPI_MakeEdge(P(*a),P(*b)).Edge())
    return BRepBuilderAPI_MakeFace(ww.Wire(),True).Face()
planes=[face_pts((XM,-300,ZF-2),(XM,-210,ZF-2),(XM,-210,ZB+2),(XM,-300,ZB+2)),   # symmetry
        face_pts((-40,-300,ZF),(40,-300,ZF),(40,-210,ZF),(-40,-210,ZF)),             # front lid
        face_pts((-40,-300,ZR),(40,-300,ZR),(40,YCUT,ZR),(-40,YCUT,ZR)),             # handguard rear end
        face_pts((-40,YCUT,ZR),(40,YCUT,ZR),(40,YCUT,ZB+2),(-40,YCUT,ZB+2)),         # strip underside
        face_pts((-40,-300,ZB),(40,-300,ZB),(40,-210,ZB),(-40,-210,ZB))]  # rear lid
args=[f for f in faces(O) if bb(f)[3]>XM+1e-4]+patches+faces(cav)+planes
print('args',len(args))
mv=BOPAlgo_MakerVolume(); L=TopTools_ListOfShape()
for a in args: L.Append(a)
mv.SetArguments(L); mv.SetFuzzyValue(FZ); mv.SetRunParallel(True); mv.SetIntersect(True); mv.Perform()
print('mv errors',mv.HasErrors(), 'warnings', mv.HasWarnings())
R_=mv.Shape(); cells=[]; e=TopExp_Explorer(R_,TopAbs_SOLID)
while e.More(): cells.append(TopoDS.Solid_s(e.Current())); e.Next()
print('cells',len(cells))
ccl=BRepClass3d_SolidClassifier(cav)
random.seed(3); keep=[]
for c in cells:
    b=bb(c); cl=BRepClass3d_SolidClassifier(c); p=None
    for _ in range(40000):
        q=P(*[random.uniform(b[i],b[i+3]) for i in range(3)]); cl.Perform(q,1e-7)
        if cl.State()==TopAbs_IN: p=q; break
    if p is None: print('  no interior pt',b,vol(c)); continue
    ccl.Perform(p,1e-7); incav=ccl.State()==TopAbs_IN
    ok=(p.X()>XM) and (ZF<p.Z()<ZB) and not incav and not (p.Z()>ZR and p.Y()<YCUT)
    if ok: keep.append(c)
    if vol(c)>1 or ok: print('  cell v=%.1f keep=%s incav=%s'%(vol(c),ok,incav),b)
BRepTools.Write_s(R_,'mv_cells.brep')
comp=TopoDS_Compound(); bld=BRep_Builder(); bld.MakeCompound(comp)
for c in keep: bld.Add(comp,c)
BRepTools.Write_s(comp,'keep_cells.brep')
print('kept',len(keep),'vol',round(sum(vol(c) for c in keep),1))
