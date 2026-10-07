import sys, pickle, numpy as np
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.TopTools import TopTools_IndexedMapOfShape
rows=[]
for k,(s,comp,ref) in parts.items():
    s=st.GetShape_s(comp); b=bb(s)
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
    rows.append(dict(name=k,short=k.replace("조준경 + 짐벌 + 소총","P"),solid=TopExp_Explorer(s,TopAbs_SOLID).More(),faces=fm.Extent(),area=p.Mass(),bbox=b))
pickle.dump(rows,open("work/overview.pkl","wb"))
rows.sort(key=lambda r:(r['bbox'][2]+r['bbox'][5])/2)
print("part        type   faces   area   centre(x,y,z)            size(x,y,z)")
for r in rows:
    b=r['bbox']; c=(b[:3]+b[3:])/2; d=b[3:]-b[:3]
    print("%-11s %-5s %5d %8.0f  (%6.0f %6.0f %6.0f)  (%5.0f %5.0f %5.0f)"%(r['short'][:11],"solid" if r['solid'] else "open",r['faces'],r['area'],*c,*d))
