import sys, numpy as np, collections
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.BRepAdaptor import BRepAdaptor_Surface
res=[]
for k,(s,comp,ref) in parts.items():
    s=st.GetShape_s(comp); b=bb(s)
    if b[3]-b[0]<8: continue
    pos=neg=0; ap=an=0.0; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); bf=Bnd_Box(); BRepBndLib.Add_s(f,bf); x=bf.Get(); cx=(x[0]+x[3])/2
        p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
        if cx>0: pos+=1; ap+=p.Mass()
        else: neg+=1; an+=p.Mass()
        ex.Next()
    res.append((abs(pos-neg),k[-8:],pos,neg,round(ap),round(an),[round(v) for v in b]))
res.sort(reverse=True)
print("part  faces(+x,-x)  area(+x,-x)  bbox")
for r in res[:14]: print(r[1],(r[2],r[3]),(r[4],r[5]),r[6])
