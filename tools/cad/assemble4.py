import sys
src=open("assemble2.py").read()
exec(src.split("k114=[k for k")[0])
rb=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
k=[k for k in parts if k.endswith("262")][0]
asm,comp,ref=parts[k]; loc=st.GetLocation_s(comp)
local=BRepBuilderAPI_Transform(rb(sys.argv[3]),loc.Inverted().Transformation(),True).Shape()
nref=st.AddShape(local,False,True)
a_=TDataStd_Name(); ref.FindAttribute(TDataStd_Name.GetID_s(),a_); TDataStd_Name.Set_s(nref,a_.Get())
ncomp=st.AddComponent(asm,nref,loc); b_=TDataStd_Name()
if comp.FindAttribute(TDataStd_Name.GetID_s(),b_): TDataStd_Name.Set_s(ncomp,b_.Get())
st.RemoveComponent(comp); st.RemoveShape(ref,False); st.UpdateAssemblies()
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
