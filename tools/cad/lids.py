import sys, numpy as np, mapbox_earcut as ec
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools, BRepTools_WireExplorer
from OCP.BRep import BRep_Builder
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.BRepBuilderAPI import *
from OCP.gp import gp_Pnt
from OCP.ShapeFix import ShapeFix_Solid, ShapeFix_Shell
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
src,out_brep,out_step,tol=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4])
s=TopoDS_Shape(); BRepTools.Read_s(s,src,BRep_Builder())
shell=TopoDS.Shell_s(TopExp_Explorer(s,TopAbs_SHELL).Current())
def wires(sh):
    fb=ShapeAnalysis_FreeBounds(sh,1e-3); L=[]
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More(): L.append(TopoDS.Wire_s(ex.Current())); ex.Next()
    return L
def ordered_points(w,defl=0.02):
    P=[]; we=BRepTools_WireExplorer(w)
    while we.More():
        e=we.Current(); c=BRepAdaptor_Curve(e); d=GCPnts_QuasiUniformDeflection(c,defl)
        pts=[np.array([d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()]) for k in range(1,d.NbPoints()+1)]
        if e.Orientation()==TopAbs_REVERSED: pts=pts[::-1]
        if P and np.linalg.norm(P[-1]-pts[0])>1e-6: pts=pts[::-1] if np.linalg.norm(P[-1]-pts[-1])<np.linalg.norm(P[-1]-pts[0]) else pts
        P+= pts if not P else pts[1:]
        we.Next()
    P=np.array(P)
    if np.linalg.norm(P[0]-P[-1])<1e-6: P=P[:-1]
    return P


def stitch(A,B):
    """triangulate the band between two closed 3D polylines (greedy shortest diagonal)"""
    def sa(P): 
        x,z=P[:,0],P[:,2]; return 0.5*np.sum(x*np.roll(z,-1)-np.roll(x,-1)*z)
    if sa(A)*sa(B)<0: B=B[::-1]
    j0=int(np.argmin(np.linalg.norm(B-A[0],axis=1))); B=np.roll(B,-j0,axis=0)
    n,m=len(A),len(B); i=j=0; tris=[]
    while i<n or j<m:
        if i>=n: adv='B'
        elif j>=m: adv='A'
        else:
            dA=np.linalg.norm(A[(i+1)%n]-B[j%m]); dB=np.linalg.norm(A[i%n]-B[(j+1)%m])
            adv='A' if dA<=dB else 'B'
        if adv=='A': tris.append((A[i%n],A[(i+1)%n],B[j%m])); i+=1
        else: tris.append((A[i%n],B[j%m],B[(j+1)%m])); j+=1
    return tris
def tri_face(pts):
    if np.linalg.norm(np.cross(pts[1]-pts[0],pts[2]-pts[0]))<1e-9: return None
    mp=BRepBuilderAPI_MakePolygon(*[gp_Pnt(*p) for p in pts],True); mf=BRepBuilderAPI_MakeFace(mp.Wire(),True)
    return mf.Face() if mf.IsDone() else None
def lid_pass(shell,first=False):
    faces=[]; report=[]
    W=wires(shell); PT=[ordered_points(w) for w in W]
    skip=set()
    if first and len(W)>=2:
        order=sorted(range(len(W)),key=lambda k:-len(PT[k]))[:2]   # the two big underside loops
        a,b=order; 
        for tr in stitch(PT[b],PT[a]):      # b = outer (fewer pts), a = comb-shaped inner
            f=tri_face(list(tr)); 
            if f is not None: faces.append(f)
        skip={a,b}; report.append(("stitched",a,b))
    for i,w in enumerate(W):
        if i in skip: continue
        P=PT[i]; c=P.mean(0); u,sv,vt=np.linalg.svd(P-c)
        XY=((P-c)@vt[:2].T).astype(np.float64)
        tri=ec.triangulate_float64(XY,np.array([len(XY)],dtype=np.uint32)).reshape(-1,3)
        ok=0
        for a_,b_,c_ in tri:
            f=tri_face([P[a_],P[b_],P[c_]])
            if f is not None: faces.append(f); ok+=1
        report.append((i,len(P),len(tri),ok))
    sw=BRepBuilderAPI_Sewing(tol); sw.Add(shell)
    for f in faces: sw.Add(f)
    sw.Perform(); res=sw.SewedShape()
    L=[]; ex=TopExp_Explorer(res,TopAbs_SHELL)
    while ex.More(): L.append(TopoDS.Shell_s(ex.Current())); ex.Next()
    return L,report
cur=shell
for ps in range(4):
    if not wires(cur): break
    L,rep=lid_pass(cur,first=False); cur=L[0]
    print("pass",ps+1,"loops lidded",len(rep),"-> shells",len(L),"remaining free loops",len(wires(cur)))
sh=cur
ms=BRepBuilderAPI_MakeSolid(sh); so=ms.Solid()
fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=TopoDS.Solid_s(fx.Solid())
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p); b=Bnd_Box(); BRepBndLib.Add_s(so,b)
print("solid valid:",BRepCheck_Analyzer(so).IsValid(),"volume %.1f"%p.Mass(),"bbox",[round(v,1) for v in b.Get()])
BRepTools.Write_s(so,out_brep)
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write(out_step)
