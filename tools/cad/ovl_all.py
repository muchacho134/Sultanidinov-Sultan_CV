import glob,os,sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.TopAbs import TopAbs_SOLID
from OCP.Bnd import Bnd_Box
from OCP.BRepCheck import BRepCheck_Analyzer
P={os.path.basename(f)[:-5]:f for f in glob.glob("work/allp/*.brep")}
new={"P244":"work/p244_c3.brep","425":"work/rail_in/rail.brep","381":"work/closed_381.brep","388":"work/closed_388.brep","432":"work/closed_432.brep","410":"work/closed_410.brep","411":"work/closed_411.brep","417":"work/closed_417.brep","418":"work/closed_418.brep","421":"work/closed_421.brep"}
P.update(new); S={k:rd(v) for k,v in P.items()}
def bb(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); return b
B={k:bb(v) for k,v in S.items()}
for k in new:
    for m,o in S.items():
        if m==k or B[k].IsOut(B[m]): continue
        if m in new and m<k: continue
        v=vol(BRepAlgoAPI_Common(S[k],o).Shape())
        if abs(v)>0.5: print("OVERLAP",k,m,"%.1f"%v)
print("done")
