import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopAbs import *
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.TopoDS import TopoDS
import collections
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
seq=TDF_LabelSequence(); st.GetShapes(seq)
n=TCollection_ExtendedString
hit=None
for i in range(1,seq.Length()+1):
    lab=seq.Value(i); a=TDataStd_Name()
    if lab.FindAttribute(TDataStd_Name.GetID_s(),a):
        nm=a.Get().ToExtString()
        if nm.endswith("266"): hit=(lab,nm); print("found",repr(nm), "label",lab.Tag())
lab,nm=hit
shp=st.GetShape_s(lab)
print("type",shp.ShapeType())
b=Bnd_Box(); BRepBndLib.Add_s(shp,b); x=b.Get(); print("bbox",[round(v,2) for v in x],"size",[round(x[3]-x[0],2),round(x[4]-x[1],2),round(x[5]-x[2],2)])
p=GProp_GProps(); BRepGProp.SurfaceProperties_s(shp,p); print("area",round(p.Mass(),2))
sol=TopExp_Explorer(shp,TopAbs_SOLID).More(); print("is solid:",sol)
fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(shp,TopAbs_FACE,fm); print("faces",fm.Extent())
c=collections.Counter(); 
for i in range(1,fm.Extent()+1): c[str(BRepAdaptor_Surface(TopoDS.Face_s(fm.FindKey(i))).GetType()).split('.')[-1]]+=1
print(dict(c))
# compare to neighbours' names: other parts near it
