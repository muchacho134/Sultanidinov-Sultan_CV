import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.Interface import Interface_Static
doc=TDocStd_Document(TCollection_ExtendedString("d"))
r=STEPCAFControl_Reader(); r.SetNameMode(True); r.SetColorMode(True); r.SetLayerMode(True); r.SetPropsMode(True); r.ReadFile(sys.argv[1]); r.Transfer(doc)
Interface_Static.SetIVal_s("write.surfacecurve.mode",0)
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(sys.argv[2]); print("written")
