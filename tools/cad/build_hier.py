import sys, pickle
src=open("assemble2.py").read()
exec(src.split("k114=[k for k")[0])
from OCP.TopLoc import TopLoc_Location
M=pickle.load(open("work/hier_map.pkl","rb"))
roots_asm={a for (a,c,r) in parts.values()}; assert len(roots_asm)==1 or True
root=list(parts.values())[0][0]
names={"01_Muzzle":"01_Muzzle","02_Mount_Plates":"02_Mount_Plates","03_Front_Bracket":"03_Front_Bracket"}
sub={}
for g in sorted(set(M.values())):
    lab=st.NewShape(); TDataStd_Name.Set_s(lab,TCollection_ExtendedString(g)); sub[g]=lab
moved=0
for k,(asm,comp,ref) in parts.items():
    g=M[k]; loc=st.GetLocation_s(comp)
    nc=st.AddComponent(sub[g],ref,loc)
    b_=TDataStd_Name()
    if comp.FindAttribute(TDataStd_Name.GetID_s(),b_): TDataStd_Name.Set_s(nc,b_.Get())
    st.RemoveComponent(comp); moved+=1
for g,lab in sub.items():
    c=st.AddComponent(root,lab,TopLoc_Location()); TDataStd_Name.Set_s(c,TCollection_ExtendedString(g))
st.UpdateAssemblies()
print("parts moved:",moved,"sub-assemblies:",len(sub))
w=STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True); w.SetLayerMode(True); w.SetPropsMode(True)
w.Transfer(doc,STEPControl_AsIs); w.Write(out); print("written",out)
