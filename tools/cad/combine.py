import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Interface import Interface_Static
files=[("work/grouped_m_lean.step","Gun"),("work/addin/gunstruct.step","Gun_structure"),("work/addin/body.step","Body_with_handles"),("work/addin/handle.step","Handle_all_solids"),("work/addin/motor.step","Motor")]
doc=TDocStd_Document(TCollection_ExtendedString("d")); st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def free():
    fs=TDF_LabelSequence(); st.GetFreeShapes(fs); return [fs.Value(i) for i in range(1,fs.Length()+1)]
roots=[]
for fn,nm in files:
    before=set(l.Tag() for l in free())
    r=STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True); r.SetLayerMode(True); r.SetPropsMode(True)
    r.ReadFile(fn); r.Transfer(doc)
    new=[l for l in free() if l.Tag() not in before]; print(fn,"new roots",len(new)); roots.append((nm,new))
top=st.NewShape(); TDataStd_Name.Set_s(top,TCollection_ExtendedString("Gun_drone_full_assembly"))
for nm,labs in roots:
    for i,l in enumerate(labs):
        c=st.AddComponent(top,l,TopLoc_Location())
        TDataStd_Name.Set_s(c,TCollection_ExtendedString(nm if len(labs)==1 else f"{nm}_{i+1}"))
        if nm=="Gun_structure": TDataStd_Name.Set_s(l,TCollection_ExtendedString("Gun_structure"))
st.UpdateAssemblies()
print("free roots now",len(free()))
Interface_Static.SetIVal_s("write.surfacecurve.mode",0)
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(sys.argv[1]); print("written")
