import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name
from OCP.TopAbs import *
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
doc=TDocStd_Document(TCollection_ExtendedString("d"))
rd=STEPCAFControl_Reader(); rd.SetNameMode(True); rd.ReadFile(sys.argv[1]); rd.Transfer(doc)
st=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
roots=TDF_LabelSequence(); st.GetFreeShapes(roots)
parts={}
def name(l):
    a=TDataStd_Name()
    return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else ""
def walk(l):
    comps=TDF_LabelSequence(); 
    if st.IsAssembly_s(l):
        st.GetComponents_s(l,comps)
        for i in range(1,comps.Length()+1): walk(comps.Value(i))
    else:
        from OCP.TDF import TDF_Label
        ref=TDF_Label()
        n=name(l)
        if st.IsReference_s(l) and st.GetReferredShape_s(l,ref): n=name(ref)
        sh=st.GetShape_s(l)
        key=n.replace("조준경 + 짐벌 + 소총","")
        parts[key]=sh
for i in range(1,roots.Length()+1): walk(roots.Value(i))
print("parts placed:",len(parts))
def bbox(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); return [round(v,1) for v in b.Get()]
t=parts["266"]; print("266 placed bbox",bbox(t))
# find rail: shell with 528 faces
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopExp import TopExp
rail=None
for k,s in parts.items():
    m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,m)
    if m.Extent()==528: rail=(k,s)
print("rail part number:",rail[0],"placed bbox",bbox(rail[1]))
d=BRepExtrema_DistShapeShape(t,rail[1]); d.Perform(); print("min distance 266 -> rail: %.3f mm"%d.Value())
res=[]
for k,s in parts.items():
    if k=="266": continue
    dd=BRepExtrema_DistShapeShape(t,s); 
    if dd.Perform(): res.append((dd.Value(),k,bbox(s)))
res.sort(); 
for r in res[:6]: print(round(r[0],2),r[1],r[2])

print("---- sewing test: rail + 266")
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.TopExp import TopExp_Explorer
def loops(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-3); m=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m)
    o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o); return m.Extent()+o.Extent()
rs=rail[1]; print("rail free loops alone:",loops(rs))
for tol in (0.05,0.5,1.0):
    sw=BRepBuilderAPI_Sewing(tol); sw.Add(rs); sw.Add(t); sw.Perform(); out=sw.SewedShape()
    e=TopExp_Explorer(out,TopAbs_SHELL); shs=[]
    while e.More(): shs.append(e.Current()); e.Next()
    print(f"tol {tol}: shells {len(shs)}, free loops {[loops(x) for x in shs]}")
# where is 266's boundary relative to rail's free-loop edges
fb=ShapeAnalysis_FreeBounds(rs,1e-3)
from OCP.TopoDS import TopoDS
best=[]
ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More():
    w=ex.Current(); dd=BRepExtrema_DistShapeShape(t,w); dd.Perform(); best.append((round(dd.Value(),2),bbox(w))); ex.Next()
best.sort(key=lambda r:r[0]); print("closest rail free loops to 266:"); [print(" ",b) for b in best[:4]]
