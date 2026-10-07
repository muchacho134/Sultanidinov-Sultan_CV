import sys
exec(open("placed.py").read().split("print(\"parts placed")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
# parts dict keyed by name suffix; rebuild with full names
parts2={}
def walk2(l):
    comps=TDF_LabelSequence()
    if st.IsAssembly_s(l):
        st.GetComponents_s(l,comps)
        for i in range(1,comps.Length()+1): walk2(comps.Value(i))
    else:
        from OCP.TDF import TDF_Label
        ref=TDF_Label(); n=name(l)
        if st.IsReference_s(l) and st.GetReferredShape_s(l,ref): n=name(ref)
        parts2[n]=st.GetShape_s(l)
for i in range(1,roots.Length()+1): walk2(roots.Value(i))
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.TopoDS import TopoDS
from OCP.TopExp import TopExp
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
import collections
def info(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=[round(v,2) for v in b.Get()]
    fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    c=collections.Counter(str(BRepAdaptor_Surface(TopoDS.Face_s(fm.FindKey(i))).GetType()).split('.')[-1][8:] for i in range(1,fm.Extent()+1))
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,p)
    return str(s.ShapeType()).split('.')[-1],x,fm.Extent(),dict(c),round(p.Mass(),2)
for k in sorted(parts2):
    if k.endswith(("114","131")) : print(k, info(parts2[k]))
import pickle

print("=========== detail")
import numpy as np
from OCP.TopExp import TopExp_Explorer
from OCP.GeomAbs import *
def face_rows(s):
    rows=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t=a.GetType()
        b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=[round(v,2) for v in b.Get()]
        p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
        ne=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(f,TopAbs_EDGE,ne)
        d=None
        if t==GeomAbs_Plane: n=a.Plane().Axis().Direction(); d=(round(n.X(),2),round(n.Y(),2),round(n.Z(),2))
        elif t==GeomAbs_Cylinder: c=a.Cylinder(); d=("R=%.3f"%c.Radius(),tuple(round(v,3) for v in (c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z())),tuple(round(v,2) for v in (c.Location().X(),c.Location().Y(),c.Location().Z())))
        elif t==GeomAbs_Cone: c=a.Cone(); d=("semi %.1f deg"%(c.SemiAngle()*57.3),"refR=%.3f"%c.RefRadius(),tuple(round(v,3) for v in (c.Axis().Direction().X(),c.Axis().Direction().Y(),c.Axis().Direction().Z())),tuple(round(v,2) for v in (c.Location().X(),c.Location().Y(),c.Location().Z())))
        rows.append((str(t).split('.')[-1][8:],ne.Extent(),round(p.Mass(),3),x,d)); ex.Next()
    return rows
print("--- solid_131 faces"); [print(r) for r in face_rows(parts2["solid_131"])]
r114=face_rows(parts2["조준경 + 짐벌 + 소총114"])
print("--- 114 non-plane faces"); [print(r) for r in r114 if r[0]!="Plane"]
pl=[r for r in r114 if r[0]=="Plane"]
import collections
print("--- 114 planar faces by edge-count:",collections.Counter(r[1] for r in pl))
tiny=[r for r in pl if r[2]<0.2]; print("tiny planar faces (<0.2 mm2):",len(tiny)); [print(r) for r in tiny[:12]]
print("planar area distribution (sorted):",sorted(round(r[2],2) for r in pl)[:60])

print("=========== axial analysis")
from OCP.TopExp import TopExp
O=np.array([4.74,-241.16,-237.85]); A=np.array([0.866,0.5,0.0]); A/=np.linalg.norm(A)
def verts(s):
    vm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_VERTEX,vm)
    from OCP.BRep import BRep_Tool
    return np.array([[BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).X(),BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).Y(),BRep_Tool.Pnt_s(TopoDS.Vertex_s(vm.FindKey(i))).Z()] for i in range(1,vm.Extent()+1)])
def tr(P): d=P-O; t=d@A; r=np.linalg.norm(d-np.outer(t,A),axis=1); return t,r
for nm in ("solid_131","조준경 + 짐벌 + 소총114"):
    t,r=tr(verts(parts2[nm])); print(nm,"axial t: %.2f .. %.2f"%(t.min(),t.max()),"| radial r: %.2f .. %.2f"%(r.min(),r.max()))
# per-face axial ranges for 114
ex=TopExp_Explorer(parts2["조준경 + 짐벌 + 소총114"],TopAbs_FACE); rows=[]
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); t,r=tr(verts(f))
    rows.append((str(a.GetType()).split('.')[-1][8:],len(t),round(t.min(),2),round(t.max(),2),round(r.min(),2),round(r.max(),2))); ex.Next()
import collections
big=[x for x in rows if x[0]!="Plane"]; print("114 non-planar faces (type,nverts,t0,t1,r0,r1):"); [print(" ",x) for x in big]
pl=[x for x in rows if x[0]=="Plane"]
print("114 planar facets: t range %.2f..%.2f, r range %.2f..%.2f"%(min(x[2] for x in pl),max(x[3] for x in pl),min(x[4] for x in pl),max(x[5] for x in pl)))
print("big planar faces (>=11 verts):",[x for x in pl if x[1]>=9])
