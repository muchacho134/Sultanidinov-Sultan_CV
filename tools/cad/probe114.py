import sys, numpy as np, collections
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRep import BRep_Tool
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
            else: parts[name(ref)]=(st.GetShape_s(comp),comp,ref)
for i in range(1,roots.Length()+1): walk(roots.Value(i))
def bb(s): b=Bnd_Box(); BRepBndLib.Add_s(s,b); return np.array(b.Get())
O=np.array([4.74,-241.16,-237.85]); A=np.array([0.866,0.5,0.0]); A/=np.linalg.norm(A)
def tr(P): d=P-O; t=d@A; return t,np.linalg.norm(d-np.outer(t,A),axis=1)
def fverts(f):
    vm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_VERTEX,vm)
    return np.array([[BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).X(),BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).Y(),BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).Z()] for i in range(1,vm.Extent()+1)])
k114=[k for k in parts if k.endswith("114")][0]; s114=parts[k114][0]
rows=[]; ex=TopExp_Explorer(s114,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t,r=tr(fverts(f)); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    rows.append((str(a.GetType()).split('.')[-1][8:],t.min(),t.max(),r.max(),p.Mass())); ex.Next()
pl=[x for x in rows if x[0]=="Plane"]
print("114 planar faces:",len(pl)," with t_min<6.4:",sum(1 for x in pl if x[1]<6.4)," with t_min>=6.4:",sum(1 for x in pl if x[1]>=6.4))
print("114 planar faces with t_min<6.4:",[(round(x[1],2),round(x[2],2),round(x[3],2),round(x[4],3)) for x in pl if x[1]<6.4][:10])
# tiny neighbour parts
b114=bb(s114); lo=b114[:3]-3; hi=b114[3:]+3
cand=[]
for k,(s,c,r) in parts.items():
    if k==k114: continue
    b=bb(s)
    if (b[:3]>=lo).all() and (b[3:]<=hi).all():
        fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
        cand.append((k[-12:],str(s.ShapeType()).split('.')[-1],fm.Extent(),round(p.Mass(),3),[round(v,1) for v in b]))
print("parts fully inside 114's neighbourhood (±3 mm):",len(cand))
for c in cand: print(" ",c)
