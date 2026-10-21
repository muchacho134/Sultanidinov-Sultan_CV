"""Assemble the parts into a coloured STEP (AP214) via XCAF."""
import sys, pickle
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDataStd import TDataStd_Name
from OCP.Interface import Interface_Static
from overlay import load
from build_car import faces, wheel
import body as B

RGB = {None: (0.90, 0.91, 0.93), 'well': (0.12, 0.12, 0.13), 'dark': (0.08, 0.08, 0.09),
       'recess': (0.45, 0.46, 0.50), 'glass': (0.10, 0.13, 0.17), 'lamp': (0.62, 0.72, 0.85),
       'tyre': (0.05, 0.05, 0.05), 'disc': (0.62, 0.63, 0.66),
       'trim': (0.90, 0.91, 0.93), 'fin': (0.22, 0.23, 0.25), 'red': (0.85, 0.04, 0.04)}


def col(t):
    return Quantity_Color(*RGB[t], Quantity_TOC_RGB)


def main(out):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    st.SetAutoNaming_s(False)
    asm = st.NewShape()
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString("Concept_car"))

    def add(shape, name, color, face_tags=None):
        lab = st.AddShape(shape, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
        ct.SetColor(lab, col(color), XCAFDoc_ColorGen)
        if face_tags:
            for f, t in zip(faces(shape), face_tags):
                if t is not None:
                    sub = st.AddSubShape(lab, f)
                    if not sub.IsNull():
                        ct.SetColor(sub, col(t), XCAFDoc_ColorSurf)
        st.AddComponent(asm, lab, shape.Location())

    body = load("out/body.brep")
    add(body, "Body", None, pickle.load(open("out/body_tags.pkl", "rb")))
    for name, path, tag in pickle.load(open("out/parts.pkl", "rb")):
        add(load(path), name, tag)
    for xa, ax in ((B.AXLE_F, "Front"), (B.AXLE_R, "Rear")):
        for s, side in ((1, "Left"), (-1, "Right")):
            add(wheel(xa, s), f"{ax}_{side}_wheel", 'tyre')
    st.UpdateAssemblies()
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    print("write", w.Write(out))


if __name__ == "__main__":
    main(sys.argv[1])
