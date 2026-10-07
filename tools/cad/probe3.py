import sys, numpy as np, collections
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
doc=TDocStd_Document(TCollection_ExtendedString("d")); rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()); roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
def name(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
P={}
def walk(l,loc):
    c=TDF_LabelSequence(); st.GetComponents_s(l,c)
    for i in range(1,c.Length()+1):
        comp=c.Value(i); ref=TDF_Label(); st.GetReferredShape_s(comp,ref); L=loc.Multiplied(st.GetLocation_s(comp))
        if st.IsAssembly_s(ref): walk(ref,L)
        else: P[name(ref).replace("조준경 + 짐벌 + 소총","P")]=st.GetShape_s(ref).Moved(L)
walk(roots.Value(1),TopLoc_Location())
for n in sys.argv[2:]:
    s=P[n]; BRepTools.Write_s(s,f"work/x_{n}.brep"); b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,w); o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o)
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    ty=collections.Counter(str(BRepAdaptor_Surface(TopoDS.Face_s(fm.FindKey(i))).GetType()).split('.')[-1][8:] for i in range(1,fm.Extent()+1))
    print(f"== {n}: {str(s.ShapeType()).split('.')[-1][7:]} valid {BRepCheck_Analyzer(s).IsValid()} faces {fm.Extent()} {dict(ty)} | free loops {w.Extent()}+{o.Extent()} | bbox x[{x[0]:.2f},{x[3]:.2f}] y[{x[1]:.2f},{x[4]:.2f}] z[{x[2]:.2f},{x[5]:.2f}]")
    for i in range(1,w.Extent()+1):
        wb=Bnd_Box(); BRepBndLib.Add_s(w.FindKey(i),wb); y=wb.Get(); ne=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(w.FindKey(i),TopAbs_EDGE,ne)
        print("     free loop: %d edges x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(ne.Extent(),y[0],y[3],y[1],y[4],y[2],y[5]))
