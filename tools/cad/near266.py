import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); seq=TDF_LabelSequence(); st.GetShapes(seq)
T=(34.7,-195.0,84.2,34.7,92.93,97.2)
rows=[]
for i in range(1,seq.Length()+1):
    lab=seq.Value(i); a=TDataStd_Name()
    if not lab.FindAttribute(TDataStd_Name.GetID_s(),a): continue
    nm=a.Get().ToExtString()
    if not nm.startswith("조준경"): continue
    s=st.GetShape_s(lab)
    if s.ShapeType() not in (TopAbs_SHELL,TopAbs_SOLID): continue
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    d=0
    for k in range(3):
        lo,hi=x[k],x[k+3]; tl,th=T[k],T[k+3]
        d+=max(0,tl-hi,lo-th)**2
    rows.append((d**.5,nm.replace("조준경 + 짐벌 + 소총",""),str(s.ShapeType()).split('.')[-1],[round(v,1) for v in x]))
rows.sort(key=lambda r:r[0])
for r in rows[:8]: print(round(r[0],1),r[1],r[2],r[3])
allx=[r[3] for r in rows]
print("model extents y:",min(r[3][1] for r in rows),max(r[3][4] for r in rows)," x:",min(r[3][0] for r in rows),max(r[3][3] for r in rows))
