import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE
from OCP.BRepCheck import BRepCheck_Analyzer
doc=TDocStd_Document(TCollection_ExtendedString("d")); r=STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(sys.argv[1]); r.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); depth=int(sys.argv[2]) if len(sys.argv)>2 else 3
def nm(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else "?"
def cnt(s,t):
    e=TopExp_Explorer(s,t); n=0
    while e.More(): n+=1; e.Next()
    return n
leaves=[0,0,0]
def walk(l,loc,d):
    ref=TDF_Label(); tgt=l; name=nm(l)
    if st.IsReference_s(l): st.GetReferredShape_s(l,ref); tgt=ref; loc=loc.Multiplied(st.GetLocation_s(l)); name=name if name!="?" else nm(ref)
    if st.IsAssembly_s(tgt):
        cs=TDF_LabelSequence(); st.GetComponents_s(tgt,cs)
        if d<depth: print("  "*d+"[A] %s (%d children)"%(name,cs.Length()))
        for i in range(1,cs.Length()+1): walk(cs.Value(i),loc,d+1)
    else:
        s=st.GetShape_s(tgt).Moved(loc); b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
        ns=cnt(s,TopAbs_SOLID); leaves[0]+=1; leaves[1]+=ns; leaves[2]+= (not BRepCheck_Analyzer(s).IsValid())
        if d<depth: print("  "*d+"- %s solids %d faces %d bb x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]"%(name,ns,cnt(s,TopAbs_FACE),x[0],x[3],x[1],x[4],x[2],x[5]))
fs=TDF_LabelSequence(); st.GetFreeShapes(fs)
for i in range(1,fs.Length()+1): walk(fs.Value(i),TopLoc_Location(),0)
print("LEAVES",leaves[0],"solids",leaves[1],"invalid",leaves[2])
