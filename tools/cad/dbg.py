import sys
exec(open("assemble.py").read().split("asm,comp262,ref262=found")[0].replace("src,solid_path,out=sys.argv[1:4]","src,solid_path,out=sys.argv[1],sys.argv[2],'x'"))
asm,comp262,ref262=found["262"]
def show(tag):
    r=TDF_Label(); st.GetReferredShape_s(comp262,r)
    print(tag,"| comp name",repr(name(comp262)),"-> refers to",repr(name(r)),"| ref262 label same as referred:",r.IsEqual(ref262),"| ref name",repr(name(ref262)))
show("initial")
loc=st.GetLocation_s(comp262)
solid=TopoDS_Shape(); BRepTools.Read_s(solid,solid_path,BRep_Builder())
st.SetShape(ref262,solid.Moved(loc.Inverted())); show("after SetShape")
st.UpdateAssemblies(); show("after UpdateAssemblies")
