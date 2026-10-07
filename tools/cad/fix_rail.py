import sys
from OCP.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS, TopoDS_Compound
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Trsf, gp_Vec
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_Sewing
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRep import BRep_Builder
src,out_part,out_full=sys.argv[1:4]
r=STEPControl_Reader(); r.ReadFile(src); r.TransferRoots(); root=r.OneShape()
# top-level children in order
kids=[]; it=TopExp_Explorer(root,TopAbs_COMPOUND)  # not used
from OCP.TopoDS import TopoDS_Iterator
ti=TopoDS_Iterator(root)
while ti.More(): kids.append(ti.Value()); ti.Next()
print("top-level children:",len(kids))
def find_shell(k):
    e=TopExp_Explorer(k,TopAbs_SHELL,TopAbs_SOLID)
    return e.Current() if e.More() else None
# locate rail child: the open shell with bbox matching 123
idx=None
for n,k in enumerate(kids):
    s=find_shell(k)
    if s is None: continue
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    if abs(x[2]+215)<0.1 and abs(x[5]-225)<0.1 and abs(x[0]+29)<0.1: idx=n; break
print("rail is child",idx)
rail=kids[idx]; shell=find_shell(rail)
def bb(f):
    b=Bnd_Box(); BRepBndLib.Add_s(f,b); return b.Get()
def area(f):
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
faces=[]; ex=TopExp_Explorer(shell,TopAbs_FACE)
while ex.More(): faces.append(TopoDS.Face_s(ex.Current())); ex.Next()
Z0,Z1,SHIFT=-75.2,-15.0,60.0
ref=[f for f in faces if bb(f)[2]>=Z0 and bb(f)[5]<=Z1+0.01 and bb(f)[4]>=-226]
print("reference faces:",len(ref))
tr=gp_Trsf(); tr.SetTranslation(gp_Vec(0,0,SHIFT))
def same(a,b):
    x,y=bb(a),bb(b)
    return all(abs(p-q)<0.02 for p,q in zip(x,y)) and abs(area(a)-area(b))<0.05
new=[]; skipped=0
for f in ref:
    g=TopoDS.Face_s(BRepBuilderAPI_Transform(f,tr,True).Shape())
    if any(same(g,e) for e in faces): skipped+=1; continue
    new.append(g)
print("new faces added:",len(new),"(skipped duplicates of existing faces:",skipped,")")
def loops(s):
    fb=ShapeAnalysis_FreeBounds(s,1e-3); m=TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,m); o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o)
    return m.Extent()+o.Extent()
print("free loops before:",loops(shell))
sew=BRepBuilderAPI_Sewing(1e-3)
for f in faces+new: sew.Add(f)
sew.Perform(); res=sew.SewedShape()
shs=[]; e=TopExp_Explorer(res,TopAbs_SHELL)
while e.More(): shs.append(e.Current()); e.Next()
print("sewed shells:",len(shs),"free loops after:",[loops(s) for s in shs],"valid:",[BRepCheck_Analyzer(s).IsValid() for s in shs])
print("faces after:",[len(list(iter(()))) or 0 for _ in []] , "free edges info ok")
print("sewing: degenerated",sew.NbDegeneratedShapes(),"free edges",sew.NbFreeEdges(),"multiple edges",sew.NbMultipleEdges())
fixed=res
w=STEPControl_Writer(); w.Transfer(fixed,STEPControl_AsIs); w.Write(out_part)
# full model with replacement
comp=TopoDS_Compound(); B=BRep_Builder(); B.MakeCompound(comp)
for n,k in enumerate(kids): B.Add(comp,fixed if n==idx else k)
w2=STEPControl_Writer(); w2.Transfer(comp,STEPControl_AsIs); w2.Write(out_full)
print("written")
