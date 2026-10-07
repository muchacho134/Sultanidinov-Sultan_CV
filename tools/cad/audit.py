import sys
exec(open("work/ext_parts.py").read().split("q=Bnd_Box()")[0])
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
# map leaves to group names
grp={}
def walk2(l,g):
    ref=TDF_Label(); tgt=l
    if st.IsReference_s(l): st.GetReferredShape_s(l,ref); tgt=ref
    n=nm(l) if nm(l)!="?" else nm(tgt)
    if st.IsAssembly_s(tgt):
        cs=TDF_LabelSequence(); st.GetComponents_s(tgt,cs)
        for i in range(1,cs.Length()+1): walk2(cs.Value(i), n if n.startswith(("0","1")) and "_" in n else g)
    else: grp.setdefault(n,g)
for i in range(1,fs.Length()+1): walk2(fs.Value(i),"")
for n,s in out:
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p); A=p.Mass()
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    ns=count(s,TopAbs_SOLID); nf=count(s,TopAbs_FACE)
    fb=ShapeAnalysis_FreeBounds(s,1e-3); fe=count(fb.GetClosedWires(),TopAbs_EDGE)+count(fb.GetOpenWires(),TopAbs_EDGE)
    k=n.replace("조준경 + 짐벌 + 소총","P")
    print("%-26s %-34s solids %d faces %4d freeEdges %4d area %9.1f vol %10.1f size %.1fx%.1fx%.1f"%(k,grp.get(n,"?"),ns,nf,fe,A,vol(s) if ns else 0,x[3]-x[0],x[4]-x[1],x[5]-x[2]))
