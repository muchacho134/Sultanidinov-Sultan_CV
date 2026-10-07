"""Small helper to edit the flat Gun assembly (one root, one component per part)
while keeping part names, colours and placements."""
import re
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_Color
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.Interface import Interface_Static
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder

PREFIX = '\\X2\\c870c900acbd\\X0\\ + \\X2\\c9d0bc8c\\X0\\ + \\X2\\c18ccd1d\\X0\\'


def _name(l):
    n = TDataStd_Name()
    return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else ''


def _key(name):
    s = name[len(PREFIX):] if name.startswith(PREFIX) else name
    return s if s else 'base'


def compound(shapes):
    c = TopoDS_Compound(); b = BRep_Builder(); b.MakeCompound(c)
    for s in shapes: b.Add(c, s)
    return c


class Asm:
    def __init__(self, path):
        self.doc = TDocStd_Document(TCollection_ExtendedString('doc'))
        r = STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True)
        r.ReadFile(path); r.Transfer(self.doc)
        self.st = XCAFDoc_DocumentTool.ShapeTool_s(self.doc.Main())
        self.ct = XCAFDoc_DocumentTool.ColorTool_s(self.doc.Main())
        roots = TDF_LabelSequence(); self.st.GetFreeShapes(roots)
        self.root = roots.Value(1); self.root_name = _name(self.root)
        comps = TDF_LabelSequence(); self.st.GetComponents_s(self.root, comps)
        self.comp = {}
        for i in range(1, comps.Length() + 1):
            c = comps.Value(i); self.comp[_key(_name(c))] = c

    def shape(self, key):
        """part shape in global coordinates"""
        return self.st.GetShape_s(self.comp[key])

    def keys(self):
        return list(self.comp)

    def colour(self, key):
        ref = TDF_Label(); self.st.GetReferredShape_s(self.comp[key], ref)
        col = Quantity_Color()
        ok = XCAFDoc_ColorTool.GetColor_s(ref, XCAFDoc_ColorSurf, col) or XCAFDoc_ColorTool.GetColor_s(ref, XCAFDoc_ColorGen, col)
        return col if ok else None

    def remove(self, keys):
        for k in keys:
            c = self.comp.pop(k)
            ref = TDF_Label(); self.st.GetReferredShape_s(c, ref)
            self.st.RemoveComponent(c)
            assert self.st.RemoveShape(ref, True), ('could not remove', k)

    def add(self, key, shape, colour=None, loc=None):
        """add a part (shape given in global coordinates); optional placement kept as component location"""
        loc = loc or TopLoc_Location()
        local = BRepBuilderAPI_Transform(shape, loc.Inverted().Transformation(), True).Shape() if not loc.IsIdentity() else shape
        lab = self.st.AddShape(local, False)
        TDataStd_Name.Set_s(lab, TCollection_ExtendedString(PREFIX + key))
        if colour is not None: self.ct.SetColor(lab, colour, XCAFDoc_ColorSurf)
        c = self.st.AddComponent(self.root, lab, loc)
        TDataStd_Name.Set_s(c, TCollection_ExtendedString(PREFIX + key))
        self.comp[key] = c

    def replace(self, key, shape):
        """swap a part's geometry, keeping its name, colour and placement"""
        col = self.colour(key); loc = self.st.GetLocation_s(self.comp[key])
        self.remove([key]); self.add(key, shape, col, loc)

    def write(self, out, description):
        self.st.UpdateAssemblies()
        TDataStd_Name.Set_s(self.root, TCollection_ExtendedString(self.root_name))
        Interface_Static.SetCVal_s('write.step.schema', 'AP214IS')
        Interface_Static.SetCVal_s('write.step.unit', 'MM')
        Interface_Static.SetIVal_s('write.surfacecurve.mode', 0)
        w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
        w.Transfer(self.doc, STEPControl_AsIs)
        assert w.Write(out) == 1
        txt = open(out, encoding='latin-1').read()
        txt = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'2;1'\);", "FILE_DESCRIPTION(('%s'),'2;1');" % description, txt, count=1, flags=re.S)
        open(out, 'w', encoding='latin-1').write(txt)
