import sys
exec(open("bcg_build.py").read().split("# A) P214")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
S=rd(sys.argv[1])
for n in sys.argv[2].split(","):
    o=rd(n); c=common(S,o); v=vol(c)
    if v>0.01:
        b=Bnd_Box(); BRepBndLib.Add_s(c,b); x=b.Get(); print(f"{n:28s} overlap {v:9.1f}  x[{x[0]:.1f},{x[3]:.1f}] y[{x[1]:.1f},{x[4]:.1f}] z[{x[2]:.1f},{x[5]:.1f}]")
    else: print(f"{n:28s} overlap {v:9.2f}")
