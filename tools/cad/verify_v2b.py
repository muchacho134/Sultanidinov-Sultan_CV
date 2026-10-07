import sys, numpy as np
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepCheck import BRepCheck_Analyzer
doc=TDocStd_Document(TCollection_ExtendedString("d")); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
found={}
def walk(l,loc):
    c=TDF_LabelSequence(); st.GetComponents_s(l,c)
    for i in range(1,c.Length()+1):
        comp=c.Value(i); ref=TDF_Label(); st.GetReferredShape_s(comp,ref); L=loc.Multiplied(st.GetLocation_s(comp))
        if st.IsAssembly_s(ref): walk(ref,L)
        elif name(ref) in ("Muzzle","Barrel"): found[name(ref)]=st.GetShape_s(ref).Moved(L)
walk(roots.Value(1),TopLoc_Location())
def props(s): p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); c=p.CentreOfMass(); return p.Mass(),np.array([c.X(),c.Y(),c.Z()])
for nm,br in (("Muzzle","work/muzzle_solid.brep"),("Barrel","work/barrel_solid.brep")):
    s=TopoDS_Shape(); BRepTools.Read_s(s,br,BRep_Builder()); v0,c0=props(s); v1,c1=props(found[nm])
    print(f"{nm}: volume built {v0:.2f} / in file {v1:.2f} | centre of mass shift {np.linalg.norm(c1-c0):.6f} mm | valid in file {BRepCheck_Analyzer(found[nm]).IsValid()}")
