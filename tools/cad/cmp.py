import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepCheck import BRepCheck_Analyzer
def load(p):
    doc=TDocStd_Document(TCollection_ExtendedString("d")); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(p); rd.Transfer(doc)
    st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
    parts={}
    def name(l):
        a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
    def walk(l):
        c=TDF_LabelSequence(); st.GetComponents_s(l,c)
        for i in range(1,c.Length()+1):
            comp=c.Value(i); ref=TDF_Label()
            if st.GetReferredShape_s(comp,ref):
                if st.IsAssembly_s(ref): walk(ref)
                else: parts[name(ref)]=st.GetShape_s(comp)
    for i in range(1,roots.Length()+1): walk(roots.Value(i))
    return parts
def info(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); has=TopExp_Explorer(s,TopAbs_SOLID).More()
    p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p)
    return [round(v,2) for v in b.Get()],has,round(p.Mass(),1)
A=load(sys.argv[1]); B=load(sys.argv[2])
print("parts original:",len(A)," new:",len(B))
print("missing in new:",[k[-3:] for k in A if k not in B]," added in new:",[k[-3:] for k in B if k not in A])
chg=[k[-3:] for k in A if k in B and info(A[k])[0]!=info(B[k])[0]]
print("parts whose placed bbox changed:",chg)
k=[x for x in B if x.endswith("262")][0]
print("rail 262 before:",info(A[k])); print("rail 262 after: ",info(B[k]))
ns=lambda P:sum(1 for s in P.values() if TopExp_Explorer(s,TopAbs_SOLID).More())
print("solids original:",ns(A)," new:",ns(B))
print("rail valid:",BRepCheck_Analyzer(B[k]).IsValid())
