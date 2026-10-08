exec(open("work/motorpos.py").read().split("docM,stM=load")[0])
exec(open("work/motorpos.py").read().split("from OCP.TopoDS import TopoDS_Compound")[1].split("print(\"motor file")[0].replace("def comp","from OCP.TopoDS import TopoDS_Compound\nfrom OCP.BRep import BRep_Builder\ndef comp"))
def comp_world(st,c):
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    C=TopoDS_Compound(); B=BRep_Builder(); B.MakeCompound(C)
    def walk(l,loc):
        ref=TDF_Label(); tgt=l
        if st.IsReference_s(l): st.GetReferredShape_s(l,ref); tgt=ref; loc=loc.Multiplied(st.GetLocation_s(l))
        if st.IsAssembly_s(tgt):
            q=TDF_LabelSequence(); st.GetComponents_s(tgt,q)
            for i in range(1,q.Length()+1): walk(q.Value(i),loc)
        else: B.Add(C,st.GetShape_s(tgt).Moved(loc))
    walk(c,TopLoc_Location()); return C
O={}
for i in range(1,cs.Length()+1):
    c=cs.Value(i); r_=TDF_Label(); stO.GetReferredShape_s(c,r_)
    if stO.IsAssembly_s(r_): O[nm(c)]=comp_world(stO,c)
docN,stN=load("work/Gun_full_assembly.step"); fsN=TDF_LabelSequence(); stN.GetFreeShapes(fsN); csN=TDF_LabelSequence(); stN.GetComponents_s(fsN.Value(1),csN)
N={}
for i in range(1,csN.Length()+1):
    c=csN.Value(i)
    if nm(c).startswith("Motor"): N[nm(c)]=comp_world(stN,c)
for (on,os_),(nn,ns) in zip(sorted(O.items()),sorted(N.items())):
    a=bb(os_); b=bb(ns); ca=area(os_)[1]; cb=area(ns)[1]
    print(on,"->",nn,"bbox max diff %.3f"%max(abs(x-y) for x,y in zip(a,b)),"centroid diff %.3f"%max(abs(x-y) for x,y in zip(ca,cb)),"centre",cb)
