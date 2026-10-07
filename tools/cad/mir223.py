import sys, numpy as np, collections
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.BRepTools import BRepTools
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Surface
k=[k for k in parts if k.endswith("223")][0]; s=parts[k][0]
BRepTools.Write_s(s,"work/p223.brep")
tr=gp_Trsf(); tr.SetMirror(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(1,0,0)))
M=BRepBuilderAPI_Transform(s,tr,True).Shape()
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def key(f):
    b=Bnd_Box(); BRepBndLib.Add_s(f,b); p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    return np.array(b.Get()),p.Mass(),str(BRepAdaptor_Surface(f).GetType()).split('.')[-1][8:]
F=[(f,)+key(f) for f in faces(s)]; Fm=[(f,)+key(f) for f in faces(M)]
def match(a,B): return any(np.abs(a[1]-b[1]).max()<0.05 and abs(a[2]-b[2])<0.1 and a[3]==b[3] for b in B)
# faces of original with no mirrored partner (i.e. exist on one side only)
only=[a for a in F if not match(a,Fm)]
print("part 223: faces",len(F)," faces with no mirror partner:",len(only))
sides=collections.Counter("+x" if (a[1][0]+a[1][3])/2>0 else "-x" for a in only); print("those lie on:",dict(sides))
only_pos=[a for a in only if (a[1][0]+a[1][3])/2>0]; only_neg=[a for a in only if (a[1][0]+a[1][3])/2<=0]
print("unpaired +x faces: types",collections.Counter(a[3] for a in only_pos),"area %.0f"%sum(a[2] for a in only_pos))
print("unpaired -x faces: types",collections.Counter(a[3] for a in only_neg),"area %.0f"%sum(a[2] for a in only_neg))
for a in sorted(only_pos,key=lambda a:-a[2])[:10]: print("  +x big unpaired: %s area %.0f x[%.1f..%.1f] y[%.0f..%.0f] z[%.0f..%.0f]"%(a[3],a[2],a[1][0],a[1][3],a[1][1],a[1][4],a[1][2],a[1][5]))
for a in sorted(only_neg,key=lambda a:-a[2])[:6]: print("  -x big unpaired: %s area %.0f x[%.1f..%.1f] y[%.0f..%.0f] z[%.0f..%.0f]"%(a[3],a[2],a[1][0],a[1][3],a[1][1],a[1][4],a[1][2],a[1][5]))
