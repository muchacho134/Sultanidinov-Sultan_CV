import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
s=rd(sys.argv[1]); boxes=[[float(v) for v in b.split(",")] for b in sys.argv[3].split(";")]
keep=[]; rm=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=ex.Current(); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); x=b.Get()
    hit=any(all(abs(x[i]-B[i])<0.03 for i in range(6)) for B in boxes)
    (rm if hit else keep).append(f); ex.Next()
sw=BRepBuilderAPI_Sewing(1e-3)
for f in keep: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2]); print("removed",len(rm))
