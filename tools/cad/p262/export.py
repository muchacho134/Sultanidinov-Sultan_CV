exec(open("finish.py").read().split("H=sol")[0])
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDataStd import TDataStd_Name
from OCP.TCollection import TCollection_ExtendedString
from OCP.Interface import Interface_Static
M=rd('P262_final.brep')
doc=TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
lab=st.AddShape(M,False)
TDataStd_Name.Set_s(lab,TCollection_ExtendedString(sys.argv[2]))
Interface_Static.SetCVal_s("write.step.schema","AP214IS")
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.Transfer(doc,STEPControl_AsIs); print('write',w.Write(sys.argv[1]))
