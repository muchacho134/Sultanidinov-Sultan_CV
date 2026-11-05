"""Export the finished CAD faces (half car) + CAD wheels to STEP, coloured and named."""
import sys, json
sys.path.insert(0, "/home/user/Sultanidinov-Sultan_CV/car")
from overlay import load
from build_car import faces as occ_faces
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
asm = st.NewShape(); TDataStd_Name.Set_s(asm, TCollection_ExtendedString("Half_car"))
COL = {"floor": (0.55, 0.35, 0.90), "cylinder": (0.95, 0.55, 0.20), "slot": (0.30, 0.80, 0.45), "Wheel": (0.08, 0.08, 0.09), "patch": (0.86, 0.87, 0.90)}
def add(s, name, key):
    lab = st.AddShape(s, False); TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*COL[key], Quantity_TOC_RGB), XCAFDoc_ColorGen); st.AddComponent(asm, lab, s.Location())
cad = load(sys.argv[1]); names = json.load(open(sys.argv[1].replace(".brep", "_names.json")))
for f, n in zip(occ_faces(cad), names):
    add(f, n.replace(" ", "_"), "floor" if "floor" in n else ("cylinder" if "cylinder" in n else "slot"))
if len(sys.argv) > 3:                         # fitted body patches
    for i, f in enumerate(occ_faces(load(sys.argv[3]))):
        add(f, f"Body_patch_{i:02d}", "patch")
for k in ("Wheel_FR", "Wheel_RR"):           # right-hand (-Y) half wheels
    add(load(f"part_{k}.brep"), k, "Wheel")
st.UpdateAssemblies()
Interface_Static.SetCVal_s("write.step.schema", "AP214IS"); Interface_Static.SetCVal_s("write.step.unit", "MM")
w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True); w.Transfer(doc, STEPControl_AsIs)
print(w.Write(sys.argv[2]))
