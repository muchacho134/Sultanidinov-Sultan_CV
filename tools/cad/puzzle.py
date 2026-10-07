import sys, pickle, numpy as np, collections
from scipy.spatial import cKDTree
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_UniformAbscissa, GCPnts_AbscissaPoint
from OCP.BRepTools import BRepTools
doc=TDocStd_Document(TCollection_ExtendedString("d")); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
parts={}
def walk(l):
    c=TDF_LabelSequence(); st.GetComponents_s(l,c)
    for i in range(1,c.Length()+1):
        comp=c.Value(i); ref=TDF_Label()
        if st.GetReferredShape_s(comp,ref):
            if st.IsAssembly_s(ref): walk(ref)
            else: parts[name(ref).replace("조준경 + 짐벌 + 소총","P")]=st.GetShape_s(comp)
for i in range(1,roots.Length()+1): walk(roots.Value(i))
print("parts",len(parts))
STEP=0.1
pts=[]; lab=[]; isfree=[]; info={}
for k,s in parts.items():
    solid=TopExp_Explorer(s,TopAbs_SOLID).More()
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
    nfree=0; freelen=0.0
    for i in range(1,m.Extent()+1):
        e=TopoDS.Edge_s(m.FindKey(i)); free=(m.FindFromIndex(i).Size()==1)
        if solid: free=False
        try:
            c=BRepAdaptor_Curve(e); L=GCPnts_AbscissaPoint.Length_s(c)
        except Exception: continue
        if L<1e-6: continue
        n=max(3,int(L/STEP)+1)
        us=np.linspace(c.FirstParameter(),c.LastParameter(),n)
        P=np.array([[c.Value(u).X(),c.Value(u).Y(),c.Value(u).Z()] for u in us])
        pts.append(P); lab+= [k]*len(P); isfree+=[free]*len(P)
        if free: nfree+=1; freelen+=L
    info[k]=dict(solid=solid,nfree=nfree,freelen=freelen)
P=np.concatenate(pts); lab=np.array(lab); isfree=np.array(isfree)
print("sample points",len(P))
tree=cKDTree(P)
pickle.dump(dict(P=P,lab=lab,isfree=isfree,info=info),open("work/puzzle_pts.pkl","wb"))
# for each free sample point, find points of OTHER parts within tol
TOL=float(sys.argv[2]) if len(sys.argv)>2 else 0.05
idx=np.where(isfree)[0]
nb=tree.query_ball_point(P[idx],TOL)
W=collections.Counter()   # (A,B) -> matched free length on A
for i,cand in zip(idx,nb):
    a=lab[i]; others=set(lab[j] for j in cand if lab[j]!=a)
    for b in others: W[(a,b)]+=STEP
pickle.dump(dict(W=W,info=info,tol=TOL),open("work/puzzle_graph.pkl","wb"))
print("matched pairs:",len(W))
