import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
src,out=sys.argv[1],sys.argv[2]
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.SetColorMode(True); rd.SetLayerMode(True); rd.SetPropsMode(True); rd.ReadFile(src); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
roots=TDF_LabelSequence(); st.GetFreeShapes(roots); root=roots.Value(1)
subs={}; members={}
c=TDF_LabelSequence(); st.GetComponents_s(root,c)
for i in range(1,c.Length()+1):
    comp=c.Value(i); ref=TDF_Label(); st.GetReferredShape_s(comp,ref); subs[name(ref)]=ref
    cc=TDF_LabelSequence(); st.GetComponents_s(ref,cc)
    for j in range(1,cc.Length()+1):
        pc=cc.Value(j); pr=TDF_Label(); st.GetReferredShape_s(pc,pr)
        members[name(pr).replace("조준경 + 짐벌 + 소총","P")]=(pc,pr)
rb=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
jobs=[("01_Muzzle","Muzzle","work/muzzle_solid.brep",["P221","solid_222","P215","solid_220"]),
      ("05_Barrel","Barrel","work/barrel_solid.brep",["P159","solid_199","solid_158","P156","solid_153"])]
for sub,pname,brep,old in jobs:
    for n in old:
        pc,pr=members[n]; st.RemoveComponent(pc); st.RemoveShape(pr,False)
    nref=st.AddShape(rb(brep),False,True); TDataStd_Name.Set_s(nref,TCollection_ExtendedString(pname))
    nc=st.AddComponent(subs[sub],nref,TopLoc_Location()); TDataStd_Name.Set_s(nc,TCollection_ExtendedString(pname))
    print(f"{sub}: removed {len(old)} pieces, added solid '{pname}'")
st.UpdateAssemblies()
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
