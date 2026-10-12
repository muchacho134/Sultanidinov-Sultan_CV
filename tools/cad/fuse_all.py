import glob, os, sys, time
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.TopTools import TopTools_ListOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL
from OCP.Message import Message_Gravity
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
fz=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
P=[(os.path.basename(f)[:-5],rd(f)) for f in sorted(glob.glob("work/gunp/*.brep"))]
print("parts",len(P),"input solids",sum(count(s,TopAbs_SOLID) for _,s in P),"sum vol %.1f"%sum(vol(s) for _,s in P),flush=True)
A=TopTools_ListOfShape(); T=TopTools_ListOfShape()
A.Append(P[0][1])
for _,s in P[1:]: T.Append(s)
t0=time.time()
op=BRepAlgoAPI_Fuse(); op.SetArguments(A); op.SetTools(T); op.SetRunParallel(True); op.SetFuzzyValue(fz); op.SetNonDestructive(True); op.Build()
print("fuse done in %.0fs, IsDone %s"%(time.time()-t0,op.IsDone()),flush=True)
r=op.Shape()
print("result: solids",count(r,TopAbs_SOLID),"shells",count(r,TopAbs_SHELL),"faces",count(r,TopAbs_FACE),"valid",BRepCheck_Analyzer(r).IsValid(),"vol %.1f"%vol(r),flush=True)
BRepTools.Write_s(r,f"work/gun_fused_{fz}.brep")
