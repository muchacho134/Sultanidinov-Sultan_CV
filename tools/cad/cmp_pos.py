import sys
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def load(fn):
    sys.argv=[None,fn]; g={}
    exec(open("work/audit.py").read().split("for n,s in out:")[0],g)
    R={}
    for n,s in g["out"]:
        p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p); c=p.CentreOfMass(); R[n.replace("조준경 + 짐벌 + 소총","P")]=(p.Mass(),c.X(),c.Y(),c.Z())
    return R
ARGS=sys.argv[1:]
A=load(ARGS[0]); B=load(ARGS[1]); changed=set(ARGS[2].split(","))
moved=[k for k in A if k in B and k not in changed and max(abs(a-b) for a,b in zip(A[k],B[k]))>1e-3]
print("unchanged parts compared",len([k for k in A if k in B and k not in changed]),"moved/changed:",moved)
