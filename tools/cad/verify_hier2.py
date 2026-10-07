import sys, numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopLoc import TopLoc_Location
def load(p):
    doc=TDocStd_Document(TCollection_ExtendedString("d")); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(p); rd.Transfer(doc)
    st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
    def name(l):
        a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
    tree={}; placed={}
    def walk(l,loc,path):
        c=TDF_LabelSequence(); st.GetComponents_s(l,c)
        for i in range(1,c.Length()+1):
            comp=c.Value(i); ref=TDF_Label(); st.GetReferredShape_s(comp,ref)
            L=loc.Multiplied(st.GetLocation_s(comp))
            if st.IsAssembly_s(ref): walk(ref,L,path+[name(ref)])
            else:
                tree.setdefault(" / ".join(path),[]).append(name(ref))
                s=st.GetShape_s(ref).Moved(L); b=Bnd_Box(); BRepBndLib.Add_s(s,b)
                if b.IsVoid(): print("EMPTY PART:",name(ref).replace("조준경 + 짐벌 + 소총","P"),"in",path[-1]); continue
                placed[name(ref)]=np.array(b.Get())
    for i in range(1,roots.Length()+1): walk(roots.Value(i),TopLoc_Location(),[name(roots.Value(i))])
    return tree,placed
tA,pA=load(sys.argv[1]); tB,pB=load(sys.argv[2])
print("BEFORE:",{k:len(v) for k,v in tA.items()})
print("AFTER tree:")
for k in sorted(tB): print("  ",k.replace("조준경 + 짐벌 + 소총","ROOT "),":",len(tB[k]),"parts")
print("parts before/after:",len(pA),len(pB),"| names identical:",set(pA)==set(pB))
moved=[k for k in pA if np.abs(pA[k]-pB[k]).max()>1e-3]; print("parts whose position changed:",moved)
