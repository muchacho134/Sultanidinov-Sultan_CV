from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TopLoc import TopLoc_Location
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
def load(fn):
    doc=TDocStd_Document(TCollection_ExtendedString("d")); r=STEPCAFControl_Reader(); r.SetNameMode(True); r.ReadFile(fn); r.Transfer(doc)
    return doc, XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
def nm(l):
    a=TDataStd_Name(); return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(),a) else "?"
def leafprops(st,l,loc=TopLoc_Location()):
    out=[]
    def walk(l,loc):
        ref=TDF_Label(); tgt=l
        if st.IsReference_s(l): st.GetReferredShape_s(l,ref); tgt=ref; loc=loc.Multiplied(st.GetLocation_s(l))
        if st.IsAssembly_s(tgt):
            cs=TDF_LabelSequence(); st.GetComponents_s(tgt,cs)
            for i in range(1,cs.Length()+1): walk(cs.Value(i),loc)
        else:
            s=st.GetShape_s(tgt).Moved(loc); p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); c=p.CentreOfMass(); out.append((round(p.Mass(),0),round(c.X(),2),round(c.Y(),2),round(c.Z(),2)))
    walk(l,loc); return sorted(out)
docO,stO=load("work/orig/fm300.step")
fs=TDF_LabelSequence(); stO.GetFreeShapes(fs); root=fs.Value(1)
ref=TDF_Label(); cs=TDF_LabelSequence(); stO.GetComponents_s(root,cs)
docM,stM=load("work/addin/motor.step"); fsM=TDF_LabelSequence(); stM.GetFreeShapes(fsM); mot=leafprops(stM,fsM.Value(1))
print("motor file leaves",len(mot),"total vol %.0f"%sum(x[0] for x in mot))
for i in range(1,cs.Length()+1):
    c=cs.Value(i); r_=TDF_Label(); stO.GetReferredShape_s(c,r_)
    if not stO.IsAssembly_s(r_): continue
    loc=stO.GetLocation_s(c); T=loc.Transformation(); tr=T.TranslationPart()
    m=[[T.Value(a,b) for b in (1,2,3)] for a in (1,2,3)]
    local=leafprops(stO,r_,TopLoc_Location())
    same=sorted(x[0] for x in local)==sorted(x[0] for x in mot)
    match=sum(1 for a,b in zip(local,mot) if a==b)
    print(nm(c),"translation (%.3f,%.3f,%.3f)"%(tr.X(),tr.Y(),tr.Z()),"rot",[[round(v,4) for v in row] for row in m])
    print("   local leaves",len(local),"same volumes as motor file:",same,"| identical local centres:",match,"/",len(mot))
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
def comp(st,l):
    C=TopoDS_Compound(); B=BRep_Builder(); B.MakeCompound(C)
    def walk(l,loc):
        ref=TDF_Label(); tgt=l
        if st.IsReference_s(l): st.GetReferredShape_s(l,ref); tgt=ref; loc=loc.Multiplied(st.GetLocation_s(l))
        if st.IsAssembly_s(tgt):
            cs=TDF_LabelSequence(); st.GetComponents_s(tgt,cs)
            for i in range(1,cs.Length()+1): walk(cs.Value(i),loc)
        else: B.Add(C,st.GetShape_s(tgt).Moved(loc))
    walk(l,TopLoc_Location()); return C
def bb(s):
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(s,b,False,False); return [round(v,2) for v in b.Get()]
def area(s):
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p); c=p.CentreOfMass(); return round(p.Mass(),0),(round(c.X(),2),round(c.Y(),2),round(c.Z(),2))
print("motor file  bbox",bb(comp(stM,fsM.Value(1))),"area/centroid",area(comp(stM,fsM.Value(1))))
c4=cs.Value(4); r4=TDF_Label(); stO.GetReferredShape_s(c4,r4)
print("orig NAUO4 local bbox",bb(comp(stO,r4)),"area/centroid",area(comp(stO,r4)))
