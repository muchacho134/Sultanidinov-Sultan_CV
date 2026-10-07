import sys, numpy as np
exec(open("verify_hier.py").read().split("tA,pA=load")[0])
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
tA,pA=load(sys.argv[1]); tB,pB=load(sys.argv[2])
print("tree:")
for k in sorted(tB): print("  ",k.replace("조준경 + 짐벌 + 소총","ROOT "),":",len(tB[k]),"parts", "->"+",".join(tB[k]) if len(tB[k])==1 else "")
common=set(pA)&set(pB); print("parts before/after:",len(pA),len(pB),"| removed:",sorted(n.replace("조준경 + 짐벌 + 소총","P") for n in set(pA)-set(pB)),"| added:",sorted(set(pB)-set(pA)))
print("unchanged parts moved:",[k for k in common if np.abs(pA[k]-pB[k]).max()>1e-3])
for nm,br in (("Muzzle","work/muzzle_solid.brep"),("Barrel","work/barrel_solid.brep")):
    s=TopoDS_Shape(); BRepTools.Read_s(s,br,BRep_Builder()); b=Bnd_Box(); BRepBndLib.Add_s(s,b)
    print(nm,"in file at same place as built solid:",np.abs(pB[nm]-np.array(b.Get())).max()<1e-3)
for nm,br in (("Muzzle","work/muzzle_solid.brep"),("Barrel","work/barrel_solid.brep")):
    s=TopoDS_Shape(); BRepTools.Read_s(s,br,BRep_Builder()); b=Bnd_Box(); BRepBndLib.Add_s(s,b)
    print(nm,"built:",np.round(b.Get(),2)); print(nm,"in file:",np.round(pB[nm],2))
k=[x for x in pA if x.endswith("221")][0]; print("P221 in old grouped file:",np.round(pA[k],2))
