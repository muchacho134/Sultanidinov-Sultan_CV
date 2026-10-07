import sys
src=open("assemble2.py").read()
exec(src.split("k114=[k for k")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
rb=lambda p:(lambda s:(BRepTools.Read_s(s,p,BRep_Builder()),s)[1])(TopoDS_Shape())
def K(n): 
    m=[k for k in parts if k.endswith("소총"+n)]; assert len(m)==1,(n,m); return m[0]
def area(s): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p); return p.Mass()
def put(key,placed):
    asm,comp,ref=parts[key]; loc=st.GetLocation_s(comp)
    local=BRepBuilderAPI_Transform(placed,loc.Inverted().Transformation(),True).Shape()
    nref=st.AddShape(local,False,True); a_=TDataStd_Name(); ref.FindAttribute(TDataStd_Name.GetID_s(),a_); TDataStd_Name.Set_s(nref,a_.Get())
    ncomp=st.AddComponent(asm,nref,loc); b_=TDataStd_Name()
    if comp.FindAttribute(TDataStd_Name.GetID_s(),b_): TDataStd_Name.Set_s(ncomp,b_.Get())
    st.RemoveComponent(comp); st.RemoveShape(ref,False)
def drop(key):
    asm,comp,ref=parts[key]; st.RemoveComponent(comp); st.RemoveShape(ref,False)
# 1) rail: new closed solid absorbs 267, 268
put(K("262"),rb("work/closed_r2.brep")); drop(K("267")); drop(K("268"))
# 2) merge confirmed groups into their largest member
for grp in (["592","596","597","598","261"],["110","216","217"],["251","258"]):
    keys=[K(n) for n in grp]; shapes={k:st.GetShape_s(parts[k][1]) for k in keys}
    main=max(keys,key=lambda k:area(shapes[k]))
    sw=BRepBuilderAPI_Sewing(0.05)
    for k in keys: sw.Add(shapes[k])
    sw.Perform(); put(main,sw.SewedShape())
    for k in keys:
        if k!=main: drop(k)
    print("merged",grp,"->",main[-6:])
st.UpdateAssemblies()
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
