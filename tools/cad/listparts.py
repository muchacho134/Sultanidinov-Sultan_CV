exec(open("probe3.py").read().split("P={}")[0])
G={}
def walk(l,loc,grp):
    c=TDF_LabelSequence(); st.GetComponents_s(l,c)
    for i in range(1,c.Length()+1):
        comp=c.Value(i); ref=TDF_Label(); st.GetReferredShape_s(comp,ref); L=loc.Multiplied(st.GetLocation_s(comp))
        if st.IsAssembly_s(ref): walk(ref,L,name(ref))
        else:
            n=name(ref).replace("조준경 + 짐벌 + 소총","P"); s=st.GetShape_s(ref).Moved(L); G[n]=(grp,s)
walk(roots.Value(1),TopLoc_Location(),"")
import pickle
for n,(g,s) in sorted(G.items(),key=lambda t:(t[1][0],t[0])):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    print(f"{g:32s} {n:10s} {str(s.ShapeType()).split('.')[-1][7:]:6s} f{fm.Extent():5d} x[{x[0]:7.1f},{x[3]:7.1f}] y[{x[1]:7.1f},{x[4]:7.1f}] z[{x[2]:7.1f},{x[5]:7.1f}]")
    BRepTools.Write_s(s,f"work/g_{n}.brep")
