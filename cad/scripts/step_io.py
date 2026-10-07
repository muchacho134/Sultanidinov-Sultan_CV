"""Read a STEP assembly into an XCAF document; returns {part-suffix: global shape}."""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
import numpy as np
def nm(l):
    n=TDataStd_Name()
    return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),n) else ''
def load(path):
    doc=TDocStd_Document(TCollection_ExtendedString("doc"))
    r=STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True)
    r.ReadFile(path); r.Transfer(doc)
    st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
    root=roots.Value(1)
    comps=TDF_LabelSequence(); st.GetComponents_s(root,comps)
    parts={}
    for i in range(1,comps.Length()+1):
        c=comps.Value(i); s=st.GetShape_s(c)
        k=nm(c)[-3:]; parts[k if k.isdigit() else ('MERGED' if 'MERGED' in nm(c) else 'base')]=s
    return parts,doc,st,root
