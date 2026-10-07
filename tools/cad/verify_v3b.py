import sys, numpy as np
exec(open("verify_hier2.py").read().split("tA,pA=load")[0])
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
tA,pA=load(sys.argv[1]); tB,pB=load(sys.argv[2])
for k in sorted(tB): print("  ",k.replace("조준경 + 짐벌 + 소총","ROOT "),":",len(tB[k]),"parts")
short=lambda n:n.replace("조준경 + 짐벌 + 소총","P")
print("parts:",len(pA),"->",len(pB),"| removed:",sorted(short(n) for n in set(pA)-set(pB)),"| added:",sorted(short(n) for n in set(pB)-set(pA)))
same=[k for k in set(pA)&set(pB) if short(k) not in ("P213","P111")]
print("other parts moved:",[short(k) for k in same if np.abs(pA[k]-pB[k]).max()>1e-3])
# exact check of the two new solids
exec(open("verify_v2b.py").read().split("def props")[0].replace("sys.argv[1]","sys.argv[2]").replace('elif name(ref) in ("Muzzle","Barrel")','elif short(name(ref)) in ("P213","P111")'))
def props(s): p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); c=p.CentreOfMass(); return p.Mass(),np.array([c.X(),c.Y(),c.Z()])
for key,br in (("P213","work/p213_solid.brep"),("P111","work/sight_collar_solid.brep")):
    s=TopoDS_Shape(); BRepTools.Read_s(s,br,BRep_Builder()); v0,c0=props(s); k=[n for n in found if short(n)==key][0]; v1,c1=props(found[k])
    print(f"{key}: solid {TopExp_Explorer(found[k],TopAbs_SOLID).More()} valid {BRepCheck_Analyzer(found[k]).IsValid()} | volume built {v0:.2f} / in file {v1:.2f} | centre shift {np.linalg.norm(c1-c0):.6f} mm")
