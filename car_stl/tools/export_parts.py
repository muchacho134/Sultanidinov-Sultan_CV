import sys, json
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDataStd import TDataStd_Name
from OCP.Interface import Interface_Static
doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
st.SetAutoNaming_s(False)
asm = st.NewShape(); TDataStd_Name.Set_s(asm, TCollection_ExtendedString("Car_parts_stage1"))
COL = {"Wheel": (0.08, 0.08, 0.09), "WheelRegion": (0.9, 0.3, 0.25), "Floor": (0.3, 0.55, 0.9)}
for k in json.load(open("part_names.json")):
    s = load(f"part_{k}.brep")
    lab = st.AddShape(s, False); TDataStd_Name.Set_s(lab, TCollection_ExtendedString(k))
    ct.SetColor(lab, Quantity_Color(*COL[k.split("_")[0]], Quantity_TOC_RGB), XCAFDoc_ColorGen)
    st.AddComponent(asm, lab, s.Location())
st.UpdateAssemblies()
Interface_Static.SetCVal_s("write.step.schema", "AP214IS"); Interface_Static.SetCVal_s("write.step.unit", "MM")
w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True); w.Transfer(doc, STEPControl_AsIs)
print(w.Write(sys.argv[1]))
