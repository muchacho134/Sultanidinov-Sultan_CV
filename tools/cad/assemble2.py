import sys, numpy as np
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
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
src,out=sys.argv[1],sys.argv[2]
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.SetColorMode(True); rd.SetLayerMode(True); rd.SetPropsMode(True)
rd.ReadFile(src); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
parts={}
def walk(l):
    c=TDF_LabelSequence(); st.GetComponents_s(l,c)
    for i in range(1,c.Length()+1):
        comp=c.Value(i); ref=TDF_Label()
        if st.GetReferredShape_s(comp,ref):
            if st.IsAssembly_s(ref): walk(ref)
            else: parts[name(ref)]=(l,comp,ref)
for i in range(1,roots.Length()+1): walk(roots.Value(i))
def bb(s): b=Bnd_Box(); BRepBndLib.Add_s(s,b); return np.array(b.Get())
k114=[k for k in parts if k.endswith("114")][0]; k131="solid_131"
b114=bb(st.GetShape_s(parts[k114][1]))
# tiny leftover facet parts around 114 (<=2 faces, area<0.2) -> delete
tiny=[]
for k,(asm,comp,ref) in parts.items():
    if k in (k114,k131): continue
    s=st.GetShape_s(comp)
    if s.ShapeType() not in (TopAbs_SHELL,TopAbs_FACE): continue
    b=bb(s)
    if not ((b[:3]>=b114[:3]-3).all() and (b[3:]<=b114[3:]+3).all()): continue
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
    if fm.Extent()<=2 and p.Mass()<0.2: tiny.append(k)
print("tiny parts to delete:",len(tiny))
rb=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
def replace(key,placed):
    asm,comp,ref=parts[key]; loc=st.GetLocation_s(comp)
    local=BRepBuilderAPI_Transform(placed,loc.Inverted().Transformation(),True).Shape()
    nref=st.AddShape(local,False,True)
    a_=TDataStd_Name()
    if ref.FindAttribute(TDataStd_Name.GetID_s(),a_): TDataStd_Name.Set_s(nref,a_.Get())
    ncomp=st.AddComponent(asm,nref,loc)
    b_=TDataStd_Name()
    if comp.FindAttribute(TDataStd_Name.GetID_s(),b_): TDataStd_Name.Set_s(ncomp,b_.Get())
    st.RemoveComponent(comp); st.RemoveShape(ref,False)
replace(k131,rb("work/s131_new.brep")); replace(k114,rb("work/s114_fixed.brep"))
for k in tiny:
    asm,comp,ref=parts[k]; st.RemoveComponent(comp); st.RemoveShape(ref,False)
st.UpdateAssemblies()
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
open("work/tiny_deleted.txt","w").write("\n".join(tiny))
