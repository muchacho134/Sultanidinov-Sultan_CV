import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
src,solid_path,out=sys.argv[1:4]
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.SetColorMode(True); rd.SetLayerMode(True); rd.SetPropsMode(True)
rd.ReadFile(src); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
roots=TDF_LabelSequence(); st.GetFreeShapes(roots); print("free shapes (roots):",roots.Length())
found={}
def walk(l):
    if st.IsAssembly_s(l):
        c=TDF_LabelSequence(); st.GetComponents_s(l,c)
        for i in range(1,c.Length()+1):
            comp=c.Value(i); ref=TDF_Label(); 
            if st.GetReferredShape_s(comp,ref):
                n=name(ref)
                if n.endswith("262") or n.endswith("266"): found[n[-3:]]=(l,comp,ref)
            walk(comp if not st.IsAssembly_s(comp) else comp)
for i in range(1,roots.Length()+1): walk(roots.Value(i))
print("found:",list(found))
asm,comp262,ref262=found["262"]
m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(st.GetShape_s(ref262),TopAbs_FACE,m); print("262 faces in file:",m.Extent())
loc=st.GetLocation_s(comp262); orig_name=name(ref262); orig_comp_name=name(comp262); print('orig names:',repr(orig_name),repr(orig_comp_name))
solid=TopoDS_Shape(); BRepTools.Read_s(solid,solid_path,BRep_Builder())
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
local=BRepBuilderAPI_Transform(solid,loc.Inverted().Transformation(),True).Shape()
print('local shape location identity:',local.Location().IsIdentity())
newref=st.AddShape(local,False,True)
a_=TDataStd_Name(); ref262.FindAttribute(TDataStd_Name.GetID_s(),a_); TDataStd_Name.Set_s(newref,a_.Get())
newcomp=st.AddComponent(asm,newref,loc)
b_=TDataStd_Name()
if comp262.FindAttribute(TDataStd_Name.GetID_s(),b_): TDataStd_Name.Set_s(newcomp,b_.Get())
asm266,comp266,ref266=found["266"]
st.RemoveComponent(comp262)
st.RemoveComponent(comp266)
for L in (ref262,ref266):
    try: st.RemoveShape(L,False)
    except Exception as e: print("remove label note:",e)
st.UpdateAssemblies()
roots2=TDF_LabelSequence(); st.GetFreeShapes(roots2); print("free shapes after:",roots2.Length())
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
