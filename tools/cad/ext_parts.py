import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
doc=TDocStd_Document(TCollection_ExtendedString("d")); r=STEPCAFControl_Reader(); r.SetNameMode(True)
r.ReadFile(sys.argv[1]); r.Transfer(doc); st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def nm(l):
    a=TDataStd_Name()
    return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else "?"
out=[]
def walk(l,loc):
    ref=TDF_Label()
    if st.IsReference_s(l):
        st.GetReferredShape_s(l,ref); loc=loc.Multiplied(st.GetLocation_s(l)); name=nm(l); tgt=ref
    else: tgt=l; name=nm(l)
    if st.IsAssembly_s(tgt):
        cs=TDF_LabelSequence(); st.GetComponents_s(tgt,cs)
        for i in range(1,cs.Length()+1): walk(cs.Value(i),loc)
    else:
        s=st.GetShape_s(tgt).Moved(loc); out.append((name if name!="?" else nm(tgt),s))
fs=TDF_LabelSequence(); st.GetFreeShapes(fs)
for i in range(1,fs.Length()+1): walk(fs.Value(i),TopLoc_Location())
q=Bnd_Box(); q.Update(*eval(sys.argv[2]))
for n,s in out:
    b=Bnd_Box(); BRepBndLib.Add_s(s,b)
    if b.IsOut(q): continue
    k=n.replace("조준경 + 짐벌 + 소총","P").replace(" ","_"); BRepTools.Write_s(s,f"work/cur_{k}.brep"); print(k)
