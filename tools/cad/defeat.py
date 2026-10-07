import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Defeaturing
from OCP.BRepCheck import BRepCheck_Analyzer
s=rd(sys.argv[1]); idx=[int(x) for x in sys.argv[3].split(",")]
F=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More(): F.append(ex.Current()); ex.Next()
d=BRepAlgoAPI_Defeaturing(); d.SetShape(s)
for i in idx: d.AddFaceToRemove(F[i])
d.SetRunParallel(False); d.Build()
print("done",d.IsDone(),"warn",d.HasWarnings() if hasattr(d,"HasWarnings") else "")
r=d.Shape(); print("valid",BRepCheck_Analyzer(r).IsValid(),"faces",count(r,TopAbs_FACE),"vol %.1f -> %.1f"%(vol(s),vol(r)))
BRepTools.Write_s(r,sys.argv[2])
